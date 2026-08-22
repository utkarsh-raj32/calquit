"""ParcelPilot AI Support System - Configuration"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_files"

# Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")

# Dataset snapshot time (from README sheet)
DATASET_SNAPSHOT = "2026-08-16T11:00:00+05:30"

# JWT Secret (mock)
JWT_SECRET = os.getenv("JWT_SECRET", "parcelpilot-dev-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"

# ChromaDB
CHROMA_COLLECTION = "parcelpilot_docs"

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
