import argparse
import os
import random
import sys

sys.setrecursionlimit(10000)

from maze_core import (
    DEFAULT_HEIGHT as HEIGHT,
    DEFAULT_WIDTH as WIDTH,
    find_corner_goal,
    generate_maze_grid,
    stdout_wall_char,
)

maze: list[list[int]] = []


def generate_maze(animate: bool = True) -> list[list[int]]:
    """Build a new maze; returns the grid (same algorithm as before, via maze_core)."""
    global maze
    rng = random.Random()
    on_step = None
    if animate:
        wall, free = stdout_wall_char()

        def on_step_fn(g: list[list[int]]) -> None:
            os.system("cls" if os.name == "nt" else "clear")
            for row in g:
                print("".join(wall if cell == 1 else free for cell in row))
            import time

            time.sleep(0.15)

        on_step = on_step_fn
        os.system("cls" if os.name == "nt" else "clear")

    maze = generate_maze_grid(WIDTH, HEIGHT, rng=rng, on_step=on_step)
    if animate and on_step:
        on_step(maze)
    return maze


def run_rrt_on_generated_maze(
    maze_grid: list[list[int]],
    show_plot: bool = True,
    save_path: str | None = None,
) -> object:
    """Plan with RRT in continuous space using wall segments from the grid maze."""
    from RRT_mazesolving import rrt_on_grid_maze
    import matplotlib.pyplot as plt

    start = (0, 0)
    goal = find_corner_goal(maze_grid)
    rrt = rrt_on_grid_maze(
        maze_grid,
        start_rc=start,
        goal_rc=goal,
        iter=8000,
        step_size=0.35,
    )
    title = "RRT on generated maze"
    if rrt._goal_reached:
        print(f"RRT: goal reached, path length {len(rrt._path)} waypoints.")
    else:
        print("RRT: goal not reached; try increasing iter or step_size.")
    fig, ax = rrt.visualize(title=title)
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved RRT figure to {save_path}")
    if show_plot:
        plt.show()
    else:
        plt.close(fig)
    return rrt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate a maze and plan with RRT.")
    p.add_argument(
        "--fast",
        action="store_true",
        help="Skip maze animation (no clear/sleep during generation).",
    )
    p.add_argument(
        "--no-plot",
        action="store_true",
        help="Do not open a window for the RRT figure.",
    )
    p.add_argument(
        "--save-rrt",
        metavar="FILE",
        help="Save the RRT plot as a PNG (e.g. rrt.png).",
    )
    args = p.parse_args()
    show_window = not args.no_plot
    if not show_window and not args.save_rrt:
        args.save_rrt = "rrt_maze.png"
        print("No display requested; saving RRT plot to rrt_maze.png (use --save-rrt to pick a path).")

    generate_maze(animate=not args.fast)
    print("MAZE FINISHED")
    run_rrt_on_generated_maze(
        maze,
        show_plot=show_window,
        save_path=args.save_rrt,
    )
