# config.py
"""
Central configuration module for the OCR extraction microservice.
Reads system environment variables with reliable local fallback defaults.
"""
import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# ==============================================================================
# 1. NETWORK & SERVER BINDING SETTINGS
# ==============================================================================
# Host IP: "127.0.0.1" for local Windows testing, "0.0.0.0" on production Ubuntu
SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")

# Port for FastAPI application
SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

# Worker processes (1 for local reload development, (2*cores)+1 on production)
SERVER_WORKERS: int = int(os.getenv("SERVER_WORKERS", "1"))

# Reload flag (True during local development, False in production)
SERVER_RELOAD: bool = os.getenv("SERVER_RELOAD", "True").lower() in ("true", "1")

# Base API Prefix or Route Path (e.g. "" or "/api/v1")
API_PREFIX: str = os.getenv("API_PREFIX", "")

# ==============================================================================
# 2. TESSERACT SYSTEM EXECUTABLE & DATA DIRECTORIES
# ==============================================================================
# Default Windows installation path
WINDOWS_DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR"

# Check if running on Windows and standard path exists
if os.name == "nt" and os.path.exists(WINDOWS_DEFAULT_TESSERACT):
    TESSERACT_CMD: str = os.getenv(
        "TESSERACT_CMD", 
        os.path.join(WINDOWS_DEFAULT_TESSERACT, "tesseract.exe")
    )
    TESSDATA_PREFIX: str = os.getenv(
        "TESSDATA_PREFIX", 
        os.path.join(WINDOWS_DEFAULT_TESSERACT, "tessdata")
    )
else:
    # On Linux (Ubuntu), Tesseract resides in /usr/bin/tesseract or standard PATH
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    TESSDATA_PREFIX: str = os.getenv("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/4.00/tessdata")