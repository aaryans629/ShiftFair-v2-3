# Running ShiftFair

The Replit preview serves `index.html` with Python's built-in static HTTP server on port 5000:

```sh
python3 -m http.server 5000 --bind 0.0.0.0
```

Start the **Start application** workflow to run the dashboard.

The page loads React, HTM, and Tailwind CSS from public CDNs. The current prototype uses sample in-memory data only; roster changes and swap requests are not persisted or sent to a backend.
