# Small, reliable Python base
FROM python:3.11-slim

# System deps (needed by scientific Python libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gfortran \
  && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

EXPOSE 10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
