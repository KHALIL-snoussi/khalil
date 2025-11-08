"""Color space conversions and nearest-palette color finding.

This module provides functions for converting between RGB and LAB color spaces
and finding the nearest color in a palette using perceptual distance.
"""

from typing import Tuple
import numpy as np
from palettes import ColorPalette, rgb_to_lab, delta_e, LAB


def find_nearest_color(pixel_lab: LAB, palette: ColorPalette) -> int:
    """Find the index of the nearest palette color using LAB distance.

    Args:
        pixel_lab: Input color in LAB space
        palette: Color palette with precomputed LAB values

    Returns:
        Index (0-6) of the nearest color in the palette
    """
    min_distance = float("inf")
    nearest_idx = 0

    for idx, palette_lab in enumerate(palette.lab_values):
        distance = delta_e(pixel_lab, palette_lab)
        if distance < min_distance:
            min_distance = distance
            nearest_idx = idx

    return nearest_idx


def map_image_to_palette(
    image_rgb: np.ndarray, palette: ColorPalette, dithered: bool = False
) -> np.ndarray:
    """Map RGB image to palette indices using LAB color space.

    Args:
        image_rgb: Input image as (H, W, 3) numpy array with RGB values 0-255
        palette: Color palette to map to
        dithered: If True, return RGB error for dithering; if False, return indices

    Returns:
        If dithered=False: (H, W) array of uint8 indices (0-6)
        If dithered=True: (H, W, 3) array of float RGB errors for dithering
    """
    height, width = image_rgb.shape[:2]
    indices = np.zeros((height, width), dtype=np.uint8)

    if dithered:
        errors = np.zeros((height, width, 3), dtype=np.float32)

    for y in range(height):
        for x in range(width):
            pixel_rgb = tuple(image_rgb[y, x])
            pixel_lab = rgb_to_lab(pixel_rgb)
            idx = find_nearest_color(pixel_lab, palette)
            indices[y, x] = idx

            if dithered:
                # Calculate quantization error for dithering
                palette_rgb = palette.rgb_values[idx]
                errors[y, x] = [
                    pixel_rgb[0] - palette_rgb[0],
                    pixel_rgb[1] - palette_rgb[1],
                    pixel_rgb[2] - palette_rgb[2],
                ]

    if dithered:
        return errors
    return indices


def indices_to_rgb(indices: np.ndarray, palette: ColorPalette) -> np.ndarray:
    """Convert palette indices back to RGB image.

    Args:
        indices: (H, W) array of palette indices (0-6)
        palette: Color palette

    Returns:
        (H, W, 3) RGB image with values 0-255
    """
    height, width = indices.shape
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)

    for idx in range(7):
        mask = indices == idx
        rgb_image[mask] = palette.rgb_values[idx]

    return rgb_image


def count_colors(indices: np.ndarray) -> list[int]:
    """Count occurrences of each color index (0-6).

    Args:
        indices: (H, W) array of palette indices

    Returns:
        List of 7 counts, one for each color
    """
    counts = [0] * 7
    unique, counts_arr = np.unique(indices, return_counts=True)

    for idx, count in zip(unique, counts_arr):
        counts[int(idx)] = int(count)

    return counts
