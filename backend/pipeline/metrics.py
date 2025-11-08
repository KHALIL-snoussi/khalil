"""Quality metrics for diamond painting pattern evaluation.

Computes ΔE2000, edge preservation, and entropy metrics to assess
quantization quality.
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, Tuple
from palettes_qbrix import ColorPalette, delta_e_2000, delta_e_cielab, rgb_to_oklab, rgb_to_cielab


def compute_delta_e_metrics(
    original_img: np.ndarray,
    quantized_img: np.ndarray,
    palette: ColorPalette,
    use_oklab: bool = True,
) -> Dict[str, float]:
    """Compute ΔE metrics between original and quantized images.

    Args:
        original_img: Original RGB image (H, W, 3)
        quantized_img: Quantized RGB image (H, W, 3)
        palette: Color palette used
        use_oklab: Use OKLab (True) or CIELAB (False)

    Returns:
        Dictionary with deltaE_mean, deltaE_p95, deltaE_max
    """
    height, width = original_img.shape[:2]
    delta_es = []

    # Sample pixels (compute for every Nth pixel to save time on large images)
    sample_step = max(1, min(height, width) // 100)

    for y in range(0, height, sample_step):
        for x in range(0, width, sample_step):
            orig_rgb = tuple(original_img[y, x])
            quant_rgb = tuple(quantized_img[y, x])

            if use_oklab:
                orig_lab = rgb_to_oklab(orig_rgb)
                quant_lab = rgb_to_oklab(quant_rgb)
                de = delta_e_2000(orig_lab, quant_lab)
            else:
                orig_lab = rgb_to_cielab(orig_rgb)
                quant_lab = rgb_to_cielab(quant_rgb)
                de = delta_e_cielab(orig_lab, quant_lab)

            delta_es.append(de)

    delta_es = np.array(delta_es)

    return {
        "deltaE_mean": float(np.mean(delta_es)),
        "deltaE_p95": float(np.percentile(delta_es, 95)),
        "deltaE_max": float(np.max(delta_es)),
    }


def compute_edge_score(
    original_img: np.ndarray, quantized_img: np.ndarray
) -> float:
    """Compute edge preservation score.

    Measures how well edges are preserved after quantization.

    Args:
        original_img: Original RGB image (H, W, 3)
        quantized_img: Quantized RGB image (H, W, 3)

    Returns:
        Edge preservation score (0-1, higher is better)
    """
    # Convert to grayscale
    orig_gray = cv2.cvtColor(original_img, cv2.COLOR_RGB2GRAY)
    quant_gray = cv2.cvtColor(quantized_img, cv2.COLOR_RGB2GRAY)

    # Detect edges using Canny
    orig_edges = cv2.Canny(orig_gray, 50, 150)
    quant_edges = cv2.Canny(quant_gray, 50, 150)

    # Compute overlap
    orig_edge_pixels = np.sum(orig_edges > 0)
    quant_edge_pixels = np.sum(quant_edges > 0)

    if orig_edge_pixels == 0:
        return 1.0

    # Intersection over union
    intersection = np.sum((orig_edges > 0) & (quant_edges > 0))
    union = np.sum((orig_edges > 0) | (quant_edges > 0))

    if union == 0:
        return 1.0

    iou = intersection / union
    return float(iou)


def compute_entropy(indices: np.ndarray, num_colors: int = 7) -> float:
    """Compute Shannon entropy of color distribution.

    Higher entropy indicates more even color distribution.

    Args:
        indices: Symbol indices (H, W) with values 1-7
        num_colors: Number of colors in palette

    Returns:
        Shannon entropy in bits
    """
    # Count occurrences
    counts = np.bincount(indices.flatten(), minlength=num_colors + 1)[1:]  # Skip 0
    total = counts.sum()

    if total == 0:
        return 0.0

    # Calculate probabilities
    probs = counts / total

    # Shannon entropy
    entropy = -np.sum(probs * np.log2(probs + 1e-10))  # Add epsilon to avoid log(0)

    return float(entropy)


def compute_all_metrics(
    original_img: np.ndarray,
    quantized_img: np.ndarray,
    indices: np.ndarray,
    palette: ColorPalette,
) -> Dict[str, float]:
    """Compute all quality metrics.

    Args:
        original_img: Original RGB image (H, W, 3)
        quantized_img: Quantized RGB image (H, W, 3)
        indices: Symbol indices (H, W)
        palette: Color palette

    Returns:
        Dictionary with all metrics
    """
    metrics = {}

    # ΔE metrics
    delta_metrics = compute_delta_e_metrics(original_img, quantized_img, palette)
    metrics.update(delta_metrics)

    # Edge score
    metrics["edge_score"] = compute_edge_score(original_img, quantized_img)

    # Entropy
    metrics["entropy"] = compute_entropy(indices)

    return metrics
