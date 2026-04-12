#!/bin/sh

echo "[STARTUP] Launching A11y-Agent-Pro-Max Services..."

# 1. Start FastAPI in background
echo "[STARTUP] Starting FastAPI on port 8000..."
uvicorn app:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &

# 2. Start Streamlit in background
echo "[STARTUP] Starting Streamlit on port 8501..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false > streamlit.log 2>&1 &

# 3. Give services time to warm up
sleep 5
echo "[STARTUP] Services warmed up. Launching Nginx Gateway on port 7860..."

# 4. Start Nginx in foreground (Master Process)
exec nginx -g 'daemon off;'
