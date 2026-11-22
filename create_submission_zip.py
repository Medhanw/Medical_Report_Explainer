"""
Creates the submission archive Code.zip excluding virtual environments,
bytecode, environment secrets, and cache folders.
"""

import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ZIP_OUTPUT_PATH = BASE_DIR / "Code.zip"

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
}

EXCLUDE_FILES = {
    ".env",
    "Code.zip",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
}


def create_submission_zip():
    print(f"Creating submission archive: {ZIP_OUTPUT_PATH}")
    file_count = 0
    with zipfile.ZipFile(ZIP_OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Modify dirs in-place to avoid traversing excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                file_path = Path(root) / file
                if file_path.suffix in EXCLUDE_EXTENSIONS:
                    continue

                rel_path = file_path.relative_to(BASE_DIR)
                zipf.write(file_path, arcname=str(rel_path))
                file_count += 1

    print(f"Archive successfully created with {file_count} files.")
    print(f"Archive size: {ZIP_OUTPUT_PATH.stat().st_size / 1024:.2f} KB")


def verify_zip():
    print(f"Verifying {ZIP_OUTPUT_PATH} integrity...")
    with zipfile.ZipFile(ZIP_OUTPUT_PATH, "r") as zipf:
        bad_file = zipf.testzip()
        if bad_file:
            raise ValueError(f"Corrupt file found in zip: {bad_file}")
        namelist = zipf.namelist()
        print(f"Total files verified in archive: {len(namelist)}")
        # Verify no .env or .pyc in zip
        for name in namelist:
            if name.endswith(".env") or name.endswith(".pyc") or ".venv" in name:
                raise ValueError(f"Excluded item found in zip: {name}")
    print("Verification PASSED: Code.zip is valid, clean, and ready for submission.")


if __name__ == "__main__":
    create_submission_zip()
    verify_zip()
