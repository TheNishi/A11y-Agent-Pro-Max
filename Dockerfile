FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Ensure start script is executable
RUN chmod +x start.sh

# Environment variables
ENV API_BASE_URL="http://localhost:8000"
ENV MODEL_NAME="gpt-4o"
ENV HF_TOKEN=""

# Streamlit/FastAPI standard port
EXPOSE 7860
EXPOSE 8000

CMD ["./start.sh"]
