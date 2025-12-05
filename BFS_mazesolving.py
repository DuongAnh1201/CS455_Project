from collections import deque 

class BFS: 
  def __init__(self, maze, start, goal):
    self.maze = maze
    self.start = start
    self.goal = goal
    
    self.rows = len(maze)
    self.cols = len(maze[0])
    
    self.visited = set()
    self.parents = {}
    self.path = []
    self.order = []

def inbounds(self, r, c):
  return 0 <= r < self.rows and 0 <= c < self.cols

def free(self, r, c): 
  return self.maze[r][c] == 0

def neighbors(self, r, c): 
  direcrtions = [(1,0), (-1,0), (0,1), (0,-1)]
  for dr, dc in directions:
    nr, nc = r + dr, c + dc
    if self.inbounds(nr, nc) and self.free(nr, nc):
        yield (nr, nc)

def solve(self):
  queue = deque([self.start])
  self.visited.add(self.start)

  while queue:
      current = queue.popleft()
      self.order.append(current)
  
      if current == self.goal: 
          self.generate_path() 
          return True

      for neighbor in self.neighbors(*current):
          if neighbor not in self.visted:
            self.parents[neighbor] = current
            queue.append(neighbor)

  return False


def path(self):
  node = self.goal

  while node != self.start:
    self.path.append(node)
    node = self.parent[node]
    
  self.path.append(self.start)
  self.path.reverse()


  

