"""Image preprocessing functions for diamond painting pattern generation.

Includes operations like rotation, cropping, gamma correction,
noise reduction, and edge enhancement.
"""

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from typing import Tuple


def load_and_orient(image_path: str) -> Image.Image:
    """Load image and apply EXIF orientation.

    Args:
        image_path: Path to image file

    Returns:
        PIL Image with correct orientation
    """
    img = Image.open(image_path)

    # Apply EXIF orientation if present
    try:
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")

    return img


def rotate_image(img: Image.Image, angle_deg: int) -> Image.Image:
    """Rotate image by specified angle.

    Args:
        img: Input PIL Image
        angle_deg: Rotation angle in degrees (counterclockwise)

    Returns:
        Rotated PIL Image
    """
    if angle_deg % 360 == 0:
        return img

    return img.rotate(-angle_deg, expand=True, resample=Image.BICUBIC)


def crop_to_rect(
    img: Image.Image, x: int, y: int, width: int, height: int
) -> Image.Image:
    """Crop image to specified rectangle.

    Args:
        img: Input PIL Image
        x: Top-left X coordinate
        y: Top-left Y coordinate
        width: Crop width
        height: Crop height

    Returns:
        Cropped PIL Image
    """
    return img.crop((x, y, x + width, y + height))


def apply_gamma_correction(img: Image.Image, gamma: float) -> Image.Image:
    """Apply gamma correction to image.

    Args:
        img: Input PIL Image
        gamma: Gamma value (< 1.0 brightens, > 1.0 darkens)

    Returns:
        Gamma-corrected PIL Image
    """
    if gamma == 1.0:
        return img

    # Create lookup table
    inv_gamma = 1.0 / gamma
    lut = [int(((i / 255.0) ** inv_gamma) * 255) for i in range(256)]
    lut = lut * 3  # For RGB

    return img.point(lut)


def bilateral_filter(img: Image.Image, sigma: float = 1.5) -> Image.Image:
    """Apply bilateral filter to reduce noise while preserving edges.

    Uses PIL's SMOOTH filter as an approximation.

    Args:
        img: Input PIL Image
        sigma: Filter strength

    Returns:
        Filtered PIL Image
    """
    if sigma <= 0:
        return img

    # Apply smooth filter (approximation of bilateral)
    # For stronger effect, apply multiple times
    result = img
    iterations = max(1, int(sigma))

    for _ in range(iterations):
        result = result.filter(ImageFilter.SMOOTH_MORE)

    return result


def unsharp_mask(img: Image.Image, amount: float = 0.25) -> Image.Image:
    """Apply unsharp mask for edge enhancement.

    Args:
        img: Input PIL Image
        amount: Sharpening amount (0.0 to 0.5)

    Returns:
        Sharpened PIL Image
    """
    if amount <= 0:
        return img

    # PIL's UnsharpMask filter
    # Scale amount to reasonable radius and percent
    radius = 2.0
    percent = int(amount * 200)  # 0.25 -> 50%
    threshold = 3

    return img.filter(
        ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold)
    )


def auto_white_balance(img: Image.Image) -> Image.Image:
    """Apply simple gray-world white balance.

    Args:
        img: Input PIL Image

    Returns:
        White-balanced PIL Image
    """
    # Convert to numpy for processing
    arr = np.array(img, dtype=np.float32)

    # Calculate mean for each channel
    r_mean = arr[:, :, 0].mean()
    g_mean = arr[:, :, 1].mean()
    b_mean = arr[:, :, 2].mean()

    # Calculate gray (average of means)
    gray = (r_mean + g_mean + b_mean) / 3.0

    # Avoid division by zero
    if r_mean < 1:
        r_mean = 1
    if g_mean < 1:
        g_mean = 1
    if b_mean < 1:
        b_mean = 1

    # Scale each channel
    arr[:, :, 0] *= gray / r_mean
    arr[:, :, 1] *= gray / g_mean
    arr[:, :, 2] *= gray / b_mean

    # Clip and convert back
    arr = np.clip(arr, 0, 255).astype(np.uint8)

    return Image.fromarray(arr)


def desaturate_background(
    img: Image.Image, amount: float = 0.1, threshold: float = 0.5
) -> Image.Image:
    """Reduce saturation in areas with low contrast (backgrounds).

    Args:
        img: Input PIL Image
        amount: Desaturation amount (0.0 to 0.2)
        threshold: Contrast threshold for detecting backgrounds

    Returns:
        PIL Image with desaturated background
    """
    if amount <= 0:
        return img

    # Convert to HSV to work with saturation
    arr_rgb = np.array(img, dtype=np.float32) / 255.0

    # Simple edge detection (Sobel approximation)
    from scipy import ndimage

    gray = (arr_rgb[:, :, 0] + arr_rgb[:, :, 1] + arr_rgb[:, :, 2]) / 3.0
    edges = ndimage.sobel(gray)
    edges = (edges - edges.min()) / (edges.max() - edges.min() + 1e-8)

    # Create mask: low edge areas are background
    bg_mask = edges < threshold

    # Convert to HSV
    from colorsys import rgb_to_hsv, hsv_to_rgb

    arr_out = arr_rgb.copy()

    for y in range(arr_rgb.shape[0]):
        for x in range(arr_rgb.shape[1]):
            if bg_mask[y, x]:
                r, g, b = arr_rgb[y, x]
                h, s, v = rgb_to_hsv(r, g, b)
                s *= 1.0 - amount  # Reduce saturation
                r, g, b = hsv_to_rgb(h, s, v)
                arr_out[y, x] = [r, g, b]

    arr_out = (arr_out * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr_out)


def preprocess_image(
    img: Image.Image,
    gamma: float = 1.0,
    edge_boost: float = 0.25,
    auto_wb: bool = False,
    background_desat: float = 0.0,
) -> Image.Image:
    """Apply full preprocessing pipeline.

    Args:
        img: Input PIL Image
        gamma: Gamma correction value
        edge_boost: Edge enhancement amount
        auto_wb: Apply automatic white balance
        background_desat: Background desaturation amount

    Returns:
        Preprocessed PIL Image
    """
    result = img

    # 1. Optional white balance
    if auto_wb:
        result = auto_white_balance(result)

    # 2. Gamma correction
    result = apply_gamma_correction(result, gamma)

    # 3. Bilateral filter (noise reduction)
    result = bilateral_filter(result, sigma=1.5)

    # 4. Unsharp mask (edge enhancement)
    result = unsharp_mask(result, amount=edge_boost)

    # 5. Optional background desaturation
    if background_desat > 0:
        try:
            result = desaturate_background(result, amount=background_desat)
        except ImportError:
            # Skip if scipy not available
            pass

    return result
