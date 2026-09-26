# passport_service.py
import io
import os
import sys
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from pydantic import BaseModel
import pytesseract
from passporteye import read_mrz

# ==============================================================================
# 1. WINDOWS ENVIRONMENT & TESSERACT CONFIGURATION
# PassportEye relies on calling 'tesseract' via system subprocess.
# Therefore, we MUST inject the Tesseract installation directory directly into
# the OS process PATH, otherwise Windows throws WinError 2 (File Not Found).
# ==============================================================================

# Common standard install directory for Tesseract 64-bit on Windows
TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"
TESSERACT_EXE = os.path.join(TESSERACT_DIR, "tesseract.exe")
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")

if os.path.exists(TESSERACT_DIR):
    # 1. Prepend to system PATH so subprocesses (PassportEye) locate 'tesseract.exe'
    if TESSERACT_DIR not in os.environ["PATH"]:
        os.environ["PATH"] = TESSERACT_DIR + os.pathsep + os.environ["PATH"]
        print(f"[CONFIG] Added Tesseract folder to PATH: {TESSERACT_DIR}")

    # 2. Tell pytesseract explicitly where the executable is
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

    # 3. Set the TESSDATA_PREFIX so Tesseract knows where OCR language files reside
    os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR
    print(f"[CONFIG] Configured TESSDATA_PREFIX: {TESSDATA_DIR}")
else:
    print(f"[WARN] Tesseract directory not found at standard path: {TESSERACT_DIR}")
    print("[WARN] Ensure Tesseract is installed and available in system environment PATH.")


# ==============================================================================
# 2. PYDANTIC RESPONSE SCHEMA
# Structured format for client responses (e.g., Form-C verification interface)
# ==============================================================================
class PassportDataResponse(BaseModel):
    """
    Structured response payload returning recognized identity fields
    and verification flags.
    """
    valid_mrz: bool
    document_type: Optional[str] = None
    country: Optional[str] = None
    surname: Optional[str] = None
    names: Optional[str] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    expiration_date: Optional[str] = None
    raw_mrz_text: Optional[str] = None
    warnings: List[str] = []


# ==============================================================================
# 3. INITIALIZE FASTAPI APPLICATION
# ==============================================================================
# Instantiating the core API application instance
app = FastAPI(
    title="Passport Extraction Microservice",
    description="Microservice to parse passport bio pages and extract structured MRZ fields.",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    """
    Health probe to confirm ASGI server is running and detect Tesseract.
    """
    tesseract_installed = os.path.exists(TESSERACT_EXE)
    return {
        "status": "healthy",
        "tesseract_detected": tesseract_installed,
        "tesseract_path": TESSERACT_EXE if tesseract_installed else "Not Found"
    }


@app.post(
    "/extract-passport",
    response_model=PassportDataResponse,
    status_code=status.HTTP_200_OK
)
async def extract_passport(
    # UploadFile handles file streams without reading entire file onto disk beforehand
    file: UploadFile = File(...)
):
    """
    Receives an uploaded passport image, passes binary data to PassportEye,
    extracts MRZ data, validates checksums, and returns parsed fields.
    """
    # Step 1: Validate file MIME content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{file.content_type}'. Please upload an image file (PNG, JPG, JPEG)."
        )

    # Step 2: Read binary contents safely into memory
    try:
        image_bytes = await file.read()
    except Exception as read_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded image stream: {str(read_err)}"
        )

    # Step 3: Run MRZ Extraction with comprehensive error trapping
    try:
        # Wrap bytes in BytesIO stream for PassportEye
        image_stream = io.BytesIO(image_bytes)

        # Call PassportEye's read_mrz function
        # This will automatically preprocess, isolate the MRZ band, and call Tesseract
        mrz_record = read_mrz(image_stream)

    except FileNotFoundError as fnf_err:
        # Occurs if Windows still cannot find tesseract binary
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Tesseract executable not found by worker process. "
                f"Ensure Tesseract is installed at {TESSERACT_EXE}. Details: {str(fnf_err)}"
            )
        )
    except Exception as ocr_err:
        # Catch unexpected PIL/OpenCV image decoding or parsing errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while running OCR pipeline: {str(ocr_err)}"
        )

    # Step 4: Validate detection result
    if mrz_record is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Unable to locate or decode the Machine Readable Zone (MRZ). "
                "Ensure the photo is clear, well-lit, non-skewed, and the bottom 2 lines are visible."
            )
        )

    # Step 5: Safely parse fields and handle PassportEye dict output
    try:
        mrz_dict: Dict[str, Any] = mrz_record.to_dict() if hasattr(mrz_record, "to_dict") else {}
    except Exception:
        mrz_dict = {}

    # Extract raw text if available
    raw_mrz = getattr(mrz_record, "raw_text", None)

    # Determine validity: valid_score in PassportEye is typically an int (e.g. 100) or bool
    score = getattr(mrz_record, "valid_score", 0)
    is_valid = bool(score >= 80) if isinstance(score, (int, float)) else bool(score)

    warnings: List[str] = []
    if not is_valid:
        warnings.append("MRZ checksum validation score is low. Verify fields manually against image.")

    # Step 6: Return clean response
    return PassportDataResponse(
        valid_mrz=is_valid,
        document_type=mrz_dict.get("type"),
        country=mrz_dict.get("country"),
        surname=mrz_dict.get("surname"),
        names=mrz_dict.get("names"),
        passport_number=mrz_dict.get("number"),
        nationality=mrz_dict.get("nationality"),
        date_of_birth=mrz_dict.get("date_of_birth"),
        sex=mrz_dict.get("sex"),
        expiration_date=mrz_dict.get("expiration_date"),
        raw_mrz_text=raw_mrz,
        warnings=warnings
    )