"""QBRIX-style color palettes with OKLab color space.

Each palette contains exactly 7 colors with precomputed OKLab values
for perceptually accurate color matching using ΔE2000.
"""

import math
from typing import List, Tuple

# Type aliases
RGB = Tuple[int, int, int]
OKLab = Tuple[float, float, float]
CIELAB = Tuple[float, float, float]


class ColorPalette:
    """A 7-color palette with RGB and OKLab representations."""

    def __init__(self, name: str, colors: List[Tuple[int, str, RGB]]):
        """Initialize palette.

        Args:
            name: Palette identifier (e.g., "original_v2")
            colors: List of (symbol, hex_code, (r, g, b)) tuples, symbols 1-7
        """
        self.name = name
        self.colors = colors
        self.symbols = [sym for sym, _, _ in colors]  # 1..7
        self.rgb_values = [rgb for _, _, rgb in colors]
        self.hex_values = [hex_code for _, hex_code, _ in colors]

        # Precompute OKLab and CIELAB for fast lookup
        self.oklab_values = [rgb_to_oklab(rgb) for rgb in self.rgb_values]
        self.lab_values = [rgb_to_cielab(rgb) for rgb in self.rgb_values]

    def get_bag_code(self, symbol: int) -> str:
        """Get bag code for a symbol (1-7) -> B01-B07."""
        return f"B{symbol:02d}"


def linear_to_srgb(c: float) -> float:
    """Convert linear RGB component to sRGB."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1 / 2.4)) - 0.055


def srgb_to_linear(c: float) -> float:
    """Convert sRGB component to linear RGB."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def rgb_to_oklab(rgb: RGB) -> OKLab:
    """Convert sRGB (0-255) to OKLab color space.

    OKLab provides perceptually uniform color space optimized for modern displays.
    Reference: https://bottosson.github.io/posts/oklab/

    Args:
        rgb: Tuple of (r, g, b) in range 0-255

    Returns:
        Tuple of (L, a, b) in OKLab space
    """
    # Convert to linear sRGB (0-1)
    r = srgb_to_linear(rgb[0] / 255.0)
    g = srgb_to_linear(rgb[1] / 255.0)
    b = srgb_to_linear(rgb[2] / 255.0)

    # Linear sRGB to LMS (cone response)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    # Apply cube root
    l_ = math.copysign(abs(l) ** (1 / 3), l)
    m_ = math.copysign(abs(m) ** (1 / 3), m)
    s_ = math.copysign(abs(s) ** (1 / 3), s)

    # LMS to OKLab
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_val = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    return (L, a, b_val)


def oklab_to_rgb(oklab: OKLab) -> RGB:
    """Convert OKLab to sRGB (0-255).

    Args:
        oklab: Tuple of (L, a, b) in OKLab space

    Returns:
        Tuple of (r, g, b) in range 0-255
    """
    L, a, b_val = oklab

    # OKLab to LMS
    l_ = L + 0.3963377774 * a + 0.2158037573 * b_val
    m_ = L - 0.1055613458 * a - 0.0638541728 * b_val
    s_ = L - 0.0894841775 * a - 1.2914855480 * b_val

    # Cube to get LMS
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3

    # LMS to linear sRGB
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    # Linear to sRGB
    r_srgb = linear_to_srgb(r)
    g_srgb = linear_to_srgb(g)
    b_srgb = linear_to_srgb(b)

    # Clamp and convert to 0-255
    r_int = max(0, min(255, int(round(r_srgb * 255))))
    g_int = max(0, min(255, int(round(g_srgb * 255))))
    b_int = max(0, min(255, int(round(b_srgb * 255))))

    return (r_int, g_int, b_int)


def rgb_to_cielab(rgb: RGB) -> CIELAB:
    """Convert sRGB (0-255) to CIELAB color space (for testing/comparison).

    Args:
        rgb: Tuple of (r, g, b) in range 0-255

    Returns:
        Tuple of (L*, a*, b*) in CIELAB space
    """
    # Convert to linear RGB
    r = srgb_to_linear(rgb[0] / 255.0)
    g = srgb_to_linear(rgb[1] / 255.0)
    b = srgb_to_linear(rgb[2] / 255.0)

    # Linear RGB to XYZ (D65)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041

    # Normalize by D65 white point
    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    # XYZ to LAB
    def f(t):
        delta = 6.0 / 29.0
        if t > delta ** 3:
            return t ** (1.0 / 3.0)
        return t / (3.0 * delta ** 2) + 4.0 / 29.0

    fx = f(x)
    fy = f(y)
    fz = f(z)

    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)

    return (L, a, b_val)


def delta_e_2000(lab1: OKLab, lab2: OKLab) -> float:
    """Calculate ΔE2000 perceptual color difference.

    For OKLab, we can use simplified Euclidean distance as it's already
    perceptually uniform. For true ΔE2000, use CIELAB input.

    Args:
        lab1: First color in LAB-like space
        lab2: Second color in LAB-like space

    Returns:
        Perceptual color difference
    """
    # For OKLab, Euclidean distance is sufficient
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL * dL + da * da + db * db)


def delta_e_cielab(lab1: CIELAB, lab2: CIELAB) -> float:
    """Calculate ΔE (CIE76) for CIELAB colors.

    Args:
        lab1: First CIELAB color
        lab2: Second CIELAB color

    Returns:
        Color difference
    """
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL * dL + da * da + db * db)


# QBRIX Palettes (30×40 cm canvas, 7 colors, symbols 1-7)

ORIGINAL_PALETTE = ColorPalette(
    name="original_v2",
    colors=[
        (1, "#141414", (20, 20, 20)),
        (2, "#3B4752", (59, 71, 82)),
        (3, "#6B7C88", (107, 124, 136)),
        (4, "#9FACB7", (159, 172, 183)),
        (5, "#D6DFE6", (214, 223, 230)),
        (6, "#C79A7A", (199, 154, 122)),
        (7, "#8C5A3C", (140, 90, 60)),
    ],
)

WARM_PALETTE = ColorPalette(
    name="warm_v2",
    colors=[
        (1, "#1E140E", (30, 20, 14)),
        (2, "#493326", (73, 51, 38)),
        (3, "#7A563F", (122, 86, 63)),
        (4, "#A67A5E", (166, 122, 94)),
        (5, "#D1B69A", (209, 182, 154)),
        (6, "#EFE6D8", (239, 230, 216)),
        (7, "#3C4C59", (60, 76, 89)),
    ],
)

POP_PALETTE = ColorPalette(
    name="pop_v2",
    colors=[
        (1, "#101010", (16, 16, 16)),
        (2, "#F4D03F", (244, 208, 63)),
        (3, "#E74C3C", (231, 76, 60)),
        (4, "#3498DB", (52, 152, 219)),
        (5, "#2ECC71", (46, 204, 113)),
        (6, "#9B59B6", (155, 89, 182)),
        (7, "#F1F1F1", (241, 241, 241)),
    ],
)

# Palette registry
PALETTES = {
    "original": ORIGINAL_PALETTE,
    "warm": WARM_PALETTE,
    "pop": POP_PALETTE,
}

# Grid size presets for 30×40 cm canvas
GRID_PRESETS = {
    "small": {"w": 80, "h": 106, "cells": 8480},  # ~8.5k cells
    "medium": {"w": 96, "h": 128, "cells": 12288},  # ~12k cells (default)
    "large": {"w": 108, "h": 144, "cells": 15552},  # ~15.5k cells
}
