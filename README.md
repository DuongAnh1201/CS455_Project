# Maze-Solving Algorithms Visualizer

An interactive visualization tool that demonstrates and compares different pathfinding algorithms for maze solving.

## Project Overview

This project creates an interactive maze-solving visualizer that demonstrates how different pathfinding algorithms explore and solve mazes. Users can select from multiple maze layouts and watch each algorithm solve them in real-time, allowing for direct comparison of their performance, efficiency, and solution paths.

## Algorithms Implemented

### 1. Breadth-First Search (BFS)
A classic graph traversal algorithm that explores all neighboring nodes at the current depth before moving to nodes at the next depth level. Guarantees the shortest path in unweighted mazes.

### 2. Flood Fill
An algorithm that spreads through connected regions, commonly used in graphics applications and maze solving. It explores the maze by filling adjacent cells until the goal is reached.

### 3. Randomized Search Algorithm
Based on random tree theory in pathfinding, primarily used in robotics applications. This approach has been adapted for 2D maze environments to demonstrate probabilistic pathfinding methods.

## Features

- **Multiple Maze Options**: Choose from various pre-designed maze layouts
- **Real-time Visualization**: Watch algorithms solve mazes step-by-step
- **Algorithm Comparison**: Compare speed, efficiency, and paths taken by different algorithms
- **Clean, Simple UI**: Focus on algorithm performance with an intuitive interface

## Technology Stack

- **Backend/Algorithms**: Python 3.12, FastAPI 
- **Frontend**: JavaScript, React
- **Visualization**: Real-time rendering with React components

## Installation

```bash
# Clone the repository
git clone [repository-url]

# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt


## Usage

# start the backend server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Backend will run
http://localhost:8000


# Install Node.js dependencies for the frontend
cd frontend
npm install
npm start

# Frontend will be live at
http://localhost:3000
```

1. Select a maze difficulty
2. Choose visualization mode:
 - Single Algorithm
 - Compare Algorithms
3. Choose your algorithm(s):
 - BFS
 - DFS
 - Flood Fill
 - A* (Manhattan)
 - A* (Euclidean)
4. Click Start Visualization
5. Watch the algorithm solve the maze in real time!

## Project Goals

- Full implementation of BFS and Flood Fill algorithms across multiple mazes
- Adaptation of random tree-based pathfinding theory for 2D maze environments
- Clear visualization of algorithm differences in performance and approach
- Accurate implementation demonstrating the strengths and weaknesses of each method

## Contributing

All team members contribute to core algorithm implementation. For specific questions or contributions related to different aspects:
- UI/UX: Contact Aayush
- Backend setup and algorithms: Contact Aayush ( DFS, A*)
- Project coordination: Contact Tom (RRT)
- Documentation: Contact Anthony or Josiah (BFS AND Flood Fill)
