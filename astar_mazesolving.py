"""
A* on an unweighted 4-connected grid (Manhattan heuristic).
Positions are (row, col); maze[row][col] is 0 path, 1 wall.
"""
from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

from maze_core import Grid, Pos, neighbors4

Path = List[Pos]


def _h(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def solve(grid: Grid, start: Pos, goal: Pos) -> Optional[Path]:
    if grid[start[0]][start[1]] != 0 or grid[goal[0]][goal[1]] != 0:
        return None

    open_heap: List[Tuple[int, int, Pos]] = []
    heapq.heappush(open_heap, (_h(start, goal), 0, start))
    came_from: Dict[Pos, Pos] = {}
    g_score: Dict[Pos, int] = {start: 0}

    while open_heap:
        _, g, current = heapq.heappop(open_heap)
        if g != g_score.get(current, -1):
            continue

        if current == goal:
            return _reconstruct_path(came_from, start, goal)

        for n in neighbors4(grid, current[0], current[1]):
            tentative = g + 1
            if tentative < g_score.get(n, 10**9):
                came_from[n] = current
                g_score[n] = tentative
                f = tentative + _h(n, goal)
                heapq.heappush(open_heap, (f, tentative, n))

    return None


def _reconstruct_path(came_from: Dict[Pos, Pos], start: Pos, goal: Pos) -> Path:
    cur = goal
    out: Path = []
    while True:
        out.append(cur)
        if cur == start:
            break
        cur = came_from[cur]
    out.reverse()
    return out


class AStar:
    """Class wrapper mirroring BFS style (optional use)."""

    def __init__(self, maze: Grid, start: Pos, goal: Pos):
        self.maze = maze
        self.start = start
        self.goal = goal
        self.path_result: Path = []

    def solve(self) -> bool:
        path = solve(self.maze, self.start, self.goal)
        if path is None:
            self.path_result = []
            return False
        self.path_result = path
        return True
