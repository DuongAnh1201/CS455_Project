import random
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
class Obstacle:
    def __init__(self, obstacle = None):
        self.obstacle = obstacle
    def default(self):
        if self.obstacle ==None:
            self.obstacle = [((0,0),(0,2)), ((-1,2),(2,2)), ((2,2),(2,4)), ((2,4),(0,4)), ((0,4),(0,5)), ((0,5),(5,5))]
        return self.obstacle
obs = Obstacle()
obs.default()  # Initialize obstacles
class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = 0
class RRT:
    def __init__(self, start, goal, map_size, obstacle = obs, iter = 500, step_size = 0.5):
        self._start = start
        self._goal = goal
        self._map_size = map_size
        self._obstacle = obstacle
        self._node_list = [self._start]
        self._goal_reached = False
        self._path = None
        self._max_iter = iter
        self.step_size = step_size

    
    def random_node(self):
        """Generate a random node in the map."""
        if random.random()<=0.2:
            rand_node = Node(random.randint(0, self._map_size), random.randint(0, self._map_size))
        else:
            rand_node = Node(self._goal.x, self._goal.y)
        return rand_node
    # def chunk_to_partial(self):
    #     """
    #     Divide the maze into 4 sections, each of them have one list of obstackles
    #     """

    def nearest_node(self, node_list, rand_node):
        """Find the nearest node in the tree to the random node"""
        distances = [np.linalg.norm([node.x-rand_node.x, node.y- rand_node.y]) for node in node_list]
        nearest_node = node_list[np.argmin(distances)]
        return nearest_node
    
    def plan(self):
        """Main RRT planning loop"""
        for i in range(self._max_iter):
            rand_node = self.random_node()
            nearest_node = self.nearest_node(self._node_list, rand_node)
            new_node = self.steer(nearest_node, rand_node)

            if new_node and self.is_collision_free(nearest_node, new_node):
                new_node.parent = nearest_node
                self._node_list.append(new_node)
            
            if new_node and self.reached_goal(new_node):
                self._path = self.generate_final_path(new_node)
                self._goal_reached = True
                return
    
    def steer(self, from_node, to_node):
        """Steer from one node to another, step-by-step."""
        # Improved Logic (Mental Sandbox)
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
        """Convert obstacle line segments to line equations (a, b) where y = ax + b."""
        res = []
        obstacles = self._obstacle.obstacle if hasattr(self._obstacle, 'obstacle') else self._obstacle
        for i in obstacles:
            m, n = i
            m_x, m_y = m
            n_x, n_y = n
            if m_x == n_x:
                # Vertical line: store x coordinate in b, use a = inf marker
                res.append((float('inf'), m_x))
            else:
                a = (m_y-n_y)/(m_x-n_x)
                b = m_y-m_x*a
                res.append((a,b))
        return res
    
    def is_collision_free(self, from_node, to_node):
        """Check if the path from from_node to to_node is collision-free."""
        obstacles = self._obstacle.obstacle if hasattr(self._obstacle, 'obstacle') else self._obstacle
        if not obstacles:
            return True
        
        res = self.obs_to_line()
        if from_node.x == to_node.x:
            a = float('inf')  # Vertical line
            b = from_node.x
        else:
            a = (from_node.y-to_node.y)/(from_node.x-to_node.x)
            b = from_node.y-from_node.x*a
        
        for i in range(len(obstacles)):
            obstacle_line = obstacles[i]
            m, n = obstacle_line
            m_x, m_y = m
            n_x, n_y = n
            a_i, b_i = res[i]
            
            # Check for parallel lines
            if from_node.x == to_node.x:
                # Path is vertical
                if a_i == float('inf'):  # Obstacle is also vertical
                    if abs(b - b_i) < 1e-6:  # Same vertical line
                        # Check if segments overlap
                        y_min_path = min(from_node.y, to_node.y)
                        y_max_path = max(from_node.y, to_node.y)
                        y_min_obs = min(m_y, n_y)
                        y_max_obs = max(m_y, n_y)
                        if not (y_max_path < y_min_obs or y_min_path > y_max_obs):
                            return False
                continue
            elif a_i == float('inf'):  # Obstacle is vertical
                x_intersect = b_i
                y_intersect = a * x_intersect + b
            elif abs(a - a_i) < 1e-6:  # Parallel lines
                if abs(b - b_i) < 1e-6:  # Same line
                    # Check if segments overlap
                    x_min_path = min(from_node.x, to_node.x)
                    x_max_path = max(from_node.x, to_node.x)
                    x_min_obs = min(m_x, n_x)
                    x_max_obs = max(m_x, n_x)
                    if not (x_max_path < x_min_obs or x_min_path > x_max_obs):
                        return False
                continue
            else:
                # Find intersection point
                x_intersect = (b_i - b) / (a - a_i)
                y_intersect = a * x_intersect + b
            
            # Check if intersection is within both segments
            x_min_path = min(from_node.x, to_node.x)
            x_max_path = max(from_node.x, to_node.x)
            y_min_path = min(from_node.y, to_node.y)
            y_max_path = max(from_node.y, to_node.y)
            
            x_min_obs = min(m_x, n_x)
            x_max_obs = max(m_x, n_x)
            y_min_obs = min(m_y, n_y)
            y_max_obs = max(m_y, n_y)
            
            if (x_min_path <= x_intersect <= x_max_path and 
                y_min_path <= y_intersect <= y_max_path and
                x_min_obs <= x_intersect <= x_max_obs and
                y_min_obs <= y_intersect <= y_max_obs):
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
        
        Args:
            title: Title of the plot
            show_tree: Whether to show the RRT tree (nodes and edges)
            show_path: Whether to show the final path if found
            figsize: Figure size (width, height)
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
            # Draw all edges (connections between parent and child)
            for node in self._node_list[1:]:  # Skip start node (no parent)
                if node.parent is not None:
                    ax.plot([node.parent.x, node.x], [node.parent.y, node.y], 
                           'lightblue', linewidth=0.5, alpha=0.6, zorder=1)
            
            # Draw all nodes
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
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return fig, ax
    
    def visualize_animation(self, step=10, title="RRT Path Planning Animation", figsize=(10, 10)):
        """
        Visualize the RRT tree growth step by step.
        
        Args:
            step: Show tree every 'step' iterations
            title: Title of the plot
            figsize: Figure size (width, height)
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
                ax.plot([x1, x2], [y1, y2], 'k-', linewidth=3)
        
        # Save current node list length to track growth
        previous_node_count = 1
        
        # Draw start and goal
        ax.scatter(self._start.x, self._start.y, c='green', s=200, 
                  marker='o', edgecolors='darkgreen', linewidths=2, zorder=7, label='Start')
        ax.scatter(self._goal.x, self._goal.y, c='red', s=200, 
                  marker='*', edgecolors='darkred', linewidths=2, zorder=7, label='Goal')
        
        # Run planning with animation
        for i in range(self._max_iter):
            rand_node = self.random_node()
            nearest_node = self.nearest_node(self._node_list, rand_node)
            new_node = self.steer(nearest_node, rand_node)

            if new_node and self.is_collision_free(nearest_node, new_node):
                new_node.parent = nearest_node
                self._node_list.append(new_node)
                
                # Draw new edge
                ax.plot([nearest_node.x, new_node.x], [nearest_node.y, new_node.y], 
                       'lightblue', linewidth=0.5, alpha=0.6, zorder=1)
                # Draw new node
                ax.scatter(new_node.x, new_node.y, c='lightblue', s=20, alpha=0.6, 
                          edgecolors='blue', linewidths=0.5, zorder=2)
                
                # Update plot every 'step' iterations
                if len(self._node_list) - previous_node_count >= step:
                    ax.set_title(f"{title} - Iteration {i+1}, Nodes: {len(self._node_list)}", 
                               fontsize=14, fontweight='bold')
                    plt.pause(0.01)
                    previous_node_count = len(self._node_list)
            
            if new_node and self.reached_goal(new_node):
                self._path = self.generate_final_path(new_node)
                self._goal_reached = True
                
                # Draw final path
                path_x = [point[0] for point in self._path]
                path_y = [point[1] for point in self._path]
                ax.plot(path_x, path_y, 'r-', linewidth=3, zorder=5, label='Final Path')
                ax.scatter(path_x, path_y, c='red', s=50, zorder=6, edgecolors='darkred', linewidths=1.5)
                
                ax.set_title(f"{title} - Goal Reached! Iteration {i+1}", 
                           fontsize=14, fontweight='bold', color='green')
                plt.pause(0.1)
                break
        
        # Set plot properties
        ax.set_xlim(-1, self._map_size + 1)
        ax.set_ylim(-1, self._map_size + 1)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X', fontsize=12)
        ax.set_ylabel('Y', fontsize=12)
        
        # Add legend
        ax.legend(loc='upper right', fontsize=10)
        
        plt.tight_layout()
        return fig, ax


# Example usage and visualization function
def visualize_rrt_example():
    """
    Example function demonstrating how to use RRT with visualization.
    """
    # Create obstacles
    obstacles = Obstacle()
    obstacles.default()
    
    # Define start and goal positions
    start_node = Node(1, 1)
    goal_node = Node(4, 4)
    map_size = 6
    
    # Create RRT planner
    rrt = RRT(start=start_node, goal=goal_node, map_size=map_size, 
              obstacle=obstacles, iter=1000, step_size=0.3)
    
    # Run the planning algorithm
    print("Running RRT path planning...")
    rrt.plan()
    
    # Visualize the result
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
    # Run example
    rrt_result = visualize_rrt_example()

                




