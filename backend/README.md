# Diamond Painting Generator - Backend

FastAPI backend for diamond painting pattern generation with advanced image processing.

## Features

- **Color Space Conversion**: Custom RGB↔LAB implementation for perceptually accurate color matching
- **Advanced Dithering**: Floyd-Steinberg and Bayer ordered dithering
- **Image Preprocessing**: Gamma, bilateral filter, unsharp mask, optional white balance
- **PDF Generation**: Vector-based A4 patterns with ReportLab
- **RESTful API**: FastAPI with automatic OpenAPI documentation

## API Endpoints

### Health Check
```
GET /health
```

### Generate Preview
```
POST /preview
Content-Type: multipart/form-data

Fields:
  - image: File (JPG/PNG)
  - payload: JSON string (see schemas)
```

### Generate Final Pattern
```
POST /final
Content-Type: application/json

Body: FinalRequest JSON
Response: ZIP file
```

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run server
make run
```

## Development

### Run Tests
```bash
make test
```

### Format Code
```bash
make format
```

### Lint Code
```bash
make lint
```

### Docker Build
```bash
make build
docker run -p 8000:8000 diamond-backend
```

## Configuration

Edit `.env` file:

```env
DEFAULT_GRID_W=100
DEFAULT_GRID_H=140
MAX_UPLOAD_MB=15
OUTPUT_DPI=300
CORS_ORIGINS=http://localhost:*
```

## Project Structure

```
backend/
├── app.py                # FastAPI application
├── api_schemas.py        # Pydantic request/response models
├── palettes.py           # Color palettes and LAB conversion
├── settings.py           # Configuration management
├── pipeline/             # Image processing modules
│   ├── preprocess.py     # Gamma, filters, sharpening
│   ├── color.py          # Color space & palette mapping
│   ├── dither.py         # Dithering algorithms
│   ├── grid.py           # Grid operations
│   ├── render.py         # PNG & PDF rendering
│   └── export_pack.py    # ZIP packaging
├── tests/                # Unit & integration tests
│   ├── test_color.py
│   ├── test_dither.py
│   └── test_pipeline.py
└── samples/              # Test images
```

## Image Processing Pipeline

1. **Load & Orient** - EXIF rotation handling
2. **Rotate** - User-specified rotation
3. **Crop** - Extract region of interest
4. **Preprocess**:
   - Optional white balance (gray-world)
   - Gamma correction
   - Bilateral filter (denoise)
   - Unsharp mask (edge boost)
   - Optional background desaturation
5. **Resize** - Bicubic to grid dimensions
6. **RGB→LAB** - Perceptually uniform color space
7. **Dither** - Error diffusion or ordered
8. **Palette Map** - Nearest color (ΔE in LAB)
9. **Cleanup** - Optional speckle removal
10. **Render** - PNG preview & PDF pattern

## Color Conversion Math

### sRGB → Linear RGB
```python
if c <= 0.04045:
    linear = c / 12.92
else:
    linear = ((c + 0.055) / 1.055) ^ 2.4
```

### Linear RGB → XYZ (D65)
```
X = 0.4124*R + 0.3576*G + 0.1805*B
Y = 0.2127*R + 0.7152*G + 0.0722*B
Z = 0.0193*R + 0.1192*G + 0.9505*B
```

### XYZ → LAB
```
L* = 116 * f(Y/Yn) - 16
a* = 500 * (f(X/Xn) - f(Y/Yn))
b* = 200 * (f(Y/Yn) - f(Z/Zn))

where f(t) = t^(1/3) if t > δ³
            else (t/(3δ²) + 4/29)
            δ = 6/29
```

## Dithering Algorithms

### Floyd-Steinberg
```
Error distribution:
     X   7/16
3/16 5/16 1/16
```

### Bayer 8×8
Ordered dithering with threshold matrix.

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_color.py -v

# Run single test
pytest tests/test_color.py::TestColorConversion::test_rgb_to_lab_black -v
```

## Performance Tips

- Use smaller grid sizes for faster preview generation
- Bayer dithering is faster than Floyd-Steinberg
- Disable speckle cleanup if not needed
- Cache LAB values for palette (already implemented)

## API Documentation

Run the server and visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Use different port
uvicorn app:app --port 8001
```

### CORS Issues
```bash
# Update .env
CORS_ORIGINS=http://localhost:*,http://127.0.0.1:*
```
