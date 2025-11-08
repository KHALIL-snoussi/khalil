#!/bin/bash
# QBRIX Diamond Painting Generator - Quick Start

set -e

echo "=== QBRIX Diamond Painting Generator - Quick Start ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.11+ is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION found"

echo ""
echo "=== Setting up QBRIX Backend ==="
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
echo "Installing dependencies (this may take a few minutes)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✓ Backend setup complete!"

echo ""
echo "=== Running Tests ==="
pytest tests/test_qbrix_*.py -v

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the QBRIX API server:"
echo ""
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  python app_qbrix.py"
echo ""
echo "The API will be available at http://localhost:8000"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "See QBRIX_README.md for full documentation and examples."
echo ""
echo "Example API call:"
echo ""
echo "  curl http://localhost:8000/health"
echo ""
