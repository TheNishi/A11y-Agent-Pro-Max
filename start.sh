#!/bin/sh

# Start FastAPI in background
uvicorn app:app --host 0.0.0.0 --port 8000 &

# Start Streamlit in background on port 8501
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false &

# Start Nginx in foreground to route port 7860 to both services
nginx -g 'daemon off;'
