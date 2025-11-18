#!/bin/bash
# Build script for Render deployment

echo "Starting build process..."

# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# Install core dependencies first
pip install fastapi==0.104.1 uvicorn==0.24.0

# Try to install remaining dependencies
pip install -r requirements.txt || echo "Some dependencies failed to install, continuing..."

echo "Build complete!"