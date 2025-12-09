import random
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

class Obstacle:
    def __init__(self, obstacle=None):
        self.obstacle = obstacle

    def default(self):
        if self.obstacle is None:
            # Format: [((x1, y1), (x2, y2)), ...]
            # Assumed Map Size: 10x10 area
            self.obstacle = [
    # --- Outer Boundary (with entry top-left and exit bottom-right) ---
    ((0, 0), (0, 10)),    # Left wall
    ((1, 10), (10, 10)),  # Top wall (gap from x=0..1 for entry)
    ((10, 10), (10, 1)),  # Right wall (gap from y=0..1 for exit)
    ((10, 0), (0, 0)),    # Bottom wall

    # --- Internal Walls (10x10 grid-aligned, structure-preserving) ---
    # Top band
    ((1, 9), (4, 9)),
    ((4, 9), (4, 6)),
    ((4, 7), (6, 7)),
    ((6, 9), (9, 9)),
    ((8, 10), (8, 9.2)),  # short top connector

    # Upper-left cluster
    ((1.5, 8), (3.5, 8)),
    ((1.5, 8), (1.5, 6.5)),
    ((3.5, 8), (3.5, 7)),
    ((1.5, 6.5), (2.5, 6.5)),

    # Upper-center / upper-right connectors
    ((5, 10), (5, 8.2)),
    ((6.5, 8), (6.5, 6)),
    ((7.5, 8.5), (7.5, 7.5)),
    ((9, 8), (9, 6.2)),

    # Middle big barriers
    ((0.8, 6), (3.2, 6)),
    ((3.2, 6), (3.2, 4)),
    ((3.2, 4), (6.8, 4)),
    ((6.8, 4), (6.8, 2)),

    # Center features (vertical corridors / boxes)
    ((2.8, 5.2), (2.8, 3.2)),
    ((4.8, 6.2), (4.8, 5)),
    ((5.8, 6.2), (5.8, 4.4)),
    ((7.2, 5.5), (7.2, 3.8)),

    # Middle-left horizontal connectors
    ((0.5, 4.5), (2.5, 4.5)),
    ((1, 3.2), (2.2, 3.2)),

    # Lower-middle pattern (meandering)
    ((1.8, 3.2), (1.8, 1.8)),
    ((1.8, 1.8), (4.2, 1.8)),
    ((4.2, 1.8), (4.2, 3.6)),
    ((4.2, 3.6), (6.2, 3.6)),
    ((6.2, 3.6), (6.2, 2.4)),
    ((6.2, 2.4), (8.2, 2.4)),

    # Lower-left spiral-ish
    ((0.8, 2.2), (0.8, 0.8)),
    ((0.8, 2.2), (2.2, 2.2)),
    ((2.2, 2.2), (2.2, 0.8)),
    ((2.2, 0.8), (4.6, 0.8)),

    # Lower-right connectors & dead-ends
    ((5.6, 1.6), (8.0, 1.6)),
    ((8.0, 1.6), (8.0, 3.2)),
    ((8.0, 3.2), (9.2, 3.2)),
    ((7.2, 0.8), (7.2, 2.0)),
    ((9.2, 4.2), (9.2, 6.2)),
    ((7.8, 5.2), (9.2, 5.2)),

    # Small interior stubs to capture tight corridors
    ((3.8, 2.8), (5.0, 2.8)),
    ((4.6, 4.8), (5.6, 4.8)),
    ((2.8, 7.2), (4.6, 7.2)),

    # A few short separators to reflect image detail
    ((6.8, 7.8), (6.8, 7.0)),
    ((3.0, 0.8), (3.0, 1.8)),
    ((8.8, 0.8), (8.8, 1.4)),
]

        return self.obstacle

# Initialize obstacles global for default param usage
obs = Obstacle()
obs.default()  

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = 0

class RRT:
    def __init__(self, start, goal, map_size, obstacle=obs, iter=500, step_size=1):
        self._start = start
        self._goal = goal
        self._map_size = map_size
        self._obstacle = obstacle
        self._node_list = [self._start]
        self._goal_reached = False
        self._path = None
        self._max_iter = iter
        self.step_size = step_size
        self._obstacle_lines = self.obs_to_line()
    
    def random_node(self):
        """Generate a random node in the map."""
        if random.random() <= 0.7:
            rand_node = Node(random.randint(0, self._map_size), random.randint(0, self._map_size))
        else:
            rand_node = Node(self._goal.x, self._goal.y)
        return rand_node

    def nearest_node(self, node_list, rand_node):
        """Find the nearest node in the tree to the random node"""
        distances = [np.linalg.norm([node.x - rand_node.x, node.y - rand_node.y]) for node in node_list]
        nearest_node = node_list[np.argmin(distances)]
        return nearest_node
    
    def plan(self):
        """Main RRT planning loop"""
        for i in range(self._max_iter):
            rand_node = self.random_node()
            nearest_node = self.nearest_node(self._node_list, rand_node)
            new_node = self.steer(nearest_node, rand_node)

            if self.is_collision_free(nearest_node, new_node):
                new_node.parent = nearest_node
                self._node_list.append(new_node)
            
            if self.reached_goal(new_node):
                self._path = self.generate_final_path(new_node)
                self._goal_reached = True
                return
    
    def steer(self, from_node, to_node):
        """Steer from one node to another, step-by-step."""
        dist = math.hypot(to_node.x - from_node.x, to_node.y - from_node.y)

        if dist < self.step_size:
            # If target is close, just go there!
            new_x = to_node.x
            new_y = to_node.y
            cost_increment = dist
        else:
            # If target is far, Step forward by step_size
            theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
            new_x = from_node.x + self.step_size * math.cos(theta)
            new_y = from_node.y + self.step_size * math.sin(theta)
            cost_increment = self.step_size
        
        new_node = Node(new_x, new_y)
        new_node.cost = from_node.cost + cost_increment
        return new_node

    def obs_to_line(self):
        """Convert obstacle line segments to line equations (a, b) where y = ax + b.
        Vertical lines are marked as (inf, x_intercept)."""
        res = []
        obstacles = self._obstacle.obstacle if hasattr(self._obstacle, 'obstacle') else self._obstacle
        
        for (m, n) in obstacles:
            m_x, m_y = m
            n_x, n_y = n
            
            # Vertical line
            if m_x == n_x:
                res.append((float('inf'), m_x))   # a = inf, b = x-intercept
            else:
                a = (m_y - n_y) / (m_x - n_x)
                b = m_y - m_x * a
                res.append((a, b))
        
        return res

    def is_intersection(self, seg_a, seg_b, node):
        """Check if point `node` lies within the bounding box of segment endpoints seg_a and seg_b.
        Accepts seg_a and seg_b as either tuples (x, y) or Node objects."""
        # Handle both tuple and Node formats
        if isinstance(seg_a, tuple):
            x_a, y_a = seg_a
        else:
            x_a, y_a = seg_a.x, seg_a.y
        
        if isinstance(seg_b, tuple):
            x_b, y_b = seg_b
        else:
            x_b, y_b = seg_b.x, seg_b.y
        
        x = node.x
        y = node.y
        
        # Check if point is within the bounds (with small epsilon for float errors)
        return (
            min(x_a, x_b) - 1e-6 <= x <= max(x_a, x_b) + 1e-6 and
            min(y_a, y_b) - 1e-6 <= y <= max(y_a, y_b) + 1e-6
        )

    def is_collision_free(self, from_node, to_node):
        """Check if the path segment from from_node to to_node intersects any obstacle line segment."""
        obstacles = self._obstacle.obstacle if hasattr(self._obstacle, 'obstacle') else self._obstacle
        if not obstacles:
            return True

        res = self._obstacle_lines

        # Path line equation
        if abs(from_node.x - to_node.x) < 1e-6:
            a = float('inf')  # vertical line
            b = from_node.x
        else:
            a = (from_node.y - to_node.y) / (from_node.x - to_node.x)
            b = from_node.y - from_node.x * a

        # Check against every obstacle
        for i in range(len(obstacles)):
            (m, n) = obstacles[i]
            m_x, m_y = m
            n_x, n_y = n
            a_i, b_i = res[i]

            intersect_node = None

            # -------- CASE 1: BOTH LINES VERTICAL --------
            if a == float('inf') and a_i == float('inf'):
                if abs(b - b_i) < 1e-6:  # same x = constant line
                    # Check y-range overlap
                    if not (max(from_node.y, to_node.y) < min(m_y, n_y) or
                            min(from_node.y, to_node.y) > max(m_y, n_y)):
                        return False
                continue

            # -------- CASE 2: PATH VERTICAL, OBSTACLE NON-VERTICAL --------
            elif a == float('inf') and a_i != float('inf'):
                x = b
                y = a_i * x + b_i
                intersect_node = Node(x, y)

            # -------- CASE 3: OBSTACLE VERTICAL, PATH NON-VERTICAL --------
            elif a_i == float('inf') and a != float('inf'):
                x = b_i
                y = a * x + b
                intersect_node = Node(x, y)

            # -------- CASE 4: BOTH NON-VERTICAL --------
            else:
                if abs(a - a_i) < 1e-6:
                    # Parallel lines
                    continue
                else:
                    # Compute true intersection point
                    x = (b_i - b) / (a - a_i)
                    y = a * x + b
                    intersect_node = Node(x, y)

            # [FIXED LOGIC] If we found an intersection point, we must check if it lies 
            # on BOTH the path segment AND the obstacle segment.
            if intersect_node:
                on_path = self.is_intersection(from_node, to_node, intersect_node)
                on_obstacle = self.is_intersection(m, n, intersect_node)
                
                if on_path and on_obstacle:
                    return False

        return True
    
    def reached_goal(self, node):
        """Check if the node has reached the goal."""
        dist = math.hypot(node.x - self._goal.x, node.y - self._goal.y)
        return dist <= self.step_size

    def generate_final_path(self, goal_node):
        """Generate the final path from the start to the goal."""
        path = []
        node = goal_node
        while node is not None:
            path.append([node.x, node.y])
            node = node.parent
        return path[::-1]  # Reverse the path
    
    def visualize(self, title="RRT Path Planning", show_tree=True, show_path=True, figsize=(10, 10)):
        """
        Visualize the RRT tree, obstacles, start, goal, and path.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get obstacles
        obstacles = self._obstacle.obstacle if hasattr(self._obstacle, 'obstacle') else self._obstacle
        
        # Draw obstacles
        if obstacles:
            for obstacle in obstacles:
                point1, point2 = obstacle
                x1, y1 = point1
                x2, y2 = point2
                ax.plot([x1, x2], [y1, y2], 'k-', linewidth=3, label='Obstacles' if obstacle == obstacles[0] else '')
        
        # Draw RRT tree
        if show_tree and self._node_list:
            for node in self._node_list[1:]:
                if node.parent is not None:
                    ax.plot([node.parent.x, node.x], [node.parent.y, node.y], 
                           'lightblue', linewidth=0.5, alpha=0.6, zorder=1)
            
            node_x = [node.x for node in self._node_list]
            node_y = [node.y for node in self._node_list]
            ax.scatter(node_x, node_y, c='lightblue', s=20, alpha=0.6, 
                      edgecolors='blue', linewidths=0.5, zorder=2, label='RRT Nodes')
        
        # Draw final path if found
        if show_path and self._path is not None:
            path_x = [point[0] for point in self._path]
            path_y = [point[1] for point in self._path]
            ax.plot(path_x, path_y, 'r-', linewidth=3, zorder=5, label='Final Path')
            ax.scatter(path_x, path_y, c='red', s=50, zorder=6, edgecolors='darkred', linewidths=1.5)
        
        # Draw start node
        ax.scatter(self._start.x, self._start.y, c='green', s=200, 
                  marker='o', edgecolors='darkgreen', linewidths=2, 
                  zorder=7, label='Start')
        
        # Draw goal node
        ax.scatter(self._goal.x, self._goal.y, c='red', s=200, 
                  marker='*', edgecolors='darkred', linewidths=2, 
                  zorder=7, label='Goal')
        
        # Set plot properties
        ax.set_xlim(-1, self._map_size + 1)
        ax.set_ylim(-1, self._map_size + 1)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X', fontsize=12)
        ax.set_ylabel('Y', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Add legend
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=10)
        
        # Add info text
        info_text = f"Iterations: {self._max_iter}\n"
        info_text += f"Nodes: {len(self._node_list)}\n"
        info_text += f"Goal Reached: {'Yes' if self._goal_reached else 'No'}"
        if self._path is not None:
            path_length = sum(math.hypot(self._path[i+1][0] - self._path[i][0], 
                                       self._path[i+1][1] - self._path[i][1]) 
                            for i in range(len(self._path)-1))
            info_text += f"\nPath Length: {path_length:.2f}"
        
        # [FIXED SYNTAX] Removed invalid type hinting syntax for bbox dict
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return fig, ax
    
    def visualize_animation(self, step=10, title="RRT Path Planning Animation", figsize=(10, 10)):
        """
        Visualize the RRT tree growth step by step.
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        obstacles = self._obstacle.obstacle if hasattr(self._obstacle, 'obstacle') else self._obstacle
        
        if obstacles:
            for obstacle in obstacles:
                point1, point2 = obstacle
                x1, y1 = point1
                x2, y2 = point2
                ax.plot([x1, x2], [y1, y2], 'k-', linewidth=3)
        
        previous_node_count = 1
        
        ax.scatter(self._start.x, self._start.y, c='green', s=200, 
                  marker='o', edgecolors='darkgreen', linewidths=2, zorder=7, label='Start')
        ax.scatter(self._goal.x, self._goal.y, c='red', s=200, 
                  marker='*', edgecolors='darkred', linewidths=2, zorder=7, label='Goal')
        
        for i in range(self._max_iter):
            rand_node = self.random_node()
            nearest_node = self.nearest_node(self._node_list, rand_node)
            new_node = self.steer(nearest_node, rand_node)

            if new_node and self.is_collision_free(nearest_node, new_node):
                new_node.parent = nearest_node
                self._node_list.append(new_node)
                
                ax.plot([nearest_node.x, new_node.x], [nearest_node.y, new_node.y], 
                       'lightblue', linewidth=0.5, alpha=0.6, zorder=1)
                ax.scatter(new_node.x, new_node.y, c='lightblue', s=20, alpha=0.6, 
                          edgecolors='blue', linewidths=0.5, zorder=2)
                
                if len(self._node_list) - previous_node_count >= step:
                    ax.set_title(f"{title} - Iteration {i+1}, Nodes: {len(self._node_list)}", 
                               fontsize=14, fontweight='bold')
                    plt.pause(0.01)
                    previous_node_count = len(self._node_list)
            
            if new_node and self.reached_goal(new_node):
                self._path = self.generate_final_path(new_node)
                self._goal_reached = True
                
                path_x = [point[0] for point in self._path]
                path_y = [point[1] for point in self._path]
                ax.plot(path_x, path_y, 'r-', linewidth=3, zorder=5, label='Final Path')
                ax.scatter(path_x, path_y, c='red', s=50, zorder=6, edgecolors='darkred', linewidths=1.5)
                
                ax.set_title(f"{title} - Goal Reached! Iteration {i+1}", 
                           fontsize=14, fontweight='bold', color='green')
                plt.pause(0.1)
                break
        
        ax.set_xlim(-1, self._map_size + 1)
        ax.set_ylim(-1, self._map_size + 1)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X', fontsize=12)
        ax.set_ylabel('Y', fontsize=12)
        ax.legend(loc='upper right', fontsize=10)
        plt.tight_layout()
        return fig, ax

def visualize_rrt_example():
    """
    Example function demonstrating how to use RRT with visualization.
    """
    obstacles = Obstacle()
    obstacles.default()
    
    start_node = Node(0.5, 9.5)
    goal_node = Node(10, 0)
    map_size = 10
    
    rrt = RRT(start=start_node, 
            goal=goal_node, 
            map_size=map_size, 
            obstacle=obstacles, 
            iter=50000, 
            step_size=0.3)
    
    print("Running RRT path planning...")
    rrt.plan()
    
    if rrt._goal_reached:
        print(f"✓ Goal reached! Path found with {len(rrt._path)} nodes.")
        fig, ax = rrt.visualize(title="RRT Maze Solving - Final Result")
        plt.show()
    else:
        print("✗ Goal not reached. Showing current tree:")
        fig, ax = rrt.visualize(title="RRT Maze Solving - No Path Found")
        plt.show()
    
    return rrt

if __name__ == "__main__":
    rrt_result = visualize_rrt_example()