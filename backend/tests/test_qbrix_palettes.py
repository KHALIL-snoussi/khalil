"""Tests for QBRIX palettes and OKLab color space."""

import pytest
from palettes_qbrix import (
    rgb_to_oklab,
    oklab_to_rgb,
    rgb_to_cielab,
    delta_e_2000,
    ORIGINAL_PALETTE,
    WARM_PALETTE,
    POP_PALETTE,
    PALETTES,
)


class TestOKLabConversion:
    """Test OKLab color space conversions."""

    def test_black_conversion(self):
        """Test black (0, 0, 0) conversion."""
        oklab = rgb_to_oklab((0, 0, 0))
        assert oklab[0] == pytest.approx(0, abs=0.01)  # L near 0

    def test_white_conversion(self):
        """Test white (255, 255, 255) conversion."""
        oklab = rgb_to_oklab((255, 255, 255))
        assert oklab[0] == pytest.approx(1.0, abs=0.01)  # L near 1

    def test_roundtrip_conversion(self):
        """Test RGB -> OKLab -> RGB round-trip."""
        test_colors = [
            (0, 0, 0),
            (255, 255, 255),
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (128, 128, 128),
            (199, 154, 122),
        ]

        for original_rgb in test_colors:
            oklab = rgb_to_oklab(original_rgb)
            result_rgb = oklab_to_rgb(oklab)

            # Allow small rounding errors
            for i in range(3):
                assert abs(result_rgb[i] - original_rgb[i]) <= 3

    def test_delta_e_identical(self):
        """Test that identical colors have zero distance."""
        oklab1 = rgb_to_oklab((128, 128, 128))
        oklab2 = rgb_to_oklab((128, 128, 128))
        assert delta_e_2000(oklab1, oklab2) == pytest.approx(0, abs=0.01)

    def test_delta_e_different(self):
        """Test that different colors have positive distance."""
        oklab_black = rgb_to_oklab((0, 0, 0))
        oklab_white = rgb_to_oklab((255, 255, 255))
        distance = delta_e_2000(oklab_black, oklab_white)
        assert distance > 0


class TestPalettes:
    """Test palette definitions."""

    def test_all_palettes_have_7_colors(self):
        """Verify all palettes have exactly 7 colors."""
        for name, palette in PALETTES.items():
            assert len(palette.symbols) == 7
            assert len(palette.rgb_values) == 7
            assert len(palette.hex_values) == 7
            assert len(palette.oklab_values) == 7
            assert len(palette.lab_values) == 7

    def test_symbols_are_1_to_7(self):
        """Verify symbols are numbered 1-7."""
        for palette in PALETTES.values():
            assert palette.symbols == [1, 2, 3, 4, 5, 6, 7]

    def test_bag_codes(self):
        """Verify bag codes are B01-B07."""
        palette = ORIGINAL_PALETTE
        expected_codes = ["B01", "B02", "B03", "B04", "B05", "B06", "B07"]
        for i, symbol in enumerate(palette.symbols):
            assert palette.get_bag_code(symbol) == expected_codes[i]

    def test_oklab_precomputed(self):
        """Verify OKLab values are precomputed correctly."""
        for palette in PALETTES.values():
            for i, rgb in enumerate(palette.rgb_values):
                # Recompute and compare
                oklab = rgb_to_oklab(rgb)
                precomputed = palette.oklab_values[i]

                for j in range(3):
                    assert precomputed[j] == pytest.approx(oklab[j], abs=0.001)

    def test_original_palette_colors(self):
        """Verify Original palette has expected colors."""
        palette = ORIGINAL_PALETTE
        assert palette.name == "original_v2"
        assert palette.hex_values[0] == "#141414"  # Black
        assert palette.hex_values[6] == "#8C5A3C"  # AccentBrown

    def test_warm_palette_colors(self):
        """Verify Warm palette has expected colors."""
        palette = WARM_PALETTE
        assert palette.name == "warm_v2"
        assert palette.hex_values[0] == "#1E140E"  # DeepUmber
        assert palette.hex_values[5] == "#EFE6D8"  # Pearl

    def test_pop_palette_colors(self):
        """Verify Pop palette has expected colors."""
        palette = POP_PALETTE
        assert palette.name == "pop_v2"
        assert palette.hex_values[1] == "#F4D03F"  # SolarYellow
        assert palette.hex_values[4] == "#2ECC71"  # SpringGreen
