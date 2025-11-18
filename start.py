#!/usr/bin/env python3
"""
Simple startup script for production deployment
"""
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import uvicorn
    from app import app
    
    # Get port from environment or default to 8000
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting TexToTest server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)