FROM python:3.10-slim

# 1) system tools for building wheels (harmless if wheels exist)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) install deps first for caching
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip setuptools wheel \
 && python3 -m pip install --no-cache-dir -r requirements.txt

# 3) copy app
COPY . .

# 4) helpful debug: ensure start.sh exists and permissions are correct
RUN ls -la /app \
 && test -f /app/app.py \
 && chmod +x /app/start.sh || true

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# 5) print diagnostics, then start uvicorn. Any missing piece will be obvious in logs.
CMD ["sh", "-c", "\
  echo '--- DEBUG: listing /app ---' && ls -la /app && \
  echo '--- DEBUG: python version ---' && python3 -V && \
  echo '--- DEBUG: pip list (uvicorn/fastapi/taxcalc) ---' && python3 -m pip show uvicorn fastapi taxcalc || true && \
  echo '--- DEBUG: starting uvicorn ---' && \
  exec python3 -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} \
"]
