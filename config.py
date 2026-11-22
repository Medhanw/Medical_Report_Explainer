"""
Configuration module for Medical Report Explainer.
Handles environment variables, constants, paths, and model settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
SAMPLES_DIR = BASE_DIR / "sample_reports"
DOCS_DIR = BASE_DIR / "docs"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Ensure essential directories exist
for folder in [OUTPUTS_DIR, SAMPLES_DIR, DOCS_DIR, SCREENSHOTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Gemini Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Supported File Formats
SUPPORTED_FILE_EXTENSIONS = [".pdf", ".txt"]
MAX_FILE_SIZE_MB = 10

# Universal Medical Disclaimer
MEDICAL_DISCLAIMER = (
    "This application is intended for educational purposes only. It does not provide medical diagnoses "
    "or replace professional medical advice. Laboratory reference ranges can vary between laboratories "
    "and individuals. Consult a qualified healthcare professional for interpretation of your results."
)
