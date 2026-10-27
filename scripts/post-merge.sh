#!/usr/bin/env bash
set -euo pipefail

# Validate the server and initialize its idempotent SQLite schema after merges.
python3 -m py_compile server.py
python3 -c 'from server import initialize_db; initialize_db()'
