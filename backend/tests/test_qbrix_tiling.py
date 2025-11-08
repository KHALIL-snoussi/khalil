"""Tests for QBRIX tiling system."""

import pytest
import numpy as np
from pipeline.tiling import TileConfig


class TestTileConfig:
    """Test tile configuration and layout."""

    def test_default_96x128_grid(self):
        """Test tiling for default 96×128 grid."""
        config = TileConfig(grid_w=96, grid_h=128)

        # 96/9 = 10.67 → 11 tiles wide
        # 128/13 = 9.85 → 10 tiles tall
        assert config.tiles_x == 11
        assert config.tiles_y == 10
        assert config.total_tiles == 110

        # 110 tiles / 12 per group = 10 groups (last group has 2 tiles)
        assert config.num_groups == 10
        assert len(config.groups) == 10

        # Check first and last groups
        assert config.groups[0] == (1, 12)
        assert config.groups[-1] == (109, 110)

    def test_group_ranges(self):
        """Test group range calculations."""
        config = TileConfig(grid_w=96, grid_h=128, group_size=12)

        # Verify groups form continuous ranges
        expected_groups = [
            (1, 12),
            (13, 24),
            (25, 36),
            (37, 48),
            (49, 60),
            (61, 72),
            (73, 84),
            (85, 96),
            (97, 108),
            (109, 110),
        ]

        for i, expected in enumerate(expected_groups):
            assert config.groups[i] == expected

    def test_tile_bounds(self):
        """Test individual tile bounds."""
        config = TileConfig(grid_w=96, grid_h=128)

        # Tile 1 (top-left)
        x, y, w, h = config.get_tile_bounds(1)
        assert (x, y) == (0, 0)
        assert w == 9
        assert h == 13

        # Tile 2 (second from left, top row)
        x, y, w, h = config.get_tile_bounds(2)
        assert (x, y) == (9, 0)

        # Last tile in first row (tile 11)
        x, y, w, h = config.get_tile_bounds(11)
        assert x == 90  # 10 * 9
        assert w == 6  # 96 - 90 = 6 remaining

    def test_extract_tile_data(self):
        """Test extracting tile data from index grid."""
        # Create a simple test grid
        indices = np.arange(1, 97).reshape(12, 8).astype(np.uint8)
        config = TileConfig(grid_w=8, grid_h=12, tile_w=4, tile_h=6)

        # Extract first tile (top-left 4×6)
        tile_data = config.extract_tile_data(indices, tile_num=1)
        assert tile_data.shape == (6, 4)
        assert tile_data[0, 0] == 1  # First element
        assert tile_data[0, 3] == 4  # Fourth element of first row

    def test_get_tile_group(self):
        """Test getting group for a tile."""
        config = TileConfig(grid_w=96, grid_h=128, group_size=12)

        # Tile 1 should be in group 1-12
        assert config.get_tile_group(1) == (1, 12)

        # Tile 13 should be in group 13-24
        assert config.get_tile_group(13) == (13, 24)

        # Tile 110 should be in last group (109-110)
        assert config.get_tile_group(110) == (109, 110)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = TileConfig(grid_w=96, grid_h=128)
        data = config.to_dict()

        assert data["cell_w"] == 9
        assert data["cell_h"] == 13
        assert data["tiles_x"] == 11
        assert data["tiles_y"] == 10
        assert data["total_tiles"] == 110
        assert data["group_size"] == 12
        assert len(data["groups"]) == 10

        # Check group format
        assert data["groups"][0]["range"] == "1–12"
        assert data["groups"][0]["start"] == 1
        assert data["groups"][0]["end"] == 12

    def test_different_grid_sizes(self):
        """Test tiling for different grid presets."""
        # Small: 80×106
        config_small = TileConfig(grid_w=80, grid_h=106)
        assert config_small.tiles_x == 9  # ceil(80/9)
        assert config_small.tiles_y == 9  # ceil(106/13)
        assert config_small.total_tiles == 81

        # Large: 108×144
        config_large = TileConfig(grid_w=108, grid_h=144)
        assert config_large.tiles_x == 12  # ceil(108/9)
        assert config_large.tiles_y == 12  # ceil(144/13)
        assert config_large.total_tiles == 144
