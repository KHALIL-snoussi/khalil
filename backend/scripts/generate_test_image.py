#!/usr/bin/env python3
"""Generate a test image for diamond painting pattern testing."""

from PIL import Image, ImageDraw, ImageFont
import os


def generate_test_portrait(output_path: str, width: int = 1000, height: int = 1400):
    """Generate a portrait test image with gradient and features.

    Args:
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create image
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(height):
        gray = int((y / height) * 200 + 55)  # 55 to 255
        draw.rectangle([(0, y), (width, y + 1)], fill=(gray, gray, gray))

    # Add some circular features (face-like)
    # Head circle
    head_center = (width // 2, height // 3)
    head_radius = width // 3
    draw.ellipse(
        [
            (head_center[0] - head_radius, head_center[1] - head_radius),
            (head_center[0] + head_radius, head_center[1] + head_radius),
        ],
        fill=(220, 190, 170),
        outline=(180, 150, 130),
        width=3,
    )

    # Eyes
    eye_y = head_center[1] - head_radius // 4
    eye_offset = head_radius // 3

    # Left eye
    draw.ellipse(
        [
            (head_center[0] - eye_offset - 30, eye_y - 20),
            (head_center[0] - eye_offset + 30, eye_y + 20),
        ],
        fill=(50, 50, 50),
    )

    # Right eye
    draw.ellipse(
        [
            (head_center[0] + eye_offset - 30, eye_y - 20),
            (head_center[0] + eye_offset + 30, eye_y + 20),
        ],
        fill=(50, 50, 50),
    )

    # Mouth
    mouth_y = head_center[1] + head_radius // 3
    draw.arc(
        [
            (head_center[0] - 60, mouth_y - 30),
            (head_center[0] + 60, mouth_y + 30),
        ],
        start=0,
        end=180,
        fill=(100, 50, 50),
        width=5,
    )

    # Add some details (hair)
    for i in range(20):
        x_offset = int((i - 10) * head_radius / 10)
        draw.line(
            [
                (head_center[0] + x_offset, head_center[1] - head_radius),
                (head_center[0] + x_offset, head_center[1] - head_radius - 50),
            ],
            fill=(80, 60, 40),
            width=8,
        )

    # Save image
    img.save(output_path, "JPEG", quality=95)
    print(f"Generated test image: {output_path}")


def generate_landscape(output_path: str, width: int = 1400, height: int = 1000):
    """Generate a landscape test image.

    Args:
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
    """
    # Create image
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Sky gradient (top)
    for y in range(height // 2):
        blue = int(200 - (y / (height // 2)) * 100)
        draw.rectangle([(0, y), (width, y + 1)], fill=(100, 150, blue))

    # Ground gradient (bottom)
    for y in range(height // 2, height):
        green = int(50 + ((y - height // 2) / (height // 2)) * 100)
        draw.rectangle([(0, y), (width, y + 1)], fill=(green, 150, 50))

    # Add sun
    sun_center = (width - 200, 150)
    sun_radius = 80
    draw.ellipse(
        [
            (sun_center[0] - sun_radius, sun_center[1] - sun_radius),
            (sun_center[0] + sun_radius, sun_center[1] + sun_radius),
        ],
        fill=(255, 220, 100),
    )

    # Add some trees
    tree_positions = [200, 400, 600, 800, 1000]
    for x in tree_positions:
        # Trunk
        draw.rectangle(
            [(x - 15, height // 2 + 50), (x + 15, height - 100)],
            fill=(100, 70, 40),
        )

        # Foliage (triangle)
        draw.polygon(
            [
                (x, height // 2 - 50),
                (x - 80, height // 2 + 100),
                (x + 80, height // 2 + 100),
            ],
            fill=(50, 120, 50),
        )

    # Save image
    img.save(output_path, "JPEG", quality=95)
    print(f"Generated test image: {output_path}")


if __name__ == "__main__":
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(os.path.dirname(script_dir), "samples")

    # Create samples directory if it doesn't exist
    os.makedirs(samples_dir, exist_ok=True)

    # Generate test images
    generate_test_portrait(os.path.join(samples_dir, "portrait1.jpg"))
    generate_landscape(os.path.join(samples_dir, "landscape1.jpg"))

    print("\nTest images generated successfully!")
    print(f"Location: {samples_dir}")
