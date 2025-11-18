#!/bin/bash
# Build script for Render deployment

echo "Starting build process..."

# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
pip install -r requirements.txt

echo "Build complete!"