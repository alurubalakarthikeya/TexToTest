import os
from typing import Optional

def extract_text_from_file(file_path: str) -> Optional[str]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return text
        except Exception:
            return None
    # Add more file types as needed
    return None
