"""QBRIX-style Diamond Painting Generator API.

FastAPI application implementing the complete QBRIX workflow with
advanced preprocessing, quality metrics, and Assembly Instruction PDFs.
"""

import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image

from api_schemas_qbrix import (
    FinalRequest,
    HealthResponse,
    PreviewPayload,
    PreviewResponse,
    QualityMetrics,
    CropRect,
)
from palettes_qbrix import PALETTES, GRID_PRESETS
from pipeline.preprocess_advanced import (
    preprocess_qbrix,
    suggest_face_crop,
    detect_faces,
)
from pipeline.dither_advanced import apply_dithering
from pipeline.metrics import compute_all_metrics
from pipeline.render_qbrix import render_qbrix_pdf
from pipeline.tiling import TileConfig
from settings import settings

app = FastAPI(
    title="QBRIX Diamond Painting Generator",
    description="Convert photos to 7-color diamond painting patterns",
    version="2.0.0",
)

# CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job storage
job_store: Dict[str, dict] = {}
TEMP_DIR = Path(tempfile.gettempdir()) / "qbrix_diamond"
TEMP_DIR.mkdir(exist_ok=True)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(ok=True)


@app.post("/preview", response_model=PreviewResponse)
async def generate_preview(
    image: UploadFile = File(...), payload: str = Form(...)
):
    """Generate multi-style previews with quality metrics.

    Args:
        image: Uploaded image file
        payload: JSON string with PreviewPayload data

    Returns:
        PreviewResponse with previews, counts, percentages, and metrics
    """
    # Validate file size
    max_size = settings.MAX_UPLOAD_MB * 1024 * 1024
    contents = await image.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_MB}MB)"
        )

    # Parse payload
    try:
        payload_data = json.loads(payload)
        preview_payload = PreviewPayload(**payload_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

    # Save uploaded file
    job_id = str(uuid.uuid4())
    temp_path = TEMP_DIR / f"{job_id}_input.jpg"

    with open(temp_path, "wb") as f:
        f.write(contents)

    # Store job data
    job_store[job_id] = {
        "input_path": str(temp_path),
        "payload": payload_data,
    }

    try:
        # Load image
        img = Image.open(temp_path)

        # Auto-suggest face crop if requested
        suggested_crop = None
        if preview_payload.suggest_face_crop:
            crop_rect = suggest_face_crop(img, target_aspect=0.75)
            if crop_rect:
                suggested_crop = CropRect(
                    x=crop_rect[0], y=crop_rect[1], w=crop_rect[2], h=crop_rect[3]
                )

        # Process for each style
        previews = {}
        counts = {}
        percents = {}
        metrics = {}

        for style in preview_payload.styles:
            if style not in PALETTES:
                continue

            palette = PALETTES[style]

            # Process image
            result = _process_image(
                str(temp_path),
                preview_payload.crop,
                preview_payload.rotate_deg,
                preview_payload.grid.w,
                preview_payload.grid.h,
                palette,
                preview_payload.options,
            )

            # Generate preview data URL
            preview_b64 = _render_preview_dataurl(
                result["indices"], palette, target_height=800
            )
            previews[style] = preview_b64

            # Counts and percentages
            style_counts = result["counts"]
            counts[style] = style_counts

            total_cells = sum(style_counts)
            style_percents = [
                (c / total_cells * 100) if total_cells > 0 else 0.0
                for c in style_counts
            ]
            percents[style] = [round(p, 1) for p in style_percents]

            # Quality metrics
            metrics[style] = QualityMetrics(**result["metrics"])

        return PreviewResponse(
            job_id=job_id,
            grid=preview_payload.grid,
            previews=previews,
            counts=counts,
            percents=percents,
            metrics=metrics,
            suggested_crop=suggested_crop,
        )

    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/final")
async def generate_final(request: FinalRequest):
    """Generate final QBRIX Assembly Instruction pack.

    Args:
        request: FinalRequest with job_id and style selection

    Returns:
        ZIP file with pattern.pdf, preview.png, counts.csv, spec.json
    """
    # Validate job_id
    if request.job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = job_store[request.job_id]
    input_path = job_data["input_path"]

    if not Path(input_path).exists():
        raise HTTPException(status_code=404, detail="Input file not found")

    # Validate style
    if request.style not in PALETTES:
        raise HTTPException(status_code=400, detail="Invalid style")

    palette = PALETTES[request.style]

    try:
        # Process image
        result = _process_image(
            input_path,
            request.crop,
            request.rotate_deg,
            request.grid.w,
            request.grid.h,
            palette,
            request.options,
        )

        # Create output directory
        output_dir = TEMP_DIR / request.job_id
        output_dir.mkdir(exist_ok=True)

        pdf_path = output_dir / "pattern.pdf"
        png_path = output_dir / "preview.png"
        csv_path = output_dir / "counts.csv"
        json_path = output_dir / "spec.json"
        zip_path = TEMP_DIR / f"{request.job_id}_final.zip"

        # Render PDF
        render_qbrix_pdf(
            output_path=str(pdf_path),
            indices=result["indices"],
            palette=palette,
            counts=result["counts"],
            grid_w=request.grid.w,
            grid_h=request.grid.h,
            job_id=request.job_id,
            brand_config=request.output_profile.brand.dict(),
        )

        # Save preview PNG
        _save_preview_png(result["indices"], palette, str(png_path))

        # Create counts CSV
        _create_counts_csv(result["counts"], palette, request.grid, str(csv_path))

        # Create spec JSON
        _create_spec_json(
            request, result, palette, str(json_path), request.output_profile.brand.url_base
        )

        # Create ZIP
        import zipfile

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(pdf_path, "pattern.pdf")
            zf.write(png_path, "preview.png")
            zf.write(csv_path, "counts.csv")
            zf.write(json_path, "spec.json")

        # Clean up intermediate files
        shutil.rmtree(output_dir)

        # Return ZIP
        return FileResponse(
            str(zip_path),
            media_type="application/zip",
            filename=f"qbrix_pattern_{request.style}.zip",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


def _process_image(
    input_path: str,
    crop,
    rotate_deg: int,
    grid_w: int,
    grid_h: int,
    palette,
    options,
) -> Dict:
    """Process image through complete QBRIX pipeline.

    Returns:
        Dict with indices, counts, metrics, original_img, quantized_img
    """
    # 1. Load and orient
    img = Image.open(input_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Apply EXIF orientation
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except:
        pass

    # 2. Rotate if needed
    if rotate_deg != 0:
        img = img.rotate(-rotate_deg, expand=True, resample=Image.BICUBIC)

    # 3. Crop
    img = img.crop((crop.x, crop.y, crop.x + crop.w, crop.y + crop.h))

    # 4. Preprocess
    img_preprocessed = preprocess_qbrix(
        img,
        gamma=options.gamma,
        auto_contrast=options.auto_contrast,
        clahe_clip=options.clahe_clip,
        denoise_method=options.denoise,
        denoise_strength=options.denoise_strength,
        edge_boost=options.edge_boost,
        background_desat=options.background_desat,
    )

    # 5. Resize to grid
    img_resized = img_preprocessed.resize((grid_w, grid_h), Image.BICUBIC)
    img_array = np.array(img_resized)

    # 6. Apply dithering
    indices = apply_dithering(
        img_array,
        palette,
        method=options.dither,
        strength=options.dither_strength,
    )

    # 7. Speckle cleanup (optional)
    if options.speckle_cleanup:
        from scipy import ndimage

        def mode_filter(values):
            unique, counts = np.unique(values, return_counts=True)
            return int(unique[counts.argmax()])

        indices = ndimage.generic_filter(
            indices, mode_filter, size=3, mode="constant", cval=0
        ).astype(np.uint8)

    # 8. Count colors
    counts = [0] * 7
    for symbol in range(1, 8):
        counts[symbol - 1] = int(np.sum(indices == symbol))

    # 9. Reconstruct quantized image for metrics
    quantized_array = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)
    for symbol in range(1, 8):
        mask = indices == symbol
        quantized_array[mask] = palette.rgb_values[symbol - 1]

    # 10. Compute quality metrics
    metrics = compute_all_metrics(img_array, quantized_array, indices, palette)

    return {
        "indices": indices,
        "counts": counts,
        "metrics": metrics,
        "original_img": img_array,
        "quantized_img": quantized_array,
    }


def _render_preview_dataurl(indices: np.ndarray, palette, target_height: int = 800) -> str:
    """Render preview PNG as base64 data URL."""
    import base64
    import io

    height, width = indices.shape

    # Convert to RGB
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    for symbol in range(1, 8):
        mask = indices == symbol
        rgb_image[mask] = palette.rgb_values[symbol - 1]

    # Scale up
    scale = target_height / height
    new_width = int(width * scale)
    new_height = target_height

    img = Image.fromarray(rgb_image)
    img_scaled = img.resize((new_width, new_height), Image.NEAREST)

    # Convert to data URL
    buffer = io.BytesIO()
    img_scaled.save(buffer, format="PNG")
    buffer.seek(0)
    img_b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return f"data:image/png;base64,{img_b64}"


def _save_preview_png(indices: np.ndarray, palette, output_path: str):
    """Save preview PNG to file."""
    height, width = indices.shape

    # Convert to RGB
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    for symbol in range(1, 8):
        mask = indices == symbol
        rgb_image[mask] = palette.rgb_values[symbol - 1]

    # Scale up 10x
    img = Image.fromarray(rgb_image)
    img_scaled = img.resize((width * 10, height * 10), Image.NEAREST)
    img_scaled.save(output_path, "PNG")


def _create_counts_csv(counts: list, palette, grid, output_path: str):
    """Create counts CSV file."""
    import csv

    total = sum(counts)
    percents = [(c / total * 100) if total > 0 else 0.0 for c in counts]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "bag_code", "hex", "count", "percent", "bags"])

        for i, symbol in enumerate(palette.symbols):
            bag_code = palette.get_bag_code(symbol)
            bags = (counts[i] + 199) // 200  # ceil(count / 200)
            writer.writerow(
                [
                    symbol,
                    bag_code,
                    palette.hex_values[i],
                    counts[i],
                    f"{percents[i]:.1f}%",
                    bags,
                ]
            )


def _create_spec_json(request, result, palette, output_path: str, url_base: str):
    """Create spec.json file."""
    from datetime import datetime

    # Calculate tile configuration
    tile_config = TileConfig(grid_w=request.grid.w, grid_h=request.grid.h)

    spec = {
        "job_id": request.job_id,
        "timestamp": datetime.now().isoformat(),
        "canvas_cm": {"w": 30.0, "h": 40.0},
        "grid": {
            "w": request.grid.w,
            "h": request.grid.h,
            "total_cells": request.grid.w * request.grid.h,
        },
        "tile": tile_config.to_dict(),
        "palette": {
            "id": palette.name,
            "symbols": palette.symbols,
            "colors": [
                {
                    "symbol": sym,
                    "hex": palette.hex_values[i],
                    "rgb": palette.rgb_values[i],
                    "oklab": list(palette.oklab_values[i]),
                }
                for i, sym in enumerate(palette.symbols)
            ],
        },
        "options": request.options.dict(),
        "metrics": result["metrics"],
        "counts": [
            {
                "symbol": palette.symbols[i],
                "count": result["counts"][i],
                "percent": round(
                    (result["counts"][i] / sum(result["counts"]) * 100), 1
                ),
                "bags": (result["counts"][i] + 199) // 200,
                "bag_code": palette.get_bag_code(palette.symbols[i]),
            }
            for i in range(7)
        ],
        "qr_url": f"{url_base}/{request.job_id}",
    }

    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
