FROM python:3.10-slim

# 1) OS packages that help wheels compile (safe even if wheels exist)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) Install Python deps first for better caching
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip setuptools wheel \
 && python3 -m pip install --no-cache-dir -r requirements.txt

# 3) Copy code
COPY . .

ENV PYTHONUNBUFFERED=1

# 4) Expose (Render sets $PORT; we default to 8000 if missing)
EXPOSE 8000
CMD ["sh", "-c", "python3 -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
