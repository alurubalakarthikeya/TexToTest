# Dummy in-memory vector DB for demonstration
# Replace with real vector DB (e.g., Chroma, Pinecone, FAISS) for production

_context_store = []

def store_text(text):
    """Store text in the vector database"""
    _context_store.append(text)

def get_context():
    """Retrieve all stored context as a single string"""
    if _context_store:
        return " ".join(_context_store)
    return None

def clear_context():
    """Clear all stored context"""
    global _context_store
    _context_store = []

def get_context_chunks():
    """Get individual context chunks"""
    return _context_store.copy()
