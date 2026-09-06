FROM python:3.11-slim

WORKDIR /app

# System deps for OpenCV / face engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY frontend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy monorepo
COPY . /app

# Streamlit configuration
COPY frontend/.streamlit /app/.streamlit

EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "frontend/app/main.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true"]
