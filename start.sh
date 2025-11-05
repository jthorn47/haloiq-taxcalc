#!/usr/bin/env sh
set -e
PORT=${PORT:-8000}
exec python3 -m uvicorn app:app --host 0.0.0.0 --port "$PORT"
