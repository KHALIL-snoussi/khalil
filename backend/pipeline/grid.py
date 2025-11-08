"""Grid operations for diamond painting patterns.

Handles resizing images to grid dimensions and cleaning up speckles.
"""

import numpy as np
from PIL import Image
from scipy import ndimage


def resize_to_grid(img: Image.Image, grid_w: int, grid_h: int) -> Image.Image:
    """Resize image to exact grid dimensions using bicubic interpolation.

    Args:
        img: Input PIL Image
        grid_w: Target grid width in cells
        grid_h: Target grid height in cells

    Returns:
        Resized PIL Image of size (grid_w, grid_h)
    """
    return img.resize((grid_w, grid_h), Image.BICUBIC)


def speckle_cleanup(indices: np.ndarray) -> np.ndarray:
    """Remove single-pixel speckles using 3x3 mode filter.

    Replaces isolated pixels with the most common color in their 3x3 neighborhood.

    Args:
        indices: (H, W) array of palette indices

    Returns:
        Cleaned (H, W) array of palette indices
    """
    # Use mode filter (most common value in neighborhood)
    cleaned = ndimage.generic_filter(
        indices, _mode_filter, size=3, mode="constant", cval=0
    )

    return cleaned.astype(np.uint8)


def _mode_filter(values: np.ndarray) -> int:
    """Helper function to find mode (most common value) in array."""
    unique, counts = np.unique(values, return_counts=True)
    return int(unique[counts.argmax()])


def apply_grid_pattern(
    indices: np.ndarray, speckle_cleanup_enabled: bool = False
) -> np.ndarray:
    """Apply grid-level operations to index map.

    Args:
        indices: (H, W) array of palette indices
        speckle_cleanup_enabled: Whether to remove single-pixel speckles

    Returns:
        Processed (H, W) array of palette indices
    """
    result = indices.copy()

    if speckle_cleanup_enabled:
        result = speckle_cleanup(result)

    return result
