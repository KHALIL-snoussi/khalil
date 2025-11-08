#!/bin/bash
# Quick start script for Diamond Painting Generator

set -e

echo "=== Diamond Painting Generator - Quick Start ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

echo "✓ Python 3 found"

# Check Flutter
if ! command -v flutter &> /dev/null; then
    echo "Warning: Flutter not found. You'll need to install Flutter to run the frontend."
    SKIP_FRONTEND=1
else
    echo "✓ Flutter found"
    SKIP_FRONTEND=0
fi

echo ""
echo "=== Setting up Backend ==="
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Copy .env if needed
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Generate test images
echo "Generating test images..."
python scripts/generate_test_image.py

echo ""
echo "✓ Backend setup complete!"

cd ..

if [ "$SKIP_FRONTEND" -eq 0 ]; then
    echo ""
    echo "=== Setting up Frontend ==="
    cd frontend

    echo "Installing Flutter dependencies..."
    flutter pub get

    echo ""
    echo "✓ Frontend setup complete!"

    cd ..
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend (in terminal 1):"
echo "   cd backend"
echo "   source .venv/bin/activate"
echo "   make run"
echo ""

if [ "$SKIP_FRONTEND" -eq 0 ]; then
    echo "2. Start the frontend (in terminal 2):"
    echo "   cd frontend"
    echo "   flutter run -d chrome"
    echo ""
fi

echo "3. Run tests:"
echo "   cd backend"
echo "   make test"
echo ""
echo "4. Test API:"
echo "   cd backend"
echo "   bash scripts/test_api.sh"
echo ""
echo "Visit http://localhost:8000/docs for API documentation"
