#!/bin/sh

# Start FastAPI in background
uvicorn app:app --host 0.0.0.0 --port 8000 &

# Start Streamlit on the specified HF port (usually 7860)
streamlit run streamlit_app.py --server.port 7860 --server.address 0.0.0.0
