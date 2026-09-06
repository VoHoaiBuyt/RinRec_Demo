FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire monorepo (needed for shared/ and backend/)
COPY . /app

# Expose API port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["python", "-m", "uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
