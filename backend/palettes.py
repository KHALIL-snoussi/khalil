"""Fixed color palettes for diamond painting patterns.

Each palette contains exactly 7 colors with precomputed LAB values
for efficient nearest-color lookup.
"""

import math
from typing import Dict, List, Tuple

# Type aliases
RGB = Tuple[int, int, int]
LAB = Tuple[float, float, float]


class ColorPalette:
    """A fixed 7-color palette with RGB and LAB representations."""

    def __init__(self, name: str, colors: List[Tuple[str, str, RGB]]):
        """Initialize palette with name and color definitions.

        Args:
            name: Palette identifier
            colors: List of (color_name, hex_code, (r, g, b)) tuples
        """
        self.name = name
        self.colors = colors
        self.rgb_values = [rgb for _, _, rgb in colors]
        self.hex_values = [hex_code for _, hex_code, _ in colors]
        self.color_names = [name for name, _, _ in colors]
        # Precompute LAB values for fast lookup
        self.lab_values = [rgb_to_lab(rgb) for rgb in self.rgb_values]

    def get_bag_code(self, color_id: int) -> str:
        """Get bag code for a color index (B01 through B07)."""
        return f"B{color_id + 1:02d}"


def rgb_to_lab(rgb: RGB) -> LAB:
    """Convert sRGB (0-255) to CIELAB color space.

    Uses D65 illuminant and 2° observer.
    Implementation based on standard conversion formulas.

    Args:
        rgb: Tuple of (r, g, b) in range 0-255

    Returns:
        Tuple of (L*, a*, b*) in CIELAB space
    """
    # Convert sRGB to linear RGB (gamma correction)
    r, g, b = rgb
    r_linear = _srgb_to_linear(r / 255.0)
    g_linear = _srgb_to_linear(g / 255.0)
    b_linear = _srgb_to_linear(b / 255.0)

    # Convert linear RGB to XYZ (D65)
    x = r_linear * 0.4124564 + g_linear * 0.3575761 + b_linear * 0.1804375
    y = r_linear * 0.2126729 + g_linear * 0.7151522 + b_linear * 0.0721750
    z = r_linear * 0.0193339 + g_linear * 0.1191920 + b_linear * 0.9503041

    # Normalize by D65 white point
    x /= 0.95047
    y /= 1.00000
    z /= 1.08883

    # Convert XYZ to LAB
    x = _xyz_to_lab_component(x)
    y = _xyz_to_lab_component(y)
    z = _xyz_to_lab_component(z)

    L = 116.0 * y - 16.0
    a = 500.0 * (x - y)
    b_val = 200.0 * (y - z)

    return (L, a, b_val)


def lab_to_rgb(lab: LAB) -> RGB:
    """Convert CIELAB to sRGB (0-255).

    Args:
        lab: Tuple of (L*, a*, b*) in CIELAB space

    Returns:
        Tuple of (r, g, b) in range 0-255
    """
    L, a, b_val = lab

    # Convert LAB to XYZ
    y = (L + 16.0) / 116.0
    x = a / 500.0 + y
    z = y - b_val / 200.0

    x = _lab_to_xyz_component(x)
    y = _lab_to_xyz_component(y)
    z = _lab_to_xyz_component(z)

    # Denormalize by D65 white point
    x *= 0.95047
    y *= 1.00000
    z *= 1.08883

    # Convert XYZ to linear RGB
    r_linear = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g_linear = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b_linear = x * 0.0556434 + y * -0.2040259 + z * 1.0572252

    # Convert linear RGB to sRGB (gamma correction)
    r = _linear_to_srgb(r_linear)
    g = _linear_to_srgb(g_linear)
    b = _linear_to_srgb(b_linear)

    # Clamp and convert to 0-255
    r = max(0, min(255, int(round(r * 255))))
    g = max(0, min(255, int(round(g * 255))))
    b = max(0, min(255, int(round(b * 255))))

    return (r, g, b)


def _srgb_to_linear(c: float) -> float:
    """Apply sRGB gamma correction to get linear RGB."""
    if c <= 0.04045:
        return c / 12.92
    else:
        return math.pow((c + 0.055) / 1.055, 2.4)


def _linear_to_srgb(c: float) -> float:
    """Apply inverse sRGB gamma correction."""
    if c <= 0.0031308:
        return c * 12.92
    else:
        return 1.055 * math.pow(c, 1.0 / 2.4) - 0.055


def _xyz_to_lab_component(t: float) -> float:
    """Apply XYZ to LAB component transformation."""
    delta = 6.0 / 29.0
    if t > delta ** 3:
        return math.pow(t, 1.0 / 3.0)
    else:
        return t / (3.0 * delta ** 2) + 4.0 / 29.0


def _lab_to_xyz_component(t: float) -> float:
    """Apply LAB to XYZ component transformation."""
    delta = 6.0 / 29.0
    if t > delta:
        return t ** 3
    else:
        return 3.0 * delta ** 2 * (t - 4.0 / 29.0)


def delta_e(lab1: LAB, lab2: LAB) -> float:
    """Calculate Euclidean distance in LAB color space (ΔE).

    Args:
        lab1: First LAB color
        lab2: Second LAB color

    Returns:
        Euclidean distance in LAB space
    """
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL * dL + da * da + db * db)


# Define the three 7-color palettes

ORIGINAL_PALETTE = ColorPalette(
    name="original_v1",
    colors=[
        ("Black", "#141414", (20, 20, 20)),
        ("DarkGray", "#3B4752", (59, 71, 82)),
        ("MidGray", "#6B7C88", (107, 124, 136)),
        ("LightGray", "#9FACB7", (159, 172, 183)),
        ("Highlight", "#D6DFE6", (214, 223, 230)),
        ("SoftSkin", "#C79A7A", (199, 154, 122)),
        ("AccentBrown", "#8C5A3C", (140, 90, 60)),
    ],
)

VINTAGE_PALETTE = ColorPalette(
    name="vintage_v1",
    colors=[
        ("DeepUmber", "#1E140E", (30, 20, 14)),
        ("DarkCocoa", "#493326", (73, 51, 38)),
        ("Walnut", "#7A563F", (122, 86, 63)),
        ("Caramel", "#A67A5E", (166, 122, 94)),
        ("Sand", "#D1B69A", (209, 182, 154)),
        ("Pearl", "#EFE6D8", (239, 230, 216)),
        ("ShadowBlue", "#3C4C59", (60, 76, 89)),
    ],
)

POPART_PALETTE = ColorPalette(
    name="popart_v1",
    colors=[
        ("Ink", "#101010", (16, 16, 16)),
        ("SolarYellow", "#F4D03F", (244, 208, 63)),
        ("TangyRed", "#E74C3C", (231, 76, 60)),
        ("Azure", "#3498DB", (52, 152, 219)),
        ("SpringGreen", "#2ECC71", (46, 204, 113)),
        ("Amethyst", "#9B59B6", (155, 89, 182)),
        ("Highlight", "#F1F1F1", (241, 241, 241)),
    ],
)

# Palette registry
PALETTES: Dict[str, ColorPalette] = {
    "original": ORIGINAL_PALETTE,
    "vintage": VINTAGE_PALETTE,
    "popart": POPART_PALETTE,
}

# Bag codes for all palettes
BAG_CODES = ["B01", "B02", "B03", "B04", "B05", "B06", "B07"]
