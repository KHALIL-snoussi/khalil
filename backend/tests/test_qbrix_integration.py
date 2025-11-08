"""Integration tests for QBRIX pipeline."""

import pytest
import numpy as np
from PIL import Image
import tempfile
from pathlib import Path

from palettes_qbrix import ORIGINAL_PALETTE, WARM_PALETTE
from pipeline.dither_advanced import apply_dithering, find_nearest_color_oklab
from pipeline.metrics import compute_all_metrics, compute_entropy
from pipeline.render_qbrix import render_qbrix_pdf


class TestDithering:
    """Test dithering algorithms."""

    @pytest.fixture
    def test_image(self):
        """Create a simple gradient test image."""
        # Create 96×128 gradient
        gradient = np.zeros((128, 96, 3), dtype=np.uint8)
        for x in range(96):
            value = int((x / 96) * 255)
            gradient[:, x] = value
        return gradient

    def test_floyd_steinberg(self, test_image):
        """Test Floyd-Steinberg dithering."""
        palette = ORIGINAL_PALETTE
        indices = apply_dithering(test_image, palette, method="floyd-steinberg")

        assert indices.shape == (128, 96)
        assert indices.min() >= 1
        assert indices.max() <= 7

    def test_all_dither_methods(self, test_image):
        """Test all dithering methods produce valid output."""
        palette = ORIGINAL_PALETTE
        methods = ["fs", "jjn", "stucki", "atkinson", "bayer", "none"]

        for method in methods:
            indices = apply_dithering(test_image, palette, method=method)
            assert indices.shape == (128, 96)
            assert indices.min() >= 1
            assert indices.max() <= 7

    def test_dither_uses_all_colors(self, test_image):
        """Test that dithering uses multiple colors."""
        palette = ORIGINAL_PALETTE
        indices = apply_dithering(test_image, palette, method="fs")
        unique_symbols = np.unique(indices)
        assert len(unique_symbols) >= 3  # Should use at least 3 colors

    def test_nearest_color_matching(self):
        """Test nearest color matching."""
        palette = ORIGINAL_PALETTE

        # Black should map to symbol 1
        symbol = find_nearest_color_oklab((20, 20, 20), palette)
        assert symbol == 1

        # White should map to symbol 5 (Highlight)
        symbol = find_nearest_color_oklab((214, 223, 230), palette)
        assert symbol == 5


class TestMetrics:
    """Test quality metrics."""

    def test_entropy_calculation(self):
        """Test Shannon entropy calculation."""
        # Uniform distribution
        indices_uniform = np.array([[1, 2, 3, 4], [5, 6, 7, 1]], dtype=np.uint8)
        entropy = compute_entropy(indices_uniform, num_colors=7)
        assert entropy > 0

        # Single color (zero entropy)
        indices_single = np.ones((10, 10), dtype=np.uint8)
        entropy_single = compute_entropy(indices_single, num_colors=7)
        # Should be very low (only one color used)
        assert entropy_single < 1.0

    def test_metrics_computation(self):
        """Test complete metrics computation."""
        # Create simple test images
        original = np.random.randint(0, 256, (128, 96, 3), dtype=np.uint8)
        quantized = np.copy(original)

        # Create simple indices
        indices = np.random.randint(1, 8, (128, 96), dtype=np.uint8)

        palette = ORIGINAL_PALETTE
        metrics = compute_all_metrics(original, quantized, indices, palette)

        # Verify all metrics present
        assert "deltaE_mean" in metrics
        assert "deltaE_p95" in metrics
        assert "deltaE_max" in metrics
        assert "edge_score" in metrics
        assert "entropy" in metrics

        # Verify reasonable values
        assert metrics["deltaE_mean"] >= 0
        assert metrics["edge_score"] >= 0
        assert metrics["edge_score"] <= 1
        assert metrics["entropy"] >= 0


class TestPDFGeneration:
    """Test PDF rendering."""

    def test_pdf_creation(self):
        """Test that PDF is created successfully."""
        # Create simple test indices
        indices = np.random.randint(1, 8, (128, 96), dtype=np.uint8)
        counts = [int(np.sum(indices == i)) for i in range(1, 8)]

        palette = ORIGINAL_PALETTE
        job_id = "test-job-123"

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name

        try:
            render_qbrix_pdf(
                output_path=pdf_path,
                indices=indices,
                palette=palette,
                counts=counts,
                grid_w=96,
                grid_h=128,
                job_id=job_id,
            )

            # Verify PDF was created
            assert Path(pdf_path).exists()
            assert Path(pdf_path).stat().st_size > 1000  # Should be > 1KB

        finally:
            Path(pdf_path).unlink(missing_ok=True)

    def test_counts_sum_to_total(self):
        """Test that color counts sum to total cells."""
        indices = np.random.randint(1, 8, (128, 96), dtype=np.uint8)
        counts = [int(np.sum(indices == i)) for i in range(1, 8)]

        assert sum(counts) == 128 * 96

    def test_percentages_sum_to_100(self):
        """Test that percentages sum to 100%."""
        indices = np.random.randint(1, 8, (128, 96), dtype=np.uint8)
        counts = [int(np.sum(indices == i)) for i in range(1, 8)]

        total = sum(counts)
        percents = [(c / total * 100) for c in counts]

        assert sum(percents) == pytest.approx(100.0, abs=0.1)
