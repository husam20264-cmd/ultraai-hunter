#!/bin/bash
# Render يوفر البورت عبر متغير البيئة هذا
PORT=${PORT:-8000}
echo "Starting UltraAI on port $PORT"
uvicorn main:app --host 0.0.0.0 --port $PORT
