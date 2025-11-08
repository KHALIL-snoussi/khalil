"""Tests for color conversion and palette operations."""

import pytest
from palettes import rgb_to_lab, lab_to_rgb, delta_e, ORIGINAL_PALETTE
from pipeline.color import find_nearest_color, count_colors
import numpy as np


class TestColorConversion:
    """Test RGB <-> LAB color space conversions."""

    def test_rgb_to_lab_black(self):
        """Test conversion of black (0, 0, 0)."""
        lab = rgb_to_lab((0, 0, 0))
        assert lab[0] == pytest.approx(0, abs=0.1)  # L* should be near 0

    def test_rgb_to_lab_white(self):
        """Test conversion of white (255, 255, 255)."""
        lab = rgb_to_lab((255, 255, 255))
        assert lab[0] == pytest.approx(100, abs=1)  # L* should be near 100

    def test_rgb_to_lab_red(self):
        """Test conversion of pure red."""
        lab = rgb_to_lab((255, 0, 0))
        assert lab[0] > 0  # L* positive
        assert lab[1] > 0  # a* positive (red)
        assert abs(lab[2]) < 50  # b* near neutral

    def test_roundtrip_conversion(self):
        """Test RGB -> LAB -> RGB round-trip accuracy."""
        test_colors = [
            (0, 0, 0),
            (255, 255, 255),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (128, 128, 128),
            (199, 154, 122),  # SoftSkin from palette
        ]

        for original_rgb in test_colors:
            lab = rgb_to_lab(original_rgb)
            result_rgb = lab_to_rgb(lab)

            # Allow small rounding errors
            for i in range(3):
                assert abs(result_rgb[i] - original_rgb[i]) <= 2

    def test_delta_e_identical(self):
        """Test that identical colors have zero distance."""
        lab1 = rgb_to_lab((128, 128, 128))
        lab2 = rgb_to_lab((128, 128, 128))
        assert delta_e(lab1, lab2) == pytest.approx(0, abs=0.01)

    def test_delta_e_different(self):
        """Test that different colors have positive distance."""
        lab_black = rgb_to_lab((0, 0, 0))
        lab_white = rgb_to_lab((255, 255, 255))
        distance = delta_e(lab_black, lab_white)
        assert distance > 0


class TestPaletteLookup:
    """Test nearest color finding in palettes."""

    def test_find_exact_match(self):
        """Test finding exact palette color."""
        palette = ORIGINAL_PALETTE

        # Test black (first color in palette)
        black_lab = rgb_to_lab((20, 20, 20))
        idx = find_nearest_color(black_lab, palette)
        assert idx == 0

    def test_find_nearest_gray(self):
        """Test finding nearest gray shade."""
        palette = ORIGINAL_PALETTE

        # Pure gray should map to one of the gray shades
        gray_lab = rgb_to_lab((100, 100, 100))
        idx = find_nearest_color(gray_lab, palette)
        assert idx in [0, 1, 2, 3, 4]  # One of the grays

    def test_all_palette_colors_unique(self):
        """Verify all palette colors map to themselves."""
        palette = ORIGINAL_PALETTE

        for expected_idx, rgb in enumerate(palette.rgb_values):
            lab = rgb_to_lab(rgb)
            found_idx = find_nearest_color(lab, palette)
            assert found_idx == expected_idx


class TestColorCounting:
    """Test color counting functionality."""

    def test_count_single_color(self):
        """Test counting when only one color is used."""
        indices = np.zeros((10, 10), dtype=np.uint8)
        counts = count_colors(indices)

        assert counts[0] == 100  # All pixels are color 0
        assert sum(counts[1:]) == 0  # No other colors

    def test_count_all_colors(self):
        """Test counting when all colors are used equally."""
        indices = np.array([[i % 7 for i in range(70)] for _ in range(10)], dtype=np.uint8)
        counts = count_colors(indices)

        # Should have 100 pixels of each color
        assert all(c == 100 for c in counts)

    def test_count_total_matches_size(self):
        """Test that total count matches array size."""
        indices = np.random.randint(0, 7, size=(100, 140), dtype=np.uint8)
        counts = count_colors(indices)

        assert sum(counts) == 100 * 140
