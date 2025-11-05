# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip setuptools wheel \
 && python3 -m pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Expose the Render port (Render assigns $PORT automatically)
EXPOSE 8000

# Run FastAPI app with uvicorn using the assigned PORT
CMD ["sh", "-c", "exec python3 -m uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
