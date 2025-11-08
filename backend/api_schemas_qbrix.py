"""Pydantic schemas for QBRIX API request and response validation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CropRect(BaseModel):
    """Rectangle for cropping in source pixel coordinates."""

    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    w: int = Field(..., gt=0)
    h: int = Field(..., gt=0)


class GridSize(BaseModel):
    """Grid dimensions for the pattern."""

    w: int = Field(96, ge=60, le=150, description="Grid width in cells")
    h: int = Field(128, ge=80, le=200, description="Grid height in cells")


class ProcessingOptions(BaseModel):
    """Image processing options."""

    gamma: float = Field(1.0, ge=0.5, le=2.0)
    auto_contrast: bool = Field(True, description="Apply CLAHE")
    clahe_clip: float = Field(2.0, ge=1.0, le=4.0)
    denoise: str = Field("bilateral", pattern="^(bilateral|nlm|none)$")
    denoise_strength: float = Field(1.0, ge=0.0, le=2.0)
    dither: str = Field(
        "floyd-steinberg",
        pattern="^(floyd-steinberg|fs|jarvis-judice-ninke|jjn|stucki|atkinson|bayer|none)$",
    )
    dither_strength: float = Field(1.0, ge=0.0, le=1.0)
    edge_boost: float = Field(0.3, ge=0.0, le=0.5)
    background_desat: float = Field(0.15, ge=0.0, le=0.3)
    speckle_cleanup: bool = Field(False)


class PreviewPayload(BaseModel):
    """Payload for preview request."""

    crop: CropRect
    rotate_deg: int = Field(0, ge=-360, le=360)
    grid: GridSize = Field(default_factory=lambda: GridSize(w=96, h=128))
    styles: List[str] = Field(["original", "warm", "pop"])
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)
    suggest_face_crop: bool = Field(False, description="Auto-suggest face-centered crop")


class QualityMetrics(BaseModel):
    """Quality metrics for a style."""

    deltaE_mean: float
    deltaE_p95: float
    deltaE_max: float
    edge_score: float
    entropy: float


class PreviewResponse(BaseModel):
    """Response from preview endpoint."""

    job_id: str
    grid: GridSize
    previews: Dict[str, str] = Field(..., description="Base64 data URLs")
    counts: Dict[str, List[int]] = Field(..., description="Per-color counts [1..7]")
    percents: Dict[str, List[float]] = Field(..., description="Percentages [1..7]")
    metrics: Dict[str, QualityMetrics]
    suggested_crop: Optional[CropRect] = Field(
        None, description="Auto-suggested face crop"
    )


class BrandConfig(BaseModel):
    """Branding configuration for PDF."""

    hashtag: str = Field("#QBRIX")
    site_label: str = Field("QBRIX.ME")
    qr_label: str = Field("Use your phone to scan the assembly code")
    url_base: str = Field("https://qbrix.me/en/assembly")


class TileConfig(BaseModel):
    """Tile configuration for PDF."""

    cell_w: int = Field(9)
    cell_h: int = Field(13)
    group_size: int = Field(12)


class OutputProfile(BaseModel):
    """Output profile for final generation."""

    pdf_style: str = Field("qbrix_assembly_v2")
    tiles: TileConfig = Field(default_factory=TileConfig)
    brand: BrandConfig = Field(default_factory=BrandConfig)


class FinalRequest(BaseModel):
    """Request for final pattern generation."""

    job_id: str
    style: str = Field(..., pattern="^(original|warm|pop)$")
    grid: GridSize
    palette_id: str
    crop: CropRect
    rotate_deg: int = Field(0)
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)
    output_profile: OutputProfile = Field(default_factory=OutputProfile)


class HealthResponse(BaseModel):
    """Health check response."""

    ok: bool = True
