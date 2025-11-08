# Diamond Painting Generator (7-Color, A4)

A complete web-based application that converts photos into diamond painting patterns using fixed 7-color palettes. Features deterministic image processing with professional-grade color quantization and dithering.

## Features

- **Three Fixed Palettes**: Original (neutral), Vintage (warm sepia), Pop Art (saturated)
- **Intelligent Processing**: RGB→LAB color space conversion, Floyd-Steinberg dithering
- **A4 Portrait Output**: 100×140 grid (14,000 cells) at 2.1mm cell size
- **Complete Pattern Pack**: PDF grid + legend, PNG preview, CSV counts, JSON spec
- **Flutter Web UI**: Upload, crop, preview, and download with live previews

## Tech Stack

**Backend:**
- Python 3.11+, FastAPI, Uvicorn
- Pillow, NumPy for image processing
- ReportLab for PDF generation
- Custom RGB↔LAB conversion & Floyd-Steinberg dithering

**Frontend:**
- Flutter 3.x Web
- ExtendedImage for crop/zoom/rotate
- Responsive Material Design UI

## Quick Start

### Prerequisites

- Python 3.11+
- Flutter 3.x
- Make (optional)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
make run
# OR: uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
flutter pub get

# Run web app
flutter run -d chrome
```

Frontend will be available at `http://localhost:*` (Flutter assigns port)

## Usage

1. **Upload**: Select a photo (JPG/PNG, max 15 MB)
2. **Crop**: Adjust crop area and rotation to portrait aspect (100:140)
3. **Preview**: View three style options with color counts
4. **Download**: Select a style and download the ZIP pack

## API Documentation

### POST `/preview`

Generate previews for multiple styles.

**Request:**
```bash
curl -X POST http://localhost:8000/preview \
  -F "image=@photo.jpg" \
  -F 'payload={
    "crop": {"x": 0, "y": 0, "w": 1000, "h": 1400},
    "rotate_deg": 0,
    "grid": {"w": 100, "h": 140},
    "styles": ["original", "vintage", "popart"],
    "options": {
      "gamma": 1.0,
      "edge_boost": 0.25,
      "dither": "fs",
      "dither_strength": 1.0
    }
  }'
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "grid": {"w": 100, "h": 140},
  "previews": {
    "original": "data:image/png;base64,...",
    "vintage": "data:image/png;base64,...",
    "popart": "data:image/png;base64,..."
  },
  "counts": {
    "original": [1200, 2300, 3100, 2800, 2400, 1500, 700],
    "vintage": [...],
    "popart": [...]
  }
}
```

### POST `/final`

Generate final pattern pack.

**Request:**
```bash
curl -X POST http://localhost:8000/final \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "uuid-from-preview",
    "style": "original",
    "grid": {"w": 100, "h": 140},
    "palette_id": "original_v1",
    "crop": {"x": 0, "y": 0, "w": 1000, "h": 1400},
    "rotate_deg": 0,
    "options": {
      "gamma": 1.0,
      "edge_boost": 0.25,
      "dither": "fs",
      "dither_strength": 1.0
    }
  }' \
  --output pattern.zip
```

**Response:** ZIP file containing:
- `pattern.pdf` - Vector grid with legend (A4, 2 pages)
- `preview.png` - Scaled preview image
- `counts.csv` - Color counts with bag codes
- `spec.json` - Complete specification

### GET `/health`

Health check endpoint.

```bash
curl http://localhost:8000/health
# {"ok": true}
```

## Configuration

### Backend (backend/settings.py or .env)

```env
DEFAULT_GRID_W=100
DEFAULT_GRID_H=140
MAX_UPLOAD_MB=15
OUTPUT_DPI=300
CORS_ORIGINS=http://localhost:*
```

### Palettes

Edit `backend/palettes.py` to customize color palettes:

```python
ORIGINAL_PALETTE = ColorPalette(
    name="original_v1",
    colors=[
        ("Black", "#141414", (20, 20, 20)),
        ("DarkGray", "#3B4752", (59, 71, 82)),
        # ... 5 more colors (exactly 7 total)
    ],
)
```

Each palette must have exactly 7 colors.

## Testing

### Backend Tests

```bash
cd backend
make test

# OR:
pytest -v

# With coverage:
pytest --cov=. --cov-report=html
```

Tests include:
- RGB↔LAB color space conversion accuracy
- Dithering algorithm correctness
- Full pipeline integration
- PDF/PNG generation

## Docker Deployment

### Build Backend

```bash
cd backend
make build
# OR: docker build -t diamond-backend .
```

### Run with Docker

```bash
docker run -p 8000:8000 diamond-backend
```

## Project Structure

```
diamond-painting/
├── README.md
├── LICENSE
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── api_schemas.py         # Pydantic models
│   ├── palettes.py            # Color palettes & LAB conversion
│   ├── settings.py            # Configuration
│   ├── pipeline/
│   │   ├── preprocess.py      # Gamma, denoise, sharpen
│   │   ├── color.py           # RGB/LAB conversion, nearest-color
│   │   ├── dither.py          # Floyd-Steinberg & Bayer
│   │   ├── grid.py            # Resize & speckle cleanup
│   │   ├── render.py          # PNG & PDF rendering
│   │   └── export_pack.py     # ZIP packaging
│   ├── tests/
│   │   ├── test_color.py
│   │   ├── test_dither.py
│   │   └── test_pipeline.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── Makefile
│   └── samples/
│       └── (place test images here)
├── frontend/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   │   └── preview_response.dart
│   │   ├── services/
│   │   │   └── api.dart
│   │   └── screens/
│   │       ├── upload_screen.dart
│   │       ├── crop_screen.dart
│   │       ├── preview_screen.dart
│   │       └── download_screen.dart
│   ├── web/
│   │   └── index.html
│   ├── pubspec.yaml
│   └── README.md
```

## Image Processing Pipeline

The backend processes images through these stages:

1. **Load & Orient**: Read image, apply EXIF rotation
2. **Crop**: Extract user-selected region
3. **Preprocess**:
   - Optional auto white balance
   - Gamma correction (default 1.0)
   - Bilateral filter (noise reduction)
   - Unsharp mask (edge enhancement 0-0.5)
4. **Resize**: Bicubic to grid dimensions (100×140)
5. **RGB→LAB**: Convert to perceptually uniform color space
6. **Palette Mapping**: Find nearest color using ΔE distance in LAB
7. **Dithering**: Floyd-Steinberg error diffusion
8. **Speckle Cleanup** (optional): 3×3 mode filter
9. **Count Colors**: Tally cells per color (B01-B07)
10. **Render**: Generate PNG preview and PDF pattern

## Color Palettes

### Original (Neutral)
```
B01: #141414 (Black)
B02: #3B4752 (DarkGray)
B03: #6B7C88 (MidGray)
B04: #9FACB7 (LightGray)
B05: #D6DFE6 (Highlight)
B06: #C79A7A (SoftSkin)
B07: #8C5A3C (AccentBrown)
```

### Vintage (Warm Sepia)
```
B01: #1E140E (DeepUmber)
B02: #493326 (DarkCocoa)
B03: #7A563F (Walnut)
B04: #A67A5E (Caramel)
B05: #D1B69A (Sand)
B06: #EFE6D8 (Pearl)
B07: #3C4C59 (ShadowBlue)
```

### Pop Art (Saturated)
```
B01: #101010 (Ink)
B02: #F4D03F (SolarYellow)
B03: #E74C3C (TangyRed)
B04: #3498DB (Azure)
B05: #2ECC71 (SpringGreen)
B06: #9B59B6 (Amethyst)
B07: #F1F1F1 (Highlight)
```

## Troubleshooting

### Image Too Dark
- Increase gamma: `"gamma": 1.2`
- Adjust in preprocessing options

### Face Features Lost
- Increase edge boost: `"edge_boost": 0.4`
- Ensure face is at least 30% of crop area
- Use higher contrast source images

### Busy Background
- Enable background desaturation: `"background_desat": 0.15`
- Manually crop to focus on subject

### Too Many Single-Pixel Speckles
- Enable cleanup: `"speckle_cleanup": true`
- Reduce dither strength: `"dither_strength": 0.7`

### Different Results on Re-run
The pipeline is deterministic. If you get different results:
- Check that crop/rotate parameters are identical
- Verify same palette and options are used
- Ensure no random operations in custom code

## Performance

- **Preview generation**: ~2-4 seconds for 1000×1000 source
- **Final PDF generation**: ~3-5 seconds
- **Grid size**: 100×140 = 14,000 cells
- **Cell size**: 2.1 mm (fits A4 portrait: 210×297 mm)

## Customization

### Add New Palette

Edit `backend/palettes.py`:

```python
CUSTOM_PALETTE = ColorPalette(
    name="custom_v1",
    colors=[
        ("Name1", "#HEXCODE", (r, g, b)),
        # ... exactly 7 colors total
    ],
)

PALETTES["custom"] = CUSTOM_PALETTE
```

Then update frontend to include "custom" in styles list.

### Change Grid Size

Edit `backend/settings.py`:

```python
DEFAULT_GRID_W = 150  # wider grid
DEFAULT_GRID_H = 210  # taller grid
```

Ensure aspect ratio matches your target board dimensions.

### Adjust Dithering

In API request options:
- `"dither": "fs"` - Floyd-Steinberg (default, best quality)
- `"dither": "bayer"` - Ordered Bayer (faster, geometric patterns)
- `"dither": "none"` - No dithering (posterized look)
- `"dither_strength": 0.5` - Lower = less noise, 2.0 = more noise

## License

MIT License - see LICENSE file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run `make format` and `make test`
6. Submit a pull request

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Color space conversion based on standard CIE formulas
- Floyd-Steinberg dithering from Floyd & Steinberg (1976)
- PDF generation powered by ReportLab
- UI built with Flutter framework
