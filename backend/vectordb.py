import os
from typing import List, Optional

# Simple persistence to survive across requests within the same instance
_context_store: List[str] = []
PERSIST_PATH = os.environ.get("CONTEXT_FILE", os.path.join("uploads", "context_latest.txt"))

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def store_text(text: str):
    """Store text and persist to disk."""
    global _context_store
    if not text:
        return
    _context_store.append(text)
    try:
        _ensure_dir(PERSIST_PATH)
        with open(PERSIST_PATH, "w", encoding="utf-8") as f:
            f.write("\n\n".join(_context_store))
    except Exception:
        # Best-effort persistence
        pass

def get_context() -> Optional[str]:
    """Retrieve context from memory; if empty, try disk."""
    if _context_store:
        return " ".join(_context_store)
    try:
        if os.path.exists(PERSIST_PATH):
            with open(PERSIST_PATH, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read().strip()
                if data:
                    _context_store.append(data)
                    return data
    except Exception:
        pass
    return None

def clear_context():
    """Clear context from memory and disk."""
    global _context_store
    _context_store = []
    try:
        if os.path.exists(PERSIST_PATH):
            os.remove(PERSIST_PATH)
    except Exception:
        pass

def get_context_chunks() -> List[str]:
    return list(_context_store)
