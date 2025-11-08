"""FastAPI application for diamond painting pattern generation.

Provides endpoints for preview generation and final pattern export.
"""

import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image

from api_schemas import (
    FinalRequest,
    HealthResponse,
    PreviewPayload,
    PreviewResponse,
)
from palettes import PALETTES
from pipeline.color import count_colors, indices_to_rgb
from pipeline.dither import apply_dithering
from pipeline.export_pack import create_export_pack
from pipeline.grid import apply_grid_pattern, resize_to_grid
from pipeline.preprocess import (
    crop_to_rect,
    load_and_orient,
    preprocess_image,
    rotate_image,
)
from pipeline.render import render_pattern_pdf, render_preview_png, save_preview_png
from settings import settings

app = FastAPI(
    title="Diamond Painting Generator",
    description="Convert photos to diamond painting patterns",
    version="1.0.0",
)

# Configure CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for job data (for demo; use Redis/DB in production)
job_store: Dict[str, dict] = {}

# Temporary directory for uploaded files
TEMP_DIR = Path(tempfile.gettempdir()) / "diamond_painting"
TEMP_DIR.mkdir(exist_ok=True)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(ok=True)


@app.post("/preview", response_model=PreviewResponse)
async def generate_preview(
    image: UploadFile = File(...), payload: str = Form(...)
):
    """Generate preview images for multiple styles.

    Args:
        image: Uploaded image file
        payload: JSON string with PreviewPayload data

    Returns:
        PreviewResponse with base64 preview images and color counts
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
        # Process image for each style
        previews = {}
        counts = {}

        for style in preview_payload.styles:
            if style not in PALETTES:
                continue

            palette = PALETTES[style]

            # Process image
            indices = _process_image(
                str(temp_path),
                preview_payload.crop,
                preview_payload.rotate_deg,
                preview_payload.grid.w,
                preview_payload.grid.h,
                palette,
                preview_payload.options,
            )

            # Generate preview
            preview_b64 = render_preview_png(indices, palette, target_height=800)
            previews[style] = preview_b64

            # Count colors
            color_counts = count_colors(indices)
            counts[style] = color_counts

        return PreviewResponse(
            job_id=job_id,
            grid=preview_payload.grid,
            previews=previews,
            counts=counts,
        )

    except Exception as e:
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/final")
async def generate_final(request: FinalRequest):
    """Generate final pattern pack (PDF, PNG, CSV, JSON) as ZIP.

    Args:
        request: FinalRequest with job_id and selected style

    Returns:
        ZIP file with pattern pack
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
        indices = _process_image(
            input_path,
            request.crop,
            request.rotate_deg,
            request.grid.w,
            request.grid.h,
            palette,
            request.options,
        )

        # Create output files
        output_dir = TEMP_DIR / request.job_id
        output_dir.mkdir(exist_ok=True)

        pdf_path = output_dir / "pattern.pdf"
        png_path = output_dir / "preview.png"
        zip_path = TEMP_DIR / f"{request.job_id}_final.zip"

        # Render PDF and PNG
        render_pattern_pdf(
            indices,
            palette,
            str(pdf_path),
            request.grid.w,
            request.grid.h,
            request.style,
        )
        save_preview_png(indices, palette, str(png_path))

        # Create specification data
        spec_data = {
            "job_id": request.job_id,
            "style": request.style,
            "palette_id": request.palette_id,
            "grid": {"w": request.grid.w, "h": request.grid.h},
            "crop": request.crop.dict(),
            "rotate_deg": request.rotate_deg,
            "options": request.options.dict(),
            "total_cells": request.grid.w * request.grid.h,
            "colors": [
                {
                    "id": i,
                    "bag_code": palette.get_bag_code(i),
                    "hex": palette.hex_values[i],
                    "name": palette.color_names[i],
                }
                for i in range(7)
            ],
        }

        # Create export pack
        create_export_pack(
            str(pdf_path),
            str(png_path),
            indices,
            palette,
            spec_data,
            str(zip_path),
        )

        # Clean up intermediate files
        shutil.rmtree(output_dir)

        # Return ZIP file
        return FileResponse(
            str(zip_path),
            media_type="application/zip",
            filename=f"diamond_pattern_{request.style}.zip",
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
) -> np.ndarray:
    """Process image through the full pipeline.

    Returns:
        numpy array of palette indices (H, W)
    """
    # 1. Load and orient
    img = load_and_orient(input_path)

    # 2. Rotate if needed
    if rotate_deg != 0:
        img = rotate_image(img, rotate_deg)

    # 3. Crop
    img = crop_to_rect(img, crop.x, crop.y, crop.w, crop.h)

    # 4. Preprocess
    img = preprocess_image(
        img,
        gamma=options.gamma,
        edge_boost=options.edge_boost,
        auto_wb=False,
        background_desat=options.background_desat,
    )

    # 5. Resize to grid
    img = resize_to_grid(img, grid_w, grid_h)

    # 6. Convert to numpy array
    img_array = np.array(img)

    # 7. Apply dithering and palette mapping
    indices = apply_dithering(
        img_array,
        palette,
        method=options.dither,
        strength=options.dither_strength,
    )

    # 8. Optional speckle cleanup
    indices = apply_grid_pattern(indices, options.speckle_cleanup)

    return indices


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
