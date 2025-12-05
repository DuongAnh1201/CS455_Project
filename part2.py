import random
import time
import os
import sys

sys.setrecursionlimit(10000)

WIDTH = 20
HEIGHT = 6

# Create maze grid (1 = wall, 0 = path)
maze = [[1 for _ in range(WIDTH)] for _ in range(HEIGHT)]

# Move directions
DIRS = [(0,1), (0,-1), (1,0), (-1,0)]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_maze_step():
    clear()
    for row in maze:
        print("".join("█" if cell == 1 else " " for cell in row))
    time.sleep(0.15)

def in_bounds(x, y):
    return 0 <= x < WIDTH and 0 <= y < HEIGHT

def flood_maze(x, y):
    maze[y][x] = 0  # carve the cell
    print_maze_step()

    dirs = DIRS[:]
    random.shuffle(dirs)      # randomize directions

    for dx, dy in dirs:
        nx, ny = x + dx*2, y + dy*2 

        # Check if 2 cells away is in bounds AND still a wall
        if in_bounds(nx, ny) and maze[ny][nx] == 1:

            # Carve the wall between
            maze[y + dy][x + dx] = 0
            print_maze_step()

            # Recursively flood next cell
            flood_maze(nx, ny)
    print

clear()
flood_maze(0, 0)
print_maze_step()
print("MAZE FINISHED")
