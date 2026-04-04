"""
Depth-first search on a grid maze. Same interface as BFS / A* / RRT grid solve.
Positions are (row, col); maze[row][col] is 0 path, 1 wall.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from maze_core import Grid, Pos, neighbors4

Path = List[Pos]


def solve(grid: Grid, start: Pos, goal: Pos) -> Optional[Path]:
    """
    Return a path from start to goal, or None. Order of neighbor expansion is fixed
    (down, up, right, left as in maze_core.DIRS) for reproducibility.
    """
    if grid[start[0]][start[1]] != 0 or grid[goal[0]][goal[1]] != 0:
        return None

    stack: List[Pos] = [start]
    visited: set[Pos] = {start}
    parent: dict[Pos, Pos] = {}

    while stack:
        cur = stack.pop()
        if cur == goal:
            return _reconstruct(parent, start, goal)

        for n in neighbors4(grid, cur[0], cur[1]):
            if n not in visited:
                visited.add(n)
                parent[n] = cur
                stack.append(n)

    return None


def _reconstruct(parent: dict[Pos, Pos], start: Pos, goal: Pos) -> Path:
    out: Path = []
    cur: Pos = goal
    while True:
        out.append(cur)
        if cur == start:
            break
        cur = parent[cur]
    out.reverse()
    return out


class DFS:
    """Class wrapper mirroring BFS style (optional use)."""

    def __init__(self, maze: Grid, start: Pos, goal: Pos):
        self.maze = maze
        self.start = start
        self.goal = goal
        self.path_result: Path = []
        self.order: List[Pos] = []

    def solve(self) -> bool:
        path = solve(self.maze, self.start, self.goal)
        if path is None:
            self.path_result = []
            return False
        self.path_result = path
        self.order = list(path)
        return True
