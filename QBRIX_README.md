## QBRIX Diamond Painting Generator

Professional-grade 7-color diamond painting pattern generator with QBRIX Assembly Instruction style output.

## 🎨 Overview

This implementation generates **30×40 cm** diamond painting patterns with:
- **7 fixed colors** per palette (Original/Warm/Pop)
- **Numeric symbols 1-7** for cell identification
- **QBRIX-style Assembly Instructions** with QR codes
- **Perceptually accurate** color matching using OKLab
- **Quality-first** image processing (speed irrelevant)

### Key Features

✅ **Advanced Color Science**
- OKLab color space for perceptual uniformity
- ΔE2000 nearest-color matching
- Precomputed LAB values for all palettes

✅ **Professional Image Processing**
- Face detection with auto-crop suggestion
- CLAHE adaptive contrast enhancement
- Bilateral and NLM denoising
- Edge-aware unsharp masking
- Background desaturation for portraits

✅ **Multiple Dithering Algorithms**
- Floyd-Steinberg (default, best quality)
- Jarvis-Judice-Ninke (smoother gradients)
- Stucki (good balance)
- Atkinson (sharper, retro look)
- Ordered Bayer 8×8 (fast, geometric)

✅ **QBRIX Assembly Instructions**
- Page 1: Title, big counts line, social/QR strip
- Tile pages: 9×13 grids with row indices
- Grouped in blocks of 12 (1–12, 13–24, etc.)
- Legend with colors, counts, percentages, bags
- QR codes point to per-job assembly URLs

✅ **Quality Metrics**
- ΔE mean/p95/max for color accuracy
- Edge preservation score (Canny IoU)
- Shannon entropy for distribution

## 📐 Grid Specifications

**Canvas:** 30 cm × 40 cm (portrait)

**Grid Presets:**
- **Small:** 80×106 = 8,480 cells (~Easy)
- **Medium:** 96×128 = 12,288 cells (default)
- **Large:** 108×144 = 15,552 cells (~Hard)

**Tiling:** 9×13 cells per tile, grouped in blocks of 12

## 🎨 Palettes

### Original (Neutral)
Grayscale with warm skin tones
```
1: #141414 (Black)
2: #3B4752 (DarkGray)
3: #6B7C88 (MidGray)
4: #9FACB7 (LightGray)
5: #D6DFE6 (Highlight)
6: #C79A7A (SoftSkin)
7: #8C5A3C (AccentBrown)
```

### Warm (Sepia)
Warm browns and tans
```
1: #1E140E (DeepUmber)
2: #493326 (DarkCocoa)
3: #7A563F (Walnut)
4: #A67A5E (Caramel)
5: #D1B69A (Sand)
6: #EFE6D8 (Pearl)
7: #3C4C59 (ShadowBlue)
```

### Pop (Vibrant)
Saturated primary colors
```
1: #101010 (Ink)
2: #F4D03F (SolarYellow)
3: #E74C3C (TangyRed)
4: #3498DB (Azure)
5: #2ECC71 (SpringGreen)
6: #9B59B6 (Amethyst)
7: #F1F1F1 (Highlight)
```

## 🚀 Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run QBRIX server
python app_qbrix.py
# OR: uvicorn app_qbrix:app --reload --port 8000
```

Backend runs at `http://localhost:8000`

### Testing

```bash
# Run tests
pytest backend/tests/test_qbrix_*.py -v

# With coverage
pytest backend/tests/test_qbrix_*.py --cov=backend/pipeline --cov-report=html
```

## 📡 API Usage

### Health Check

```bash
curl http://localhost:8000/health
# {"ok": true}
```

### Generate Previews

```bash
curl -X POST http://localhost:8000/preview \
  -F "image=@photo.jpg" \
  -F 'payload={
    "crop": {"x": 0, "y": 0, "w": 1000, "h": 1333},
    "rotate_deg": 0,
    "grid": {"w": 96, "h": 128},
    "styles": ["original", "warm", "pop"],
    "suggest_face_crop": true,
    "options": {
      "gamma": 1.0,
      "auto_contrast": true,
      "clahe_clip": 2.0,
      "denoise": "bilateral",
      "denoise_strength": 1.0,
      "dither": "floyd-steinberg",
      "dither_strength": 1.0,
      "edge_boost": 0.3,
      "background_desat": 0.15,
      "speckle_cleanup": false
    }
  }'
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "grid": {"w": 96, "h": 128},
  "previews": {
    "original": "data:image/png;base64,...",
    "warm": "data:image/png;base64,...",
    "pop": "data:image/png;base64,..."
  },
  "counts": {
    "original": [1200, 2300, 3100, 2800, 2400, 1500, 700],
    "warm": [...],
    "pop": [...]
  },
  "percents": {
    "original": [9.8, 18.7, 25.2, 22.8, 19.5, 12.2, 5.7],
    ...
  },
  "metrics": {
    "original": {
      "deltaE_mean": 5.2,
      "deltaE_p95": 12.3,
      "deltaE_max": 18.7,
      "edge_score": 0.78,
      "entropy": 2.56
    },
    ...
  },
  "suggested_crop": {"x": 120, "y": 80, "w": 800, "h": 1066}
}
```

### Generate Final Pattern

```bash
curl -X POST http://localhost:8000/final \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "uuid-from-preview",
    "style": "warm",
    "grid": {"w": 96, "h": 128},
    "palette_id": "warm_v2",
    "crop": {"x": 0, "y": 0, "w": 1000, "h": 1333},
    "rotate_deg": 0,
    "options": {
      "gamma": 1.0,
      "dither": "floyd-steinberg"
    },
    "output_profile": {
      "pdf_style": "qbrix_assembly_v2",
      "tiles": {"cell_w": 9, "cell_h": 13, "group_size": 12},
      "brand": {
        "hashtag": "#QBRIX",
        "site_label": "QBRIX.ME",
        "qr_label": "Use your phone to scan the assembly code",
        "url_base": "https://qbrix.me/en/assembly"
      }
    }
  }' \
  --output pattern.zip
```

**ZIP Contents:**
- `pattern.pdf` - QBRIX Assembly Instruction (multi-page)
- `preview.png` - Upscaled preview (10x, nearest-neighbor)
- `counts.csv` - Color counts, percentages, bag codes
- `spec.json` - Full reproducibility data

## 📄 PDF Layout

### Page 1: Assembly Instruction
```
┌─────────────────────────────────┐
│   Assembly Instruction          │
│                                 │
│  1047  2481  1603  1293  ...   │  ← Big counts line
│                                 │
│  Share your result on social   │
│  #QBRIX QBRIX.ME               │
│                                 │
│  Use your phone to scan...     │
│  [QR CODE]                     │
│  https://qbrix.me/en/...       │
└─────────────────────────────────┘
```

### Tile Pages (9×13 grid)
```
Tiles 1–12                        ← Group header

Tile 1                            ← Tile number

  1  2  3  4  5  6  7  8  9       ← Column grid
1 │5│3│2│1│4│6│7│2│3│            ← Row 1 with index
2 │2│4│5│3│1│2│4│5│6│
...
13│1│3│5│7│2│4│6│1│3│

https://qbrix.me/en               ← Footer
```

### Legend Page
```
Symbol | Bag Code | Hex     | Count | Percent | Swatch
───────┼──────────┼─────────┼───────┼─────────┼────────
  1    │  B01     │ #1E140E │ 1,047 │  8.5%   │ [█████]
  2    │  B02     │ #493326 │ 2,481 │ 20.2%   │ [█████]
 ...
TOTAL  │          │         │12,288 │ 100.0%  │

Bag capacity: 200 drills/bag
Total bags needed: 78
```

## 🎯 Processing Pipeline

1. **Load & Orient** - EXIF rotation handling
2. **Crop & Rotate** - User-specified or face-centered
3. **Preprocess**
   - Auto-contrast (CLAHE on LAB L*)
   - Gamma correction
   - Bilateral or NLM denoising
   - Background desaturation (skin detection)
   - Edge enhancement (unsharp mask)
4. **Resize** - Bicubic to grid dimensions
5. **Dither** - Error diffusion or ordered
6. **Quantize** - Nearest color in OKLab (ΔE)
7. **Post-process** - Optional speckle cleanup
8. **Metrics** - ΔE, edge score, entropy
9. **Render** - PDF with QR + legend + tiles

## 📊 Quality Metrics

**ΔE (Color Accuracy)**
- `deltaE_mean < 8`: Excellent
- `8-15`: Good
- `> 15`: Noticeable artifacts

**Edge Score (Detail Preservation)**
- `> 0.7`: Excellent edge retention
- `0.5-0.7`: Good
- `< 0.5`: Significant detail loss

**Entropy (Distribution)**
- `> 2.5`: Well-distributed colors
- `1.5-2.5`: Reasonable
- `< 1.5`: Limited color usage

## 🔧 Customization

### Change Grid Size

```python
# In request
"grid": {"w": 108, "h": 144}  # Large preset
```

### Adjust Processing

```python
"options": {
  "gamma": 1.2,              # Brighten (+)
  "clahe_clip": 3.0,         # More contrast
  "denoise": "nlm",          # Better quality
  "denoise_strength": 1.5,   # Stronger
  "dither": "jjn",           # Smoother gradients
  "edge_boost": 0.4,         # Sharper
  "background_desat": 0.2    # More desat
}
```

### Custom Branding

```python
"output_profile": {
  "brand": {
    "hashtag": "#MYCOMPANY",
    "site_label": "MYSITE.COM",
    "url_base": "https://mysite.com/pattern"
  }
}
```

## 🐛 Troubleshooting

### Face Lost / Too Dark
- Increase `gamma` to 1.2-1.5
- Increase `edge_boost` to 0.4
- Ensure face fills 65-80% of crop
- Use `suggest_face_crop: true`

### Too Much Noise
- Increase `denoise_strength` to 1.5
- Switch to `denoise: "nlm"`
- Enable `speckle_cleanup: true`

### Busy Background
- Increase `background_desat` to 0.2-0.25
- Manually crop tighter
- Use darker background colors

### Banding in Gradients
- Switch to `dither: "jjn"` or `"stucki"`
- Increase `dither_strength` to 1.0
- Ensure `auto_contrast: true`

## 📈 Performance

- Preview generation: ~3-5 seconds (96×128 grid)
- Final PDF generation: ~5-8 seconds
- No optimization (quality-first, speed irrelevant)

## 🧪 Testing

```bash
# Run all QBRIX tests
pytest backend/tests/test_qbrix_*.py -v

# Test specific module
pytest backend/tests/test_qbrix_palettes.py -v
pytest backend/tests/test_qbrix_tiling.py -v
pytest backend/tests/test_qbrix_integration.py -v

# With coverage report
pytest backend/tests/test_qbrix_*.py --cov=backend --cov-report=html
open htmlcov/index.html
```

## 📦 Dependencies

**Core:**
- FastAPI 0.109+
- Pillow 10.2+
- NumPy 1.26+
- ReportLab 4.0+

**Advanced:**
- OpenCV 4.9+ (face detection, CLAHE)
- SciPy 1.11+ (filters, metrics)
- qrcode 7.4+ (QR generation)
- scikit-image 0.22+ (metrics)

## 🔒 Security Notes

- No authentication (local use only)
- Max upload: 15 MB
- Temporary files cleaned after job
- CORS enabled for development

## 📝 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- OKLab color space: Björn Ottosson
- QBRIX Assembly Instruction format
- OpenCV Haar cascades
- ReportLab PDF library

---

**Generated with QBRIX Diamond Painting Generator v2.0**
