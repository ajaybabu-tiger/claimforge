#!/bin/bash
set -e

PORT="${PORT:-3000}"
export PORT
export BACKEND_INTERNAL_URL="http://127.0.0.1:8000"

echo "=================================================="
echo " Starting ClaimForge Full-Stack Production Server "
echo " Public Port: $PORT                               "
echo "=================================================="

# 1. Start FastAPI Backend in background on internal port 8000
echo "[1/2] Launching FastAPI backend on 127.0.0.1:8000..."
cd /app/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend health check with retry
echo "Waiting for backend service to become ready..."
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "[OK] Backend is healthy and ready!"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "[WARN] Backend health check timed out, proceeding to start frontend..."
  fi
  sleep 1
done

# 2. Start Next.js Frontend on assigned public $PORT
echo "[2/2] Launching Next.js frontend on 0.0.0.0:$PORT..."
cd /app/frontend
exec npx next start -p "$PORT" -H 0.0.0.0
