"""Pydantic schemas for API request and response validation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CropRect(BaseModel):
    """Rectangle for cropping in source pixel coordinates."""

    x: int = Field(..., ge=0, description="Top-left X coordinate")
    y: int = Field(..., ge=0, description="Top-left Y coordinate")
    w: int = Field(..., gt=0, description="Width in pixels")
    h: int = Field(..., gt=0, description="Height in pixels")


class GridSize(BaseModel):
    """Grid dimensions for the pattern."""

    w: int = Field(100, ge=10, le=200, description="Grid width in cells")
    h: int = Field(140, ge=10, le=300, description="Grid height in cells")


class ProcessingOptions(BaseModel):
    """Image processing options."""

    gamma: float = Field(1.0, ge=0.5, le=2.0, description="Gamma correction")
    edge_boost: float = Field(0.25, ge=0.0, le=0.5, description="Edge enhancement amount")
    dither: str = Field("fs", pattern="^(fs|bayer|none)$", description="Dithering algorithm")
    dither_strength: float = Field(1.0, ge=0.0, le=2.0, description="Dithering strength")
    auto_face_crop: bool = Field(False, description="Automatically detect and crop face")
    background_desat: float = Field(0.0, ge=0.0, le=0.2, description="Background desaturation")
    speckle_cleanup: bool = Field(False, description="Remove single-pixel speckles")


class PreviewPayload(BaseModel):
    """Payload for preview request."""

    crop: CropRect
    rotate_deg: int = Field(0, ge=-360, le=360, description="Rotation angle in degrees")
    grid: GridSize = Field(default_factory=lambda: GridSize(w=100, h=140))
    styles: List[str] = Field(["original", "vintage", "popart"], description="Styles to preview")
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)


class PreviewResponse(BaseModel):
    """Response from preview endpoint."""

    job_id: str
    grid: GridSize
    previews: Dict[str, str] = Field(..., description="Base64 encoded PNG previews")
    counts: Dict[str, List[int]] = Field(..., description="Color counts per style")


class FinalRequest(BaseModel):
    """Request for final pattern generation."""

    job_id: str
    style: str = Field(..., pattern="^(original|vintage|popart)$")
    grid: GridSize
    palette_id: str
    crop: CropRect
    rotate_deg: int = Field(0, ge=-360, le=360)
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)


class HealthResponse(BaseModel):
    """Health check response."""

    ok: bool = True
