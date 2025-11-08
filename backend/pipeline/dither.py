"""Dithering algorithms for improved color quantization.

Implements Floyd-Steinberg and ordered Bayer dithering to reduce
quantization artifacts when mapping to a limited palette.
"""

import numpy as np
from palettes import ColorPalette, rgb_to_lab
from pipeline.color import find_nearest_color


def floyd_steinberg_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Apply Floyd-Steinberg error diffusion dithering.

    Distributes quantization error to neighboring pixels:
    - Right: 7/16
    - Down-left: 3/16
    - Down: 5/16
    - Down-right: 1/16

    Args:
        image_rgb: Input RGB image (H, W, 3) with values 0-255
        palette: Color palette to quantize to
        strength: Error diffusion strength (0.0 to 2.0)

    Returns:
        (H, W) array of palette indices (0-6)
    """
    height, width = image_rgb.shape[:2]

    # Work with float for error accumulation
    working_image = image_rgb.astype(np.float32).copy()
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            # Get current pixel
            old_pixel = working_image[y, x].clip(0, 255)
            old_rgb = tuple(old_pixel.astype(np.uint8))

            # Find nearest palette color
            pixel_lab = rgb_to_lab(old_rgb)
            idx = find_nearest_color(pixel_lab, palette)
            indices[y, x] = idx

            # Calculate error
            new_rgb = palette.rgb_values[idx]
            error = old_pixel - np.array(new_rgb, dtype=np.float32)
            error *= strength

            # Distribute error to neighbors
            if x + 1 < width:
                working_image[y, x + 1] += error * (7.0 / 16.0)

            if y + 1 < height:
                if x > 0:
                    working_image[y + 1, x - 1] += error * (3.0 / 16.0)
                working_image[y + 1, x] += error * (5.0 / 16.0)
                if x + 1 < width:
                    working_image[y + 1, x + 1] += error * (1.0 / 16.0)

    return indices


def bayer_dither(
    image_rgb: np.ndarray, palette: ColorPalette, strength: float = 1.0
) -> np.ndarray:
    """Apply ordered Bayer 8x8 dithering.

    Uses a threshold map to add controlled noise before quantization.

    Args:
        image_rgb: Input RGB image (H, W, 3) with values 0-255
        palette: Color palette to quantize to
        strength: Dithering strength (0.0 to 2.0)

    Returns:
        (H, W) array of palette indices (0-6)
    """
    # 8x8 Bayer matrix (normalized to -0.5 to 0.5)
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
            # Add Bayer threshold
            threshold = bayer_matrix[y % 8, x % 8]
            dithered_pixel = image_rgb[y, x].astype(np.float32) + threshold
            dithered_pixel = dithered_pixel.clip(0, 255).astype(np.uint8)

            # Find nearest palette color
            pixel_lab = rgb_to_lab(tuple(dithered_pixel))
            idx = find_nearest_color(pixel_lab, palette)
            indices[y, x] = idx

    return indices


def no_dither(image_rgb: np.ndarray, palette: ColorPalette) -> np.ndarray:
    """Direct palette mapping without dithering.

    Args:
        image_rgb: Input RGB image (H, W, 3) with values 0-255
        palette: Color palette to quantize to

    Returns:
        (H, W) array of palette indices (0-6)
    """
    height, width = image_rgb.shape[:2]
    indices = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            pixel_rgb = tuple(image_rgb[y, x])
            pixel_lab = rgb_to_lab(pixel_rgb)
            idx = find_nearest_color(pixel_lab, palette)
            indices[y, x] = idx

    return indices


def apply_dithering(
    image_rgb: np.ndarray,
    palette: ColorPalette,
    method: str = "fs",
    strength: float = 1.0,
) -> np.ndarray:
    """Apply specified dithering algorithm.

    Args:
        image_rgb: Input RGB image (H, W, 3) with values 0-255
        palette: Color palette to quantize to
        method: Dithering method: 'fs', 'bayer', or 'none'
        strength: Dithering strength (0.0 to 2.0)

    Returns:
        (H, W) array of palette indices (0-6)
    """
    if method == "fs":
        return floyd_steinberg_dither(image_rgb, palette, strength)
    elif method == "bayer":
        return bayer_dither(image_rgb, palette, strength)
    else:
        return no_dither(image_rgb, palette)
