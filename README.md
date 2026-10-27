# ShiftFair v2.3

A standalone workforce scheduling dashboard prototype with admin and worker views, roster generation, fairness metrics, fatigue alerts, and shift-swap interactions.

## Run on Replit

The project is served as a static web page. Start the **Start application** workflow to open it in the Replit preview.

To run it locally with Python:

```sh
python3 -m http.server 5000 --bind 0.0.0.0
```

Then open `http://localhost:5000`.

The page loads React, HTM, and Tailwind CSS from public CDNs, so those services and an internet connection are required. This prototype keeps its sample roster and interactions in browser memory; it does not save data or connect to a backend.
