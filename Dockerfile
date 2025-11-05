FROM python:3.10-slim

# Minimal build tools so wheels can install if needed
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for layer cache
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip setuptools wheel \
 && python3 -m pip install --no-cache-dir -r requirements.txt

# App code + start script
COPY . .
RUN chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# IMPORTANT: single, explicit start command (no shell quoting)
CMD ["/app/start.sh"]
