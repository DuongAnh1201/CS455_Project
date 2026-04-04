"""
Shared maze layer: grid generation (recursive backtracker / flood carve),
geometry helpers, and a small Maze wrapper for games and solvers.

Grid convention: maze[row][col] — 1 wall, 0 path. Positions are (row, col).
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import Callable, Iterator, List, Optional, Tuple

# Defaults match the original part2 maze size
DEFAULT_WIDTH = 20
DEFAULT_HEIGHT = 6

# Default game board: 10×10 = 100 unit squares (~100 sq ft if each tile = 1 ft).
SMALL_MAZE_WIDTH = 10
SMALL_MAZE_HEIGHT = 10

# Any custom / “large” maze is clamped to this range (memory and UI sanity).
MAZE_DIM_MIN = 3
MAZE_DIM_MAX = 512


def clamp_maze_dimensions(width: int, height: int) -> Tuple[int, int]:
    """Clamp maze column count and row count for generation."""
    w = max(MAZE_DIM_MIN, min(MAZE_DIM_MAX, int(width)))
    h = max(MAZE_DIM_MIN, min(MAZE_DIM_MAX, int(height)))
    return w, h


Grid = List[List[int]]
Pos = Tuple[int, int]  # (row, col)

DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def in_bounds(width: int, height: int, x: int, y: int) -> bool:
    return 0 <= x < width and 0 <= y < height


def neighbors4(grid: Grid, r: int, c: int) -> Iterator[Pos]:
    h, w = len(grid), len(grid[0])
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0:
            yield (nr, nc)


def find_corner_goal(grid: Grid) -> Pos:
    """Prefer bottom-right open cell; else last open cell scanning from bottom-right."""
    h, w = len(grid), len(grid[0])
    if grid[h - 1][w - 1] == 0:
        return (h - 1, w - 1)
    for r in range(h - 1, -1, -1):
        for c in range(w - 1, -1, -1):
            if grid[r][c] == 0:
                return (r, c)
    return (0, 0)


def _flood_carve(
    maze: Grid,
    width: int,
    height: int,
    x: int,
    y: int,
    rng: random.Random,
    on_step: Optional[Callable[[Grid], None]],
) -> None:
    maze[y][x] = 0
    if on_step:
        on_step(maze)

    order = DIRS[:]
    rng.shuffle(order)
    for dx, dy in order:
        nx, ny = x + dx * 2, y + dy * 2
        if in_bounds(width, height, nx, ny) and maze[ny][nx] == 1:
            maze[y + dy][x + dx] = 0
            if on_step:
                on_step(maze)
            _flood_carve(maze, width, height, nx, ny, rng, on_step)


def generate_maze_grid(
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    *,
    rng: Optional[random.Random] = None,
    on_step: Optional[Callable[[Grid], None]] = None,
) -> Grid:
    """
    Build a perfect maze with the same algorithm as the original part2 flood_maze.
    """
    rng = rng or random.Random()
    maze = [[1 for _ in range(width)] for _ in range(height)]
    _flood_carve(maze, width, height, 0, 0, rng, on_step)
    if on_step:
        on_step(maze)
    return maze


@dataclass
class Maze:
    """Thin wrapper around a grid for games and tooling."""

    grid: Grid

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.rows else 0

    def is_free(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == 0

    def neighbors(self, r: int, c: int) -> Iterator[Pos]:
        yield from neighbors4(self.grid, r, c)


def terminal_maze_animation(
    width: int,
    height: int,
    wall_char: str,
    free_char: str,
    sleep_s: float = 0.15,
) -> Callable[[Grid], None]:
    """Build an on_step callback that clears the terminal and redraws the maze."""
    import os
    import time

    def clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def on_step(maze: Grid) -> None:
        clear()
        for row in maze:
            print("".join(wall_char if cell == 1 else free_char for cell in row))
        time.sleep(sleep_s)

    return on_step


def stdout_wall_char() -> Tuple[str, str]:
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        "\u2588".encode(enc)
        return "\u2588", " "
    except UnicodeEncodeError:
        return "#", " "


__all__ = [
    "DEFAULT_WIDTH",
    "DEFAULT_HEIGHT",
    "SMALL_MAZE_WIDTH",
    "SMALL_MAZE_HEIGHT",
    "MAZE_DIM_MIN",
    "MAZE_DIM_MAX",
    "clamp_maze_dimensions",
    "Grid",
    "Pos",
    "Maze",
    "DIRS",
    "in_bounds",
    "neighbors4",
    "find_corner_goal",
    "generate_maze_grid",
    "terminal_maze_animation",
    "stdout_wall_char",
]
