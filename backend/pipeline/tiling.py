"""Tiling system for QBRIX-style diamond painting patterns.

Divides large grids into 9×13 tiles, grouped into blocks of 12 for PDF pages.
"""

import math
from typing import List, Tuple, Dict
import numpy as np


class TileConfig:
    """Configuration for tile layout."""

    def __init__(
        self,
        grid_w: int,
        grid_h: int,
        tile_w: int = 9,
        tile_h: int = 13,
        group_size: int = 12,
    ):
        """Initialize tile configuration.

        Args:
            grid_w: Total grid width in cells
            grid_h: Total grid height in cells
            tile_w: Tile width in cells (default 9)
            tile_h: Tile height in cells (default 13)
            group_size: Number of tiles per group/block (default 12)
        """
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.group_size = group_size

        # Calculate number of tiles needed
        self.tiles_x = math.ceil(grid_w / tile_w)
        self.tiles_y = math.ceil(grid_h / tile_h)
        self.total_tiles = self.tiles_x * self.tiles_y

        # Calculate tile groups (e.g., 1-12, 13-24, ...)
        self.num_groups = math.ceil(self.total_tiles / group_size)
        self.groups = []
        for i in range(self.num_groups):
            start = i * group_size + 1
            end = min((i + 1) * group_size, self.total_tiles)
            self.groups.append((start, end))

    def get_tile_bounds(self, tile_num: int) -> Tuple[int, int, int, int]:
        """Get pixel bounds for a tile number (1-indexed).

        Args:
            tile_num: Tile number (1 to total_tiles)

        Returns:
            (x, y, w, h) in grid coordinates
        """
        if tile_num < 1 or tile_num > self.total_tiles:
            raise ValueError(f"Tile number {tile_num} out of range")

        # Convert to 0-indexed
        idx = tile_num - 1

        # Calculate tile position
        tile_x = idx % self.tiles_x
        tile_y = idx // self.tiles_x

        # Calculate bounds
        x = tile_x * self.tile_w
        y = tile_y * self.tile_h
        w = min(self.tile_w, self.grid_w - x)
        h = min(self.tile_h, self.grid_h - y)

        return (x, y, w, h)

    def get_tile_group(self, tile_num: int) -> Tuple[int, int]:
        """Get the group range (start, end) for a tile.

        Args:
            tile_num: Tile number (1-indexed)

        Returns:
            (group_start, group_end) tile numbers
        """
        group_idx = (tile_num - 1) // self.group_size
        return self.groups[group_idx]

    def extract_tile_data(
        self, indices: np.ndarray, tile_num: int
    ) -> np.ndarray:
        """Extract symbol data for a specific tile.

        Args:
            indices: Full grid of symbol indices (H, W) with values 1-7
            tile_num: Tile number (1-indexed)

        Returns:
            Tile data (tile_h, tile_w) with symbols 1-7, padded if needed
        """
        x, y, w, h = self.get_tile_bounds(tile_num)

        # Extract tile region
        tile_data = indices[y : y + h, x : x + w]

        # Pad if needed (for edge tiles)
        if h < self.tile_h or w < self.tile_w:
            padded = np.zeros((self.tile_h, self.tile_w), dtype=indices.dtype)
            padded[:h, :w] = tile_data
            return padded

        return tile_data

    def to_dict(self) -> Dict:
        """Convert to dictionary for spec.json."""
        return {
            "cell_w": self.tile_w,
            "cell_h": self.tile_h,
            "tiles_x": self.tiles_x,
            "tiles_y": self.tiles_y,
            "total_tiles": self.total_tiles,
            "group_size": self.group_size,
            "groups": [
                {"range": f"{start}–{end}", "start": start, "end": end}
                for start, end in self.groups
            ],
        }


def create_tile_config(
    grid_w: int, grid_h: int, preset: str = "medium"
) -> TileConfig:
    """Create tile configuration for a grid.

    Args:
        grid_w: Grid width
        grid_h: Grid height
        preset: Size preset (small/medium/large)

    Returns:
        TileConfig instance
    """
    return TileConfig(grid_w=grid_w, grid_h=grid_h, tile_w=9, tile_h=13, group_size=12)
