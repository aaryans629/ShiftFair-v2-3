# Running ShiftFair

The Replit preview runs `server.py` on port 5000. It serves `index.html` and exposes the schedule API:

```sh
python3 server.py
```

Start the **Start application** workflow to run the dashboard.

Roster assignments and swap requests are stored in `shiftfair.sqlite3`, using Python's built-in SQLite support. The database is shared by users of the same running app and stores separate schedules for each profile. Profiles without a saved row display demo data until changed. This is shared workspace data, not private per-user data; the app does not include sign-in or access controls.

Set `SHIFTFAIR_DB_PATH` to put the SQLite file outside the project directory. The page loads React, HTM, and Tailwind CSS from public CDNs.
