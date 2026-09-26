# TesseractAPI - Passport MRZ & Identity OCR Microservice

A modular, lightweight REST API microservice built with **FastAPI**, **PassportEye**, and **Tesseract OCR**. It accepts images of passport bio-data pages, isolates the Machine Readable Zone (MRZ) according to **ICAO Doc 9303** specifications, extracts identity fields, performs cryptographic checksum validations, and returns clean structured JSON payloads.

---

## 1. Why It Is Built

When managing guest registrations (such as homestay Form-C foreign guest registration), extracting details manually from international passports is error-prone. Generic OCR engines frequently struggle with complex page backgrounds and security patterns. 

This service:
* Targets the standardized two-line **Machine Readable Zone (MRZ)** at the bottom of standard international passports.
* Extracts critical fields: Surname, Given Names, Passport Number, Nationality, Date of Birth, Sex, and Expiry Date.
* Evaluates cryptographic check digits built into the MRZ, providing a safety flag (`valid_mrz`) to catch OCR inaccuracies.
* Provides a decoupled backend API that can be consumed by Android apps, web dashboards, or background workers over HTTP.

## Home Lab Series & Architecture Vision

> This project is part of an ongoing **Self-Hosted Home Lab Series** showcasing privacy-first, on-premise automation workflows.

The primary objective of this microservice is to run self-hosted on a dedicated local desktop server running **Ubuntu** within a local home lab network. 

### Why Host Locally in a Home Lab?
* **Data Privacy & Compliance**: Identity documents (passports, visas, and arrival forms) contain sensitive personal information[cite: 1, 2]. Processing them inside a local network eliminates the need to route guest data through third-party cloud OCR providers.
* **Low Latency & High Availability**: Local devices (such as Android ingestion tablets or desktop check-in apps) communicate directly with the local server via LAN over fast internal HTTP connections[cite: 1].
* **Resource Optimization**: Heavier OCR pipelines and image preprocessing are offloaded from low-power client devices (like phones or tablets) to dedicated home lab compute infrastructure without external API costs[cite: 1].
* **Modular Integration**: While initially tested on local development environments (Windows/VS Code), the service is architected to deploy seamlessly onto an Ubuntu home server using Systemd or Docker, serving as the OCR backbone for projects like automated registration assistants and Form-C immigration pipelines[cite: 1].

---

## 2. Project Architecture

```text
TesseractAPI/
├── config.py              # Dynamic configuration for network ports, hosts, and paths
├── models.py              # Pydantic data contracts (Form-C & MRZ payload schemas)
├── passport_service.py    # FastAPI endpoints, Tesseract environment setup, and MRZ pipeline
├── run.py                 # Application launcher
├── requirements.txt       # Python package dependencies
├── .gitignore             # Git exclusion rules
└── README.md              # Project documentation
```

## 3. Local Development (VS Code / Windows)
1. Prerequisites
    * Python 3.10+: Ensure Python is installed and added to your system PATH.
    * Tesseract OCR (Windows):
        * Download and run the 64-bit installer from the UB-Mannheim Tesseract repository.
        * Default path: C:\Program Files\Tesseract-OCR\tesseract.exe.

2. Setup Steps in VS Code
    * Open the project root folder in VS Code (File > Open Folder...).
    * Open the built-in terminal (Ctrl + `) and initialize a virtual environment:
        ```PowerShell
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * Install dependencies:
        ```PowerShell
        pip install -r requirements.txt
        ```
    * Start the service:
        ```PowerShell
        python run.py
        ```

    * Test the endpoints:
        * Health Check: Open http://127.0.0.1:8000/health
        * Interactive Swagger UI: Open http://127.0.0.1:8000/docs

## 4. Ubuntu Server Installation & Production Testing
Use this guide when migrating and deploying the service onto an Ubuntu server.

1. Install Ubuntu System Packages & Tesseract
```Bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip tesseract-ocr tesseract-ocr-eng libgl1 libglib2.0-0 git
```

2. Clone Repository & Setup Virtual Environment
```Bash
cd /opt
sudo git clone [https://github.com/ajmanohar/TesseractAPI.git](https://github.com/ajmanohar/TesseractAPI.git)
cd TesseractAPI

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

3. Configure Ubuntu Environment Variables
You can override runtime parameters via environment variables without changing code:

```Bash
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8000"
export SERVER_RELOAD="False"
export TESSERACT_CMD="/usr/bin/tesseract"
export TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata"
```

4. Run & Test on Ubuntu
```Bash
# Launch server
python run.py
```
Test extraction from another terminal or client:
```Bash
curl -X POST "http://<SERVER_IP>:8000/extract-passport" \
-H "Content-Type: multipart/form-data" \
-F "file=@/path/to/passport_sample.jpg"
```

## 5. API Reference
#### Health Probe
* Endpoint: GET /health
* Response:
```JSON
{
  "status": "healthy",
  "tesseract_detected": true,
}
```
#### Passport Extraction
* Endpoint: POST /extract-passport
* Content-Type: multipart/form-data
* Payload: file (Image binary - JPEG/PNG)
* Response:
```JSON
{
  "valid_mrz": true,
  "document_type": "P",
  "country": "GBR",
  "surname": "SMITH",
  "names": "JANE ALICE",
  "passport_number": "987654321",
  "nationality": "GBR",
  "date_of_birth": "880512",
  "sex": "F",
  "expiration_date": "280511",
  "raw_mrz_text": "P<GBRSMITH<<JANE<ALICE<<<<<<<<<<<<<<<<<<<<<<\n9876543214GBR8805126F2805118<<<<<<<<<<<<<<<02",
  }
  ```