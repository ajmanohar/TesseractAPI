# run.py
"""
Primary execution script to launch the ASGI server
using parameters loaded dynamically from config.py.
"""
import uvicorn
import config

if __name__ == "__main__":
    print(f"[*] Starting OCR Microservice on http://{config.SERVER_HOST}:{config.SERVER_PORT}{config.API_PREFIX}")
    print(f"[*] Loaded Tesseract Path: {config.TESSERACT_CMD}")
    
    # Run uvicorn server programmatically
    uvicorn.run(
        "passport_service:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.SERVER_RELOAD,
        workers=config.SERVER_WORKERS if not config.SERVER_RELOAD else 1
    )