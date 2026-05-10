#!/bin/bash
PORT=${PORT:-8000}
echo "Starting UltraAI on port $PORT"
exec python -u -m uvicorn main:app --host 0.0.0.0 --port $PORT
