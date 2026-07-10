# backend/app/core/config.py
from pathlib import Path
import os

class Settings:
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    BACKEND_DIR = BASE_DIR / "backend"
    DATA_DIR = BACKEND_DIR / "data"
    
    # Separate folders for different knowledge bases
    VENDOR_PDF_DIR = DATA_DIR / "vendor_manuals"
    GOVT_PDF_DIR = DATA_DIR / "govt_rules"
    PROCESSED_DIR = DATA_DIR / "processed"
    
    # Separate vector DBs for different roles
    VENDOR_DB_DIR = BACKEND_DIR / "db" / "qdrant_vendor"
    GOVT_DB_DIR = BACKEND_DIR / "db" / "qdrant_govt"

    # Create directories
    for dir_path in [VENDOR_PDF_DIR, GOVT_PDF_DIR, PROCESSED_DIR, 
                     VENDOR_DB_DIR, GOVT_DB_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    EMBEDDING_MODEL = "bge-m3"
    LLM_MODEL = "mistral:latest"
    TRANSLATION_MODEL = "sarvam-cpu"
    
    # Qdrant Configuration
    VENDOR_COLLECTION = "vendor_manuals"
    GOVT_COLLECTION = "govt_rules"

    # Document Processing
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 150
    MAX_FILE_SIZE_MB = 50

    # API Configuration
    API_V1_PREFIX = "/api/v1"
    CORS_ORIGINS = ["*"]  # <-- ADD THIS LINE
    
    # Session storage
    SESSION_TIMEOUT_SECONDS = 3600
    OCR_LANGUAGES = ['hi', 'en']
    OCR_GPU = False

settings = Settings()

print("=" * 50)
print("CG e-Procurement Chatbot Configuration")
print("=" * 50)
print(f"Vendor PDF Directory: {settings.VENDOR_PDF_DIR}")
print(f"Govt PDF Directory: {settings.GOVT_PDF_DIR}")
print(f"Vendor Vector DB: {settings.VENDOR_DB_DIR}")
print(f"Govt Vector DB: {settings.GOVT_DB_DIR}")
print(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
print(f"LLM Model: {settings.LLM_MODEL}")
print(f"Translation Model: {settings.TRANSLATION_MODEL}")
print("=" * 50)