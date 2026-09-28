# ==============================================================================
# Dockerfile: TesseractAPI
# Image OCR extraction service for handwritten arrival forms & cards
# ==============================================================================

# Use official Python 3.11 slim image
FROM python:3.11-slim

# Prevent bytecode caching and ensure immediate log output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set container working directory
WORKDIR /app

# Install Tesseract OCR binary, English language pack, and OpenCV support libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements file first to take advantage of Docker layer caching
COPY requirements.txt .

# Install Python libraries
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code into the container
COPY . .

# Expose internal listening port for TesseractAPI
EXPOSE 8001

# Start server using uvicorn (adjust if your entrypoint is app.py -> app:app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
