"""Export final pattern pack as ZIP file.

Creates a ZIP archive containing PDF pattern, PNG preview,
CSV color counts, and JSON specification.
"""

import csv
import json
import zipfile
from pathlib import Path
from typing import Dict, Any

import numpy as np

from palettes import ColorPalette


def create_counts_csv(
    indices: np.ndarray, palette: ColorPalette, output_path: str
) -> None:
    """Create CSV file with color counts.

    Args:
        indices: (H, W) array of palette indices
        palette: Color palette
        output_path: Path to save CSV
    """
    # Calculate counts
    counts = [0] * 7
    unique, counts_arr = np.unique(indices, return_counts=True)
    for idx, count in zip(unique, counts_arr):
        counts[int(idx)] = int(count)

    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["color_id", "count", "bag_code", "hex"])

        for idx in range(7):
            writer.writerow(
                [
                    idx,
                    counts[idx],
                    palette.get_bag_code(idx),
                    palette.hex_values[idx],
                ]
            )


def create_spec_json(spec_data: Dict[str, Any], output_path: str) -> None:
    """Create JSON specification file.

    Args:
        spec_data: Dictionary with specification data
        output_path: Path to save JSON
    """
    with open(output_path, "w") as f:
        json.dump(spec_data, f, indent=2)


def create_export_pack(
    pdf_path: str,
    png_path: str,
    indices: np.ndarray,
    palette: ColorPalette,
    spec_data: Dict[str, Any],
    output_zip: str,
) -> None:
    """Create final export ZIP pack.

    Args:
        pdf_path: Path to pattern PDF
        png_path: Path to preview PNG
        indices: Pattern indices for counts
        palette: Color palette
        spec_data: Specification data
        output_zip: Path to output ZIP file
    """
    # Create temporary directory for intermediate files
    temp_dir = Path(pdf_path).parent

    # Create CSV and JSON
    csv_path = temp_dir / "counts.csv"
    json_path = temp_dir / "spec.json"

    create_counts_csv(indices, palette, str(csv_path))
    create_spec_json(spec_data, str(json_path))

    # Create ZIP file
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pdf_path, "pattern.pdf")
        zf.write(png_path, "preview.png")
        zf.write(csv_path, "counts.csv")
        zf.write(json_path, "spec.json")

    # Clean up temporary files
    csv_path.unlink()
    json_path.unlink()
