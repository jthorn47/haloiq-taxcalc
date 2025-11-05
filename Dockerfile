FROM python:3.10-slim

WORKDIR /app

# install deps first (better caching), then copy source
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# Render will map to whatever you listen on; default to 8000 if PORT not provided
EXPOSE 8000
CMD ["sh", "-c", "python3 -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
