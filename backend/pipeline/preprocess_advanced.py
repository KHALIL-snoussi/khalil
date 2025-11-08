"""Advanced preprocessing for QBRIX-style diamond painting.

Quality-first image processing with face detection, CLAHE, advanced denoising,
and background de-emphasis for optimal 7-color quantization.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List
from pathlib import Path

# OpenCV Haar cascade path (ships with opencv-python)
HAAR_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def detect_faces(image: Image.Image) -> List[Tuple[int, int, int, int]]:
    """Detect faces using OpenCV Haar cascade.

    Args:
        image: PIL Image in RGB

    Returns:
        List of (x, y, w, h) bounding boxes for detected faces
    """
    # Convert PIL to OpenCV
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Load Haar cascade
    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]


def suggest_face_crop(
    image: Image.Image, target_aspect: float = 0.75
) -> Optional[Tuple[int, int, int, int]]:
    """Suggest crop rectangle centered on largest face at 65-80% of frame height.

    Args:
        image: PIL Image
        target_aspect: Target aspect ratio (w/h), default 0.75 for 3:4 portrait

    Returns:
        (x, y, w, h) crop rectangle or None if no face detected
    """
    faces = detect_faces(image)
    if not faces:
        return None

    # Find largest face
    largest_face = max(faces, key=lambda f: f[2] * f[3])
    fx, fy, fw, fh = largest_face

    img_w, img_h = image.size

    # Calculate crop to place face at 70% of frame height
    target_face_height_ratio = 0.70
    crop_h = int(fh / target_face_height_ratio)
    crop_w = int(crop_h * target_aspect)

    # Ensure crop fits in image
    crop_w = min(crop_w, img_w)
    crop_h = min(crop_h, img_h)

    # Center on face
    face_center_x = fx + fw // 2
    face_center_y = fy + fh // 2

    # Position crop
    crop_x = max(0, min(img_w - crop_w, face_center_x - crop_w // 2))
    crop_y = max(0, min(img_h - crop_h, face_center_y - int(crop_h * 0.35)))

    return (crop_x, crop_y, crop_w, crop_h)


def apply_clahe(
    image: Image.Image, clip_limit: float = 2.0, tile_size: int = 8
) -> Image.Image:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) in OKLab L channel.

    Args:
        image: PIL Image
        clip_limit: Contrast limit
        tile_size: Size of grid tiles

    Returns:
        Enhanced PIL Image
    """
    img_array = np.array(image).astype(np.float32) / 255.0

    # Convert to OKLab (simplified approximation using LAB)
    img_bgr = cv2.cvtColor((img_array * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    img_lab[:, :, 0] = clahe.apply(img_lab[:, :, 0])

    # Convert back
    img_bgr = cv2.cvtColor(img_lab, cv2.COLOR_LAB2BGR)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    return Image.fromarray(img_rgb)


def apply_nlm_denoise(
    image: Image.Image, h: float = 10, search_window: int = 21, block_size: int = 7
) -> Image.Image:
    """Apply Non-Local Means denoising.

    Args:
        image: PIL Image
        h: Filter strength (higher = more denoising)
        search_window: Search window size
        block_size: Block size for computing weights

    Returns:
        Denoised PIL Image
    """
    img_array = np.array(image)
    denoised = cv2.fastNlMeansDenoisingColored(
        img_array, None, h, h, block_size, search_window
    )
    return Image.fromarray(denoised)


def apply_bilateral_denoise(
    image: Image.Image, d: int = 9, sigma_color: float = 75, sigma_space: float = 75
) -> Image.Image:
    """Apply bilateral filter for edge-preserving denoising.

    Args:
        image: PIL Image
        d: Diameter of pixel neighborhood
        sigma_color: Filter sigma in color space
        sigma_space: Filter sigma in coordinate space

    Returns:
        Denoised PIL Image
    """
    img_array = np.array(image)
    denoised = cv2.bilateralFilter(img_array, d, sigma_color, sigma_space)
    return Image.fromarray(denoised)


def detect_skin_mask(image: Image.Image) -> np.ndarray:
    """Detect skin regions using YCbCr color space.

    Args:
        image: PIL Image

    Returns:
        Binary mask (0-255) where 255 = skin
    """
    img_array = np.array(image)
    img_ycbcr = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)

    # Skin detection thresholds in YCbCr
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)

    mask = cv2.inRange(img_ycbcr, lower, upper)

    # Morphological operations to clean up mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    return mask


def apply_background_desat(
    image: Image.Image, amount: float = 0.15
) -> Image.Image:
    """Reduce saturation in non-skin regions to save palette range for faces.

    Args:
        image: PIL Image
        amount: Desaturation amount (0-1), 0.15 = reduce sat by 15%

    Returns:
        PIL Image with desaturated background
    """
    if amount <= 0:
        return image

    # Detect skin
    skin_mask = detect_skin_mask(image)

    # Convert to HSV
    img_array = np.array(image)
    img_hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV).astype(np.float32)

    # Reduce saturation in non-skin areas
    bg_mask = (skin_mask == 0).astype(np.float32) / 255.0
    saturation_factor = 1.0 - (amount * bg_mask)

    img_hsv[:, :, 1] *= saturation_factor

    # Convert back
    img_hsv = np.clip(img_hsv, 0, 255).astype(np.uint8)
    img_rgb = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2RGB)

    return Image.fromarray(img_rgb)


def apply_gamma_correction(image: Image.Image, gamma: float) -> Image.Image:
    """Apply gamma correction.

    Args:
        image: PIL Image
        gamma: Gamma value (<1 = brighten, >1 = darken)

    Returns:
        Gamma-corrected PIL Image
    """
    if gamma == 1.0:
        return image

    inv_gamma = 1.0 / gamma
    lut = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(
        np.uint8
    )

    img_array = np.array(image)
    corrected = cv2.LUT(img_array, lut)

    return Image.fromarray(corrected)


def apply_unsharp_mask(
    image: Image.Image, radius: float = 1.5, amount: float = 0.3
) -> Image.Image:
    """Apply unsharp mask for edge enhancement at grid scale.

    Args:
        image: PIL Image
        radius: Gaussian blur radius
        amount: Sharpening strength

    Returns:
        Sharpened PIL Image
    """
    if amount <= 0:
        return image

    img_array = np.array(image).astype(np.float32)

    # Gaussian blur
    blurred = cv2.GaussianBlur(img_array, (0, 0), radius)

    # Unsharp mask
    sharpened = img_array + amount * (img_array - blurred)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)

    return Image.fromarray(sharpened)


def preprocess_qbrix(
    image: Image.Image,
    gamma: float = 1.0,
    auto_contrast: bool = True,
    clahe_clip: float = 2.0,
    denoise_method: str = "bilateral",
    denoise_strength: float = 1.0,
    edge_boost: float = 0.3,
    background_desat: float = 0.15,
) -> Image.Image:
    """Complete QBRIX preprocessing pipeline.

    Args:
        image: Input PIL Image
        gamma: Gamma correction
        auto_contrast: Apply CLAHE
        clahe_clip: CLAHE clip limit
        denoise_method: 'bilateral', 'nlm', or 'none'
        denoise_strength: Denoising strength multiplier
        edge_boost: Edge enhancement amount
        background_desat: Background desaturation amount

    Returns:
        Preprocessed PIL Image
    """
    result = image.copy()

    # 1. Auto contrast (CLAHE)
    if auto_contrast:
        result = apply_clahe(result, clip_limit=clahe_clip)

    # 2. Gamma correction
    if gamma != 1.0:
        result = apply_gamma_correction(result, gamma)

    # 3. Denoising
    if denoise_method == "bilateral":
        d = int(9 * denoise_strength)
        sigma = 75 * denoise_strength
        result = apply_bilateral_denoise(result, d=d, sigma_color=sigma, sigma_space=sigma)
    elif denoise_method == "nlm":
        h = 10 * denoise_strength
        result = apply_nlm_denoise(result, h=h)

    # 4. Background desaturation (before edge boost to preserve skin tones)
    if background_desat > 0:
        result = apply_background_desat(result, amount=background_desat)

    # 5. Edge enhancement
    if edge_boost > 0:
        result = apply_unsharp_mask(result, radius=1.5, amount=edge_boost)

    return result
