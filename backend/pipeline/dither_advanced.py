"""Advanced dithering algorithms for QBRIX diamond painting.

Implements multiple error diffusion and ordered dithering methods:
- Floyd-Steinberg
- Jarvis-Judice-Ninke (JJN)
- Stucki
- Atkinson
- Ordered (Bayer 8×8)
- Blue noise (simplified)
"""

import numpy as np
from typing import Tuple
from palettes_qbrix import ColorPalette, rgb_to_oklab, delta_e_2000


def find_nearest_color_oklab(pixel_rgb: Tuple[int, int, int], palette: ColorPalette) -> int:
    """Find nearest palette color using OKLab ΔE.

    Args:
        pixel_rgb: RGB pixel (0-255)
        palette: Color palette

    Returns:
        Symbol index (1-7)
    """
    pixel_oklab = rgb_to_oklab(pixel_rgb)
    min_de = float("inf")
    nearest_idx = 1

    for i, palette_oklab in enumerate(palette.oklab_values):
        de = delta_e_2000(pixel_oklab, palette_oklab)
        if de < min_de:
            min_de = de
            nearest_idx = palette.symbols[i]

    return nearest_idx


def floyd_steinberg_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Floyd-Steinberg error diffusion dithering.

    Error distribution:
         X  7/16
    3/16 5/16 1/16

    Args:
        image_rgb: Input RGB image (H, W, 3)
        palette: Color palette
        strength: Error diffusion strength (0-1)

    Returns:
        Symbol indices (H, W) with values 1-7
    """
    height, width = image_rgb.shape[:2]
    working = image_rgb.astype(np.float32).copy()
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            old_pixel = working[y, x].clip(0, 255).astype(np.uint8)
            old_rgb = tuple(old_pixel)

            # Find nearest color
            symbol = find_nearest_color_oklab(old_rgb, palette)
            indices[y, x] = symbol

            # Get palette color
            new_rgb = palette.rgb_values[symbol - 1]
            error = (old_pixel - np.array(new_rgb, dtype=np.float32)) * strength

            # Distribute error
            if x + 1 < width:
                working[y, x + 1] += error * (7.0 / 16.0)
            if y + 1 < height:
                if x > 0:
                    working[y + 1, x - 1] += error * (3.0 / 16.0)
                working[y + 1, x] += error * (5.0 / 16.0)
                if x + 1 < width:
                    working[y + 1, x + 1] += error * (1.0 / 16.0)

    return indices


def jarvis_judice_ninke_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Jarvis-Judice-Ninke error diffusion (48-coefficient).

    Error distribution (divided by 48):
            X  7  5
    3  5  7  5  3
    1  3  5  3  1

    Args:
        image_rgb: Input RGB image
        palette: Color palette
        strength: Error diffusion strength

    Returns:
        Symbol indices (H, W)
    """
    height, width = image_rgb.shape[:2]
    working = image_rgb.astype(np.float32).copy()
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            old_pixel = working[y, x].clip(0, 255).astype(np.uint8)
            symbol = find_nearest_color_oklab(tuple(old_pixel), palette)
            indices[y, x] = symbol

            new_rgb = palette.rgb_values[symbol - 1]
            error = (old_pixel - np.array(new_rgb, dtype=np.float32)) * strength / 48.0

            # Distribute error
            if x + 1 < width:
                working[y, x + 1] += error * 7.0
            if x + 2 < width:
                working[y, x + 2] += error * 5.0

            if y + 1 < height:
                if x >= 2:
                    working[y + 1, x - 2] += error * 3.0
                if x >= 1:
                    working[y + 1, x - 1] += error * 5.0
                working[y + 1, x] += error * 7.0
                if x + 1 < width:
                    working[y + 1, x + 1] += error * 5.0
                if x + 2 < width:
                    working[y + 1, x + 2] += error * 3.0

            if y + 2 < height:
                if x >= 2:
                    working[y + 2, x - 2] += error * 1.0
                if x >= 1:
                    working[y + 2, x - 1] += error * 3.0
                working[y + 2, x] += error * 5.0
                if x + 1 < width:
                    working[y + 2, x + 1] += error * 3.0
                if x + 2 < width:
                    working[y + 2, x + 2] += error * 1.0

    return indices


def stucki_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Stucki error diffusion (42-coefficient).

    Error distribution (divided by 42):
            X  8  4
    2  4  8  4  2
    1  2  4  2  1

    Args:
        image_rgb: Input RGB image
        palette: Color palette
        strength: Error diffusion strength

    Returns:
        Symbol indices (H, W)
    """
    height, width = image_rgb.shape[:2]
    working = image_rgb.astype(np.float32).copy()
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            old_pixel = working[y, x].clip(0, 255).astype(np.uint8)
            symbol = find_nearest_color_oklab(tuple(old_pixel), palette)
            indices[y, x] = symbol

            new_rgb = palette.rgb_values[symbol - 1]
            error = (old_pixel - np.array(new_rgb, dtype=np.float32)) * strength / 42.0

            # Distribute error
            if x + 1 < width:
                working[y, x + 1] += error * 8.0
            if x + 2 < width:
                working[y, x + 2] += error * 4.0

            if y + 1 < height:
                if x >= 2:
                    working[y + 1, x - 2] += error * 2.0
                if x >= 1:
                    working[y + 1, x - 1] += error * 4.0
                working[y + 1, x] += error * 8.0
                if x + 1 < width:
                    working[y + 1, x + 1] += error * 4.0
                if x + 2 < width:
                    working[y + 1, x + 2] += error * 2.0

            if y + 2 < height:
                if x >= 2:
                    working[y + 2, x - 2] += error * 1.0
                if x >= 1:
                    working[y + 2, x - 1] += error * 2.0
                working[y + 2, x] += error * 4.0
                if x + 1 < width:
                    working[y + 2, x + 1] += error * 2.0
                if x + 2 < width:
                    working[y + 2, x + 2] += error * 1.0

    return indices


def atkinson_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Atkinson error diffusion (reduces error by 6/8 = 75%).

    Error distribution (divided by 8):
         X  1  1
    1  1  1
       1

    Args:
        image_rgb: Input RGB image
        palette: Color palette
        strength: Error diffusion strength

    Returns:
        Symbol indices (H, W)
    """
    height, width = image_rgb.shape[:2]
    working = image_rgb.astype(np.float32).copy()
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            old_pixel = working[y, x].clip(0, 255).astype(np.uint8)
            symbol = find_nearest_color_oklab(tuple(old_pixel), palette)
            indices[y, x] = symbol

            new_rgb = palette.rgb_values[symbol - 1]
            error = (old_pixel - np.array(new_rgb, dtype=np.float32)) * strength / 8.0

            # Distribute 6/8 of error
            if x + 1 < width:
                working[y, x + 1] += error
            if x + 2 < width:
                working[y, x + 2] += error

            if y + 1 < height:
                if x >= 1:
                    working[y + 1, x - 1] += error
                working[y + 1, x] += error
                if x + 1 < width:
                    working[y + 1, x + 1] += error

            if y + 2 < height:
                working[y + 2, x] += error

    return indices


def bayer_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Ordered Bayer 8×8 dithering.

    Args:
        image_rgb: Input RGB image
        palette: Color palette
        strength: Dithering strength

    Returns:
        Symbol indices (H, W)
    """
    # Bayer 8×8 matrix
    bayer_matrix = np.array(
        [
            [0, 32, 8, 40, 2, 34, 10, 42],
            [48, 16, 56, 24, 50, 18, 58, 26],
            [12, 44, 4, 36, 14, 46, 6, 38],
            [60, 28, 52, 20, 62, 30, 54, 22],
            [3, 35, 11, 43, 1, 33, 9, 41],
            [51, 19, 59, 27, 49, 17, 57, 25],
            [15, 47, 7, 39, 13, 45, 5, 37],
            [63, 31, 55, 23, 61, 29, 53, 21],
        ],
        dtype=np.float32,
    )
    bayer_matrix = (bayer_matrix / 64.0 - 0.5) * strength * 64.0

    height, width = image_rgb.shape[:2]
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            threshold = bayer_matrix[y % 8, x % 8]
            dithered_pixel = image_rgb[y, x].astype(np.float32) + threshold
            dithered_pixel = dithered_pixel.clip(0, 255).astype(np.uint8)

            symbol = find_nearest_color_oklab(tuple(dithered_pixel), palette)
            indices[y, x] = symbol

    return indices


def no_dither(image_rgb: np.ndarray, palette: ColorPalette) -> np.ndarray:
    """Direct quantization without dithering.

    Args:
        image_rgb: Input RGB image
        palette: Color palette

    Returns:
        Symbol indices (H, W)
    """
    height, width = image_rgb.shape[:2]
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            pixel_rgb = tuple(image_rgb[y, x])
            symbol = find_nearest_color_oklab(pixel_rgb, palette)
            indices[y, x] = symbol

    return indices


def apply_dithering(
    image_rgb: np.ndarray,
    palette: ColorPalette,
    method: str = "floyd-steinberg",
    strength: float = 1.0,
) -> np.ndarray:
    """Apply specified dithering algorithm.

    Args:
        image_rgb: Input RGB image (H, W, 3)
        palette: Color palette
        method: Dithering method name
        strength: Dithering strength (0-1)

    Returns:
        Symbol indices (H, W) with values 1-7
    """
    if method == "floyd-steinberg" or method == "fs":
        return floyd_steinberg_dither(image_rgb, palette, strength)
    elif method == "jarvis-judice-ninke" or method == "jjn":
        return jarvis_judice_ninke_dither(image_rgb, palette, strength)
    elif method == "stucki":
        return stucki_dither(image_rgb, palette, strength)
    elif method == "atkinson":
        return atkinson_dither(image_rgb, palette, strength)
    elif method == "bayer":
        return bayer_dither(image_rgb, palette, strength)
    elif method == "none":
        return no_dither(image_rgb, palette)
    else:
        # Default to Floyd-Steinberg
        return floyd_steinberg_dither(image_rgb, palette, strength)
