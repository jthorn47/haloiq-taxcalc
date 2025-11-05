FROM python:3.10-slim

# System deps (ssl/certs/locale sometimes needed by pandas/taxcalc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (better cache)
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# We’ll bind to 10000 explicitly (Render will detect it and rewire)
ENV PORT=10000
EXPOSE 10000

# Start server (no shell tricks, no env substitution)
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
