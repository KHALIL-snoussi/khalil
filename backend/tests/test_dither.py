"""Tests for dithering algorithms."""

import pytest
import numpy as np
from palettes import ORIGINAL_PALETTE
from pipeline.dither import (
    floyd_steinberg_dither,
    bayer_dither,
    no_dither,
    apply_dithering,
)


class TestDithering:
    """Test dithering algorithms."""

    @pytest.fixture
    def gradient_image(self):
        """Create a simple gradient test image."""
        # 100x100 gray gradient from black to white
        gradient = np.zeros((100, 100, 3), dtype=np.uint8)
        for x in range(100):
            gradient[:, x] = int(x * 2.55)
        return gradient

    @pytest.fixture
    def solid_image(self):
        """Create a solid gray test image."""
        return np.full((50, 50, 3), 128, dtype=np.uint8)

    def test_floyd_steinberg_output_shape(self, gradient_image):
        """Test that Floyd-Steinberg returns correct shape."""
        palette = ORIGINAL_PALETTE
        result = floyd_steinberg_dither(gradient_image, palette)

        assert result.shape == (100, 100)
        assert result.dtype == np.uint8

    def test_floyd_steinberg_values_in_range(self, gradient_image):
        """Test that all indices are in valid range."""
        palette = ORIGINAL_PALETTE
        result = floyd_steinberg_dither(gradient_image, palette)

        assert result.min() >= 0
        assert result.max() <= 6

    def test_bayer_output_shape(self, gradient_image):
        """Test that Bayer dithering returns correct shape."""
        palette = ORIGINAL_PALETTE
        result = bayer_dither(gradient_image, palette)

        assert result.shape == (100, 100)
        assert result.dtype == np.uint8

    def test_bayer_values_in_range(self, gradient_image):
        """Test that Bayer indices are in valid range."""
        palette = ORIGINAL_PALETTE
        result = bayer_dither(gradient_image, palette)

        assert result.min() >= 0
        assert result.max() <= 6

    def test_no_dither_output(self, solid_image):
        """Test direct quantization without dithering."""
        palette = ORIGINAL_PALETTE
        result = no_dither(solid_image, palette)

        assert result.shape == (50, 50)
        # Solid gray should map to single palette color
        assert len(np.unique(result)) <= 2  # Should be mostly uniform

    def test_dithering_uses_multiple_colors(self, gradient_image):
        """Test that dithering produces variation in color usage."""
        palette = ORIGINAL_PALETTE

        # Floyd-Steinberg should use multiple colors for gradient
        fs_result = floyd_steinberg_dither(gradient_image, palette)
        fs_unique = len(np.unique(fs_result))
        assert fs_unique >= 3  # Should use at least 3 different colors

        # Bayer should also use multiple colors
        bayer_result = bayer_dither(gradient_image, palette)
        bayer_unique = len(np.unique(bayer_result))
        assert bayer_unique >= 3

    def test_apply_dithering_methods(self, gradient_image):
        """Test apply_dithering dispatcher function."""
        palette = ORIGINAL_PALETTE

        fs_result = apply_dithering(gradient_image, palette, method="fs")
        assert fs_result.shape == (100, 100)

        bayer_result = apply_dithering(gradient_image, palette, method="bayer")
        assert bayer_result.shape == (100, 100)

        none_result = apply_dithering(gradient_image, palette, method="none")
        assert none_result.shape == (100, 100)

    def test_dither_strength_parameter(self, gradient_image):
        """Test that dither strength affects output."""
        palette = ORIGINAL_PALETTE

        # Low strength
        low_strength = floyd_steinberg_dither(gradient_image, palette, strength=0.3)

        # High strength
        high_strength = floyd_steinberg_dither(gradient_image, palette, strength=1.5)

        # Results should differ
        assert not np.array_equal(low_strength, high_strength)
