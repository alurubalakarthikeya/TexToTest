#!/usr/bin/env python3
"""
Standalone server starter for TexToTest backend
"""

import uvicorn
from app import app

if __name__ == "__main__":
    print("Starting TexToTest Backend Server...")
    uvicorn.run(
        "app:app",
        host="127.0.0.1", 
        port=8000,
        reload=False,
        log_level="info"
    )