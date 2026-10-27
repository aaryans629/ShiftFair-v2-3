# ShiftFair v2.3

A standalone workforce scheduling dashboard prototype with admin and worker views, roster generation, fairness metrics, fatigue alerts, and shift-swap interactions.

## Run on Replit

Start the **Start application** workflow to open the dashboard in the Replit preview. It runs `server.py`, which serves the page and its schedule API.

To run it locally with Python:

```sh
python3 server.py
```

Then open `http://localhost:5000`.

## Schedule storage

Roster assignments and swap requests are saved in a local SQLite database (`shiftfair.sqlite3`) by the Python server. Each schedule profile has its own saved roster and swap queue, and changes are shared with everyone using the same running app. The database is created automatically on first run. Set `SHIFTFAIR_DB_PATH` to store it at a different path.

When a profile has no saved schedule, the dashboard shows its sample demo data and labels it **Demo schedule**. Demo data is not written to SQLite until someone edits or generates a roster, submits or updates a swap, or otherwise changes the schedule. Saved schedules are labeled **Shared saved schedule**.

This prototype has no sign-in or per-person permissions: anyone who can access the running app can see and change its shared schedules. SQLite is appropriate for this single-instance prototype; deployments that need account isolation, multiple server instances, or managed backups should move schedule storage to a hosted database and add authentication.

The page loads React, HTM, and Tailwind CSS from public CDNs, so those services and an internet connection are required for the UI.
