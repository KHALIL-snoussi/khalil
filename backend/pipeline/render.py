"""Rendering functions for preview PNG and final PDF pattern.

Generates visual outputs from the indexed grid pattern.
"""

import base64
import io
from datetime import datetime
from typing import Tuple

import numpy as np
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from palettes import ColorPalette


def render_preview_png(
    indices: np.ndarray, palette: ColorPalette, target_height: int = 800
) -> str:
    """Render preview PNG as base64 data URL.

    Args:
        indices: (H, W) array of palette indices
        palette: Color palette
        target_height: Target height in pixels for preview

    Returns:
        Base64 data URL string (data:image/png;base64,...)
    """
    height, width = indices.shape

    # Convert indices to RGB
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    for idx in range(7):
        mask = indices == idx
        rgb_image[mask] = palette.rgb_values[idx]

    # Create PIL Image
    img = Image.fromarray(rgb_image)

    # Scale up for preview (maintain aspect ratio)
    scale = target_height / height
    new_width = int(width * scale)
    new_height = target_height

    # Use NEAREST to show mosaic effect
    img_scaled = img.resize((new_width, new_height), Image.NEAREST)

    # Convert to base64
    buffer = io.BytesIO()
    img_scaled.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return f"data:image/png;base64,{img_base64}"


def render_pattern_pdf(
    indices: np.ndarray,
    palette: ColorPalette,
    output_path: str,
    grid_w: int,
    grid_h: int,
    style_name: str,
) -> None:
    """Render final pattern as PDF with grid and legend.

    Args:
        indices: (H, W) array of palette indices
        palette: Color palette
        output_path: Path to save PDF
        grid_w: Grid width in cells
        grid_h: Grid height in cells
        style_name: Style name for footer
    """
    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4

    # Page 1: Pattern grid
    _render_pattern_page(c, indices, palette, grid_w, grid_h, style_name)
    c.showPage()

    # Page 2: Legend
    _render_legend_page(c, palette, indices)

    c.save()


def _render_pattern_page(
    c: canvas.Canvas,
    indices: np.ndarray,
    palette: ColorPalette,
    grid_w: int,
    grid_h: int,
    style_name: str,
) -> None:
    """Render the pattern grid on a PDF page."""
    page_width, page_height = A4

    # Calculate cell size to fit on page with margins
    margin = 10 * mm
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin - 15 * mm  # Space for footer

    cell_size = min(available_width / grid_w, available_height / grid_h)

    # Center the grid
    grid_width = cell_size * grid_w
    grid_height = cell_size * grid_h
    offset_x = (page_width - grid_width) / 2
    offset_y = (page_height - grid_height) / 2 + 10 * mm  # Shift up for footer

    # Draw cells
    for y in range(grid_h):
        for x in range(grid_w):
            idx = indices[y, x]
            color_rgb = palette.rgb_values[idx]

            # Convert RGB to reportlab color (0-1 range)
            color = colors.Color(
                color_rgb[0] / 255.0, color_rgb[1] / 255.0, color_rgb[2] / 255.0
            )

            # Draw filled rectangle
            c.setFillColor(color)
            c.rect(
                offset_x + x * cell_size,
                offset_y + (grid_h - y - 1) * cell_size,
                cell_size,
                cell_size,
                fill=1,
                stroke=0,
            )

    # Draw grid lines every 10 cells
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)

    for x in range(0, grid_w + 1, 10):
        c.line(
            offset_x + x * cell_size,
            offset_y,
            offset_x + x * cell_size,
            offset_y + grid_height,
        )

    for y in range(0, grid_h + 1, 10):
        c.line(
            offset_x,
            offset_y + y * cell_size,
            offset_x + grid_width,
            offset_y + y * cell_size,
        )

    # Draw outer border
    c.setLineWidth(1.5)
    c.rect(offset_x, offset_y, grid_width, grid_height, fill=0, stroke=1)

    # Footer
    c.setFont("Helvetica", 8)
    footer_text = (
        f"Diamond Painting Pattern | Style: {style_name} | "
        f"Grid: {grid_w}×{grid_h} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    c.drawCentredString(page_width / 2, 10 * mm, footer_text)


def _render_legend_page(
    c: canvas.Canvas, palette: ColorPalette, indices: np.ndarray
) -> None:
    """Render the color legend on a PDF page."""
    page_width, page_height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_width / 2, page_height - 30 * mm, "Color Legend")

    # Calculate counts
    counts = [0] * 7
    unique, counts_arr = np.unique(indices, return_counts=True)
    for idx, count in zip(unique, counts_arr):
        counts[int(idx)] = int(count)

    # Table headers
    start_y = page_height - 50 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30 * mm, start_y, "Color ID")
    c.drawString(60 * mm, start_y, "Bag Code")
    c.drawString(90 * mm, start_y, "Hex")
    c.drawString(120 * mm, start_y, "Count")
    c.drawString(150 * mm, start_y, "Swatch")

    # Draw line under headers
    c.setLineWidth(0.5)
    c.line(25 * mm, start_y - 3 * mm, 185 * mm, start_y - 3 * mm)

    # Table rows
    c.setFont("Helvetica", 10)
    row_height = 10 * mm

    for idx in range(7):
        y = start_y - (idx + 1) * row_height

        # Color ID
        c.drawString(30 * mm, y, str(idx))

        # Bag code
        bag_code = palette.get_bag_code(idx)
        c.drawString(60 * mm, y, bag_code)

        # Hex
        c.drawString(90 * mm, y, palette.hex_values[idx])

        # Count
        c.drawString(120 * mm, y, f"{counts[idx]:,}")

        # Swatch (colored rectangle)
        color_rgb = palette.rgb_values[idx]
        color = colors.Color(
            color_rgb[0] / 255.0, color_rgb[1] / 255.0, color_rgb[2] / 255.0
        )
        c.setFillColor(color)
        c.rect(150 * mm, y - 2 * mm, 20 * mm, 6 * mm, fill=1, stroke=1)
        c.setFillColor(colors.black)

    # Total count
    total = sum(counts)
    y = start_y - 9 * row_height
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30 * mm, y, "TOTAL")
    c.drawString(120 * mm, y, f"{total:,}")


def save_preview_png(
    indices: np.ndarray, palette: ColorPalette, output_path: str
) -> None:
    """Save preview PNG to file.

    Args:
        indices: (H, W) array of palette indices
        palette: Color palette
        output_path: Path to save PNG
    """
    height, width = indices.shape

    # Convert indices to RGB
    rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
    for idx in range(7):
        mask = indices == idx
        rgb_image[mask] = palette.rgb_values[idx]

    # Create and save PIL Image
    img = Image.fromarray(rgb_image)

    # Scale up to reasonable size (10x)
    scale = 10
    img_scaled = img.resize((width * scale, height * scale), Image.NEAREST)
    img_scaled.save(output_path, "PNG")
