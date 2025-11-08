"""Integration tests for the full image processing pipeline."""

import pytest
import numpy as np
from PIL import Image
from pathlib import Path
import tempfile

from palettes import ORIGINAL_PALETTE, VINTAGE_PALETTE, POPART_PALETTE
from pipeline.preprocess import (
    load_and_orient,
    rotate_image,
    crop_to_rect,
    apply_gamma_correction,
    preprocess_image,
)
from pipeline.grid import resize_to_grid, apply_grid_pattern
from pipeline.dither import apply_dithering
from pipeline.render import render_preview_png, render_pattern_pdf, save_preview_png
from pipeline.color import count_colors


class TestFullPipeline:
    """Test complete pipeline integration."""

    @pytest.fixture
    def test_image(self):
        """Create a test image."""
        # Create a 200x280 test image (matches 100:140 aspect ratio)
        img = Image.new("RGB", (200, 280))
        pixels = img.load()

        # Create a simple gradient with some features
        for y in range(280):
            for x in range(200):
                r = int((x / 200) * 255)
                g = int((y / 280) * 255)
                b = 128
                pixels[x, y] = (r, g, b)

        return img

    @pytest.fixture
    def test_image_path(self, test_image):
        """Save test image to temporary file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            test_image.save(f.name, "JPEG")
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    def test_full_pipeline_original(self, test_image_path):
        """Test complete pipeline with original palette."""
        palette = ORIGINAL_PALETTE

        # 1. Load
        img = load_and_orient(test_image_path)
        assert img.size == (200, 280)

        # 2. Preprocess
        img = preprocess_image(img, gamma=1.0, edge_boost=0.25)

        # 3. Resize to grid
        img = resize_to_grid(img, 100, 140)
        assert img.size == (100, 140)

        # 4. Convert to array and dither
        img_array = np.array(img)
        indices = apply_dithering(img_array, palette, method="fs", strength=1.0)

        # Verify output
        assert indices.shape == (140, 100)  # Height x Width
        assert indices.dtype == np.uint8
        assert indices.min() >= 0
        assert indices.max() <= 6

        # 5. Count colors
        counts = count_colors(indices)
        assert len(counts) == 7
        assert sum(counts) == 100 * 140  # Total cells

        # 6. Test rendering
        preview_b64 = render_preview_png(indices, palette, target_height=800)
        assert preview_b64.startswith("data:image/png;base64,")

    def test_pipeline_with_rotation(self, test_image):
        """Test pipeline with rotation."""
        palette = ORIGINAL_PALETTE

        # Rotate 90 degrees
        rotated = rotate_image(test_image, 90)

        # Size should be swapped
        assert rotated.size == (280, 200)

    def test_pipeline_with_crop(self, test_image):
        """Test pipeline with cropping."""
        # Crop center 100x140 region
        cropped = crop_to_rect(test_image, 50, 70, 100, 140)

        assert cropped.size == (100, 140)

    def test_pipeline_all_palettes(self, test_image_path):
        """Test pipeline works with all three palettes."""
        palettes = [ORIGINAL_PALETTE, VINTAGE_PALETTE, POPART_PALETTE]

        for palette in palettes:
            img = load_and_orient(test_image_path)
            img = resize_to_grid(img, 100, 140)
            img_array = np.array(img)
            indices = apply_dithering(img_array, palette, method="fs")

            # Verify valid output
            assert indices.shape == (140, 100)
            assert indices.min() >= 0
            assert indices.max() <= 6

            # Verify counts
            counts = count_colors(indices)
            assert sum(counts) == 14000

    def test_pdf_generation(self, test_image_path):
        """Test PDF pattern generation."""
        palette = ORIGINAL_PALETTE

        # Process image
        img = load_and_orient(test_image_path)
        img = resize_to_grid(img, 100, 140)
        img_array = np.array(img)
        indices = apply_dithering(img_array, palette, method="fs")

        # Generate PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name

        try:
            render_pattern_pdf(
                indices, palette, pdf_path, 100, 140, "original"
            )

            # Verify file was created and has content
            assert Path(pdf_path).exists()
            assert Path(pdf_path).stat().st_size > 0
        finally:
            Path(pdf_path).unlink(missing_ok=True)

    def test_png_export(self, test_image_path):
        """Test PNG preview export."""
        palette = ORIGINAL_PALETTE

        # Process image
        img = load_and_orient(test_image_path)
        img = resize_to_grid(img, 100, 140)
        img_array = np.array(img)
        indices = apply_dithering(img_array, palette, method="fs")

        # Generate PNG
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            png_path = f.name

        try:
            save_preview_png(indices, palette, png_path)

            # Verify file was created
            assert Path(png_path).exists()
            assert Path(png_path).stat().st_size > 0

            # Verify can load as image
            saved_img = Image.open(png_path)
            assert saved_img.size == (1000, 1400)  # 10x scale
        finally:
            Path(png_path).unlink(missing_ok=True)

    def test_speckle_cleanup(self, test_image_path):
        """Test speckle cleanup functionality."""
        palette = ORIGINAL_PALETTE

        # Process image
        img = load_and_orient(test_image_path)
        img = resize_to_grid(img, 100, 140)
        img_array = np.array(img)
        indices = apply_dithering(img_array, palette, method="fs")

        # Apply speckle cleanup
        cleaned = apply_grid_pattern(indices, speckle_cleanup_enabled=True)

        assert cleaned.shape == indices.shape
        assert cleaned.dtype == indices.dtype
