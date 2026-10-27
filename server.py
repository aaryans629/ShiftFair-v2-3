import json
import os
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("SHIFTFAIR_DB_PATH", ROOT / "shiftfair.sqlite3")).expanduser()
PORT = int(os.environ.get("PORT", "5000"))
MAX_BODY_BYTES = 1_000_000
DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
WORKERS = {"w1", "w2", "w3", "w4", "w5", "w6", "w7", "w8"}
PROFILES = {
    "CONSTRUCTION": {"day", "night", "rest"},
    "COLLEGE": {"morning", "evening", "night", "rest"},
}
SWAP_STATUSES = {"pending", "approved", "declined", "blocked", "expired"}


def connect_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                profile TEXT PRIMARY KEY,
                roster_json TEXT NOT NULL,
                swaps_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def validate_schedule(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")

    profile = data.get("profile")
    if not isinstance(profile, str) or profile not in PROFILES:
        raise ValueError("Unknown schedule profile.")

    roster = data.get("roster")
    if not isinstance(roster, dict) or set(roster) != WORKERS:
        raise ValueError("Roster must contain every known worker.")
    clean_roster = {}
    for worker_id, assignments in roster.items():
        if not isinstance(assignments, dict) or set(assignments) != DAYS:
            raise ValueError("Each worker must have one assignment for every day.")
        if any(
            not isinstance(shift, str) or shift not in PROFILES[profile]
            for shift in assignments.values()
        ):
            raise ValueError("Roster contains a shift that is not valid for this profile.")
        clean_roster[worker_id] = assignments

    swaps = data.get("swaps")
    if not isinstance(swaps, list) or len(swaps) > 1000:
        raise ValueError("Swap requests must be a list of at most 1,000 items.")
    clean_swaps = []
    seen_ids = set()
    for swap in swaps:
        if not isinstance(swap, dict):
            raise ValueError("Each swap request must be an object.")
        swap_id = swap.get("id")
        requester = swap.get("req")
        target = swap.get("tgt")
        day = swap.get("day")
        status = swap.get("status")
        if not isinstance(swap_id, str) or not swap_id or len(swap_id) > 100 or swap_id in seen_ids:
            raise ValueError("Swap request IDs must be unique non-empty strings.")
        if (
            not isinstance(requester, str)
            or not isinstance(target, str)
            or requester not in WORKERS
            or target not in WORKERS
            or requester == target
        ):
            raise ValueError("Swap request must name two different known workers.")
        if (
            not isinstance(day, str)
            or not isinstance(status, str)
            or day not in DAYS
            or status not in SWAP_STATUSES
        ):
            raise ValueError("Swap request has an invalid day or status.")
        seen_ids.add(swap_id)
        clean_swaps.append(
            {"id": swap_id, "req": requester, "tgt": target, "day": day, "status": status}
        )
    return profile, clean_roster, clean_swaps


class ShiftFairHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if request.path == "/api/state":
            profile = parse_qs(request.query).get("profile", [None])[0]
            if profile not in PROFILES:
                self.send_json(400, {"error": "Unknown schedule profile."})
                return
            with connect_db() as connection:
                row = connection.execute(
                    "SELECT roster_json, swaps_json, updated_at FROM schedules WHERE profile = ?",
                    (profile,),
                ).fetchone()
            if row is None:
                self.send_json(200, {"saved": False})
            else:
                self.send_json(
                    200,
                    {
                        "saved": True,
                        "roster": json.loads(row["roster_json"]),
                        "swaps": json.loads(row["swaps_json"]),
                        "updatedAt": row["updated_at"],
                    },
                )
            return

        if request.path in {"/", "/index.html"}:
            try:
                body = (ROOT / "index.html").read_bytes()
            except OSError:
                self.send_error(500, "Dashboard file is unavailable.")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_PUT(self):
        if urlsplit(self.path).path != "/api/state":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid content length."})
            return
        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "Request body is empty or too large."})
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
            profile, roster, swaps = validate_schedule(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self.send_json(400, {"error": str(error)})
            return

        updated_at = datetime.now(timezone.utc).isoformat()
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO schedules (profile, roster_json, swaps_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(profile) DO UPDATE SET
                    roster_json = excluded.roster_json,
                    swaps_json = excluded.swaps_json,
                    updated_at = excluded.updated_at
                """,
                (
                    profile,
                    json.dumps(roster, separators=(",", ":")),
                    json.dumps(swaps, separators=(",", ":")),
                    updated_at,
                ),
            )
        self.send_json(200, {"ok": True, "updatedAt": updated_at})

    def log_message(self, format_string, *args):
        print("%s - %s" % (self.address_string(), format_string % args))


if __name__ == "__main__":
    initialize_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ShiftFairHandler)
    print(f"ShiftFair server listening on port {PORT}; SQLite data: {DB_PATH}")
    server.serve_forever()
