"""QBRIX-style PDF rendering for Assembly Instructions.

Generates PDFs matching the QBRIX Assembly Instruction format with:
- Page 1: Title, counts line, social/QR strip
- Tile pages: 13×9 numeric grids grouped in blocks of 12
- Legend page: Color guide with counts and percentages
"""

import io
import qrcode
from datetime import datetime
from typing import List, Tuple, Dict
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from palettes_qbrix import ColorPalette
from pipeline.tiling import TileConfig


class QBRIXPDFRenderer:
    """Renderer for QBRIX-style Assembly Instruction PDFs."""

    def __init__(
        self,
        output_path: str,
        tile_config: TileConfig,
        palette: ColorPalette,
        indices: np.ndarray,
        counts: List[int],
        job_id: str,
        brand_config: Dict = None,
    ):
        """Initialize renderer.

        Args:
            output_path: Path to save PDF
            tile_config: Tiling configuration
            palette: Color palette
            indices: Grid of symbol indices (1-7)
            counts: Per-color counts [c1, c2, ..., c7]
            job_id: Job UUID for QR code
            brand_config: Branding configuration dict
        """
        self.output_path = output_path
        self.tile_config = tile_config
        self.palette = palette
        self.indices = indices
        self.counts = counts
        self.job_id = job_id

        # Default brand config
        self.brand = brand_config or {
            "hashtag": "#QBRIX",
            "site_label": "QBRIX.ME",
            "qr_label": "Use your phone to scan the assembly code",
            "url_base": "https://qbrix.me/en/assembly",
        }

        self.canvas = canvas.Canvas(output_path, pagesize=A4)
        self.page_width, self.page_height = A4

    def generate(self):
        """Generate complete PDF."""
        # Page 1: Assembly Instruction cover
        self._render_cover_page()
        self.canvas.showPage()

        # Tile pages
        for tile_num in range(1, self.tile_config.total_tiles + 1):
            self._render_tile_page(tile_num)
            self.canvas.showPage()

        # Legend page
        self._render_legend_page()

        self.canvas.save()

    def _render_cover_page(self):
        """Render Page 1: Assembly Instruction cover."""
        c = self.canvas
        pw, ph = self.page_width, self.page_height

        # === TITLE ===
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(pw / 2, ph - 50 * mm, "Assembly Instruction")

        # === COUNTS LINE ===
        # Large numerals separated by spaces, e.g., "1047 2481 1603 1293 1951 787 315"
        counts_str = "  ".join(f"{count:,}" for count in self.counts)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(pw / 2, ph - 75 * mm, counts_str)

        # === SOCIAL/QR STRIP ===
        strip_y = ph - 120 * mm

        # "Share your result on social media"
        c.setFont("Helvetica", 12)
        c.drawCentredString(pw / 2, strip_y, "Share your result on social media")

        # Hashtag and site label
        strip_y -= 20
        hashtag_str = f"{self.brand['hashtag']} {self.brand['site_label']}"
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(pw / 2, strip_y, hashtag_str)

        # QR code section
        strip_y -= 60
        c.setFont("Helvetica", 10)
        c.drawCentredString(pw / 2, strip_y, self.brand["qr_label"])

        # Generate QR code
        qr_url = f"{self.brand['url_base']}/{self.job_id}"
        qr_img = self._generate_qr_code(qr_url)

        # Draw QR code (centered, 40mm x 40mm)
        qr_size = 40 * mm
        qr_x = (pw - qr_size) / 2
        qr_y = strip_y - qr_size - 10
        c.drawImage(qr_img, qr_x, qr_y, qr_size, qr_size)

        # URL below QR code
        c.setFont("Helvetica", 9)
        c.drawCentredString(pw / 2, qr_y - 15, qr_url)

        # === FOOTER ===
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            pw / 2,
            20 * mm,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {self.brand['site_label']}",
        )

    def _render_tile_page(self, tile_num: int):
        """Render a single tile page.

        Args:
            tile_num: Tile number (1-indexed)
        """
        c = self.canvas
        pw, ph = self.page_width, self.page_height

        # === GROUP HEADER ===
        # Check if this is the first tile in a group
        group_start, group_end = self.tile_config.get_tile_group(tile_num)
        if tile_num == group_start:
            # Draw group title (e.g., "1–12", "13–24")
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(pw / 2, ph - 25 * mm, f"{group_start}–{group_end}")

        # === TILE NUMBER ===
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(pw / 2, ph - 40 * mm, f"Tile {tile_num}")

        # === TILE GRID ===
        # Extract tile data
        tile_data = self.tile_config.extract_tile_data(self.indices, tile_num)

        # Grid dimensions
        grid_top = ph - 55 * mm
        cell_size = 10 * mm  # Size of each cell
        index_col_width = 15 * mm  # Width of left index column

        # Draw 13×9 grid with row indices
        c.setFont("Courier-Bold", 10)

        for row in range(13):
            # Left row index (1..13)
            c.drawRightString(
                30 * mm, grid_top - row * cell_size - cell_size / 2, str(row + 1)
            )

            # Draw 9 cells
            for col in range(9):
                if row < tile_data.shape[0] and col < tile_data.shape[1]:
                    symbol = int(tile_data[row, col])
                else:
                    symbol = 0  # Empty padding

                # Cell position
                cell_x = 35 * mm + col * cell_size
                cell_y = grid_top - row * cell_size - cell_size

                # Draw cell border
                c.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.rect(cell_x, cell_y, cell_size, cell_size)

                # Draw symbol (1-7)
                if symbol > 0:
                    c.setFillColor(colors.black)
                    c.drawCentredString(
                        cell_x + cell_size / 2, cell_y + cell_size / 2 - 2, str(symbol)
                    )

        # === FOOTER ===
        c.setFont("Helvetica", 8)
        footer_text = f"{self.brand['url_base'].replace('/assembly', '')}"
        c.drawCentredString(pw / 2, 15 * mm, footer_text)

    def _render_legend_page(self):
        """Render legend page with color guide."""
        c = self.canvas
        pw, ph = self.page_width, self.page_height

        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(pw / 2, ph - 30 * mm, "Color Legend")

        # Calculate percentages
        total_cells = sum(self.counts)
        percents = [
            (count / total_cells * 100) if total_cells > 0 else 0
            for count in self.counts
        ]

        # Table header
        header_y = ph - 50 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(25 * mm, header_y, "Symbol")
        c.drawString(50 * mm, header_y, "Bag Code")
        c.drawString(80 * mm, header_y, "Hex")
        c.drawString(110 * mm, header_y, "Count")
        c.drawString(140 * mm, header_y, "Percent")
        c.drawString(170 * mm, header_y, "Swatch")

        # Divider line
        c.setLineWidth(1)
        c.line(20 * mm, header_y - 3 * mm, 190 * mm, header_y - 3 * mm)

        # Rows
        c.setFont("Helvetica", 10)
        row_height = 12 * mm

        for i, symbol in enumerate(self.palette.symbols):
            y = header_y - (i + 1) * row_height

            # Symbol
            c.drawCentredString(32.5 * mm, y, str(symbol))

            # Bag code
            bag_code = self.palette.get_bag_code(symbol)
            c.drawString(50 * mm, y, bag_code)

            # Hex
            c.drawString(80 * mm, y, self.palette.hex_values[i])

            # Count
            c.drawString(110 * mm, y, f"{self.counts[i]:,}")

            # Percent (1 decimal)
            c.drawString(140 * mm, y, f"{percents[i]:.1f}%")

            # Color swatch
            color_rgb = self.palette.rgb_values[i]
            swatch_color = colors.Color(
                color_rgb[0] / 255.0, color_rgb[1] / 255.0, color_rgb[2] / 255.0
            )
            c.setFillColor(swatch_color)
            c.rect(170 * mm, y - 2 * mm, 15 * mm, 6 * mm, fill=1, stroke=1)
            c.setFillColor(colors.black)

        # Total row
        total_y = header_y - 9 * row_height
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50 * mm, total_y, "TOTAL")
        c.drawString(110 * mm, total_y, f"{total_cells:,}")
        c.drawString(140 * mm, total_y, "100.0%")

        # Bag calculation
        bags_y = total_y - 20 * mm
        c.setFont("Helvetica", 10)
        c.drawString(
            25 * mm,
            bags_y,
            "Bag capacity: 200 drills/bag (bags = ceil(count / 200))",
        )

        total_bags = sum(math.ceil(count / 200) for count in self.counts)
        c.drawString(25 * mm, bags_y - 10, f"Total bags needed: {total_bags}")

    def _generate_qr_code(self, url: str) -> ImageReader:
        """Generate QR code for assembly URL.

        Args:
            url: Full URL to encode

        Returns:
            ImageReader for ReportLab
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to ImageReader
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        return ImageReader(img_buffer)


def render_qbrix_pdf(
    output_path: str,
    indices: np.ndarray,
    palette: ColorPalette,
    counts: List[int],
    grid_w: int,
    grid_h: int,
    job_id: str,
    brand_config: Dict = None,
) -> None:
    """Render QBRIX-style Assembly Instruction PDF.

    Args:
        output_path: Path to save PDF
        indices: Symbol grid (H, W) with values 1-7
        palette: Color palette
        counts: Per-color counts [c1..c7]
        grid_w: Grid width
        grid_h: Grid height
        job_id: Job UUID
        brand_config: Optional brand configuration
    """
    # Create tile configuration
    tile_config = TileConfig(grid_w=grid_w, grid_h=grid_h)

    # Create renderer
    renderer = QBRIXPDFRenderer(
        output_path=output_path,
        tile_config=tile_config,
        palette=palette,
        indices=indices,
        counts=counts,
        job_id=job_id,
        brand_config=brand_config,
    )

    # Generate PDF
    renderer.generate()


import math
