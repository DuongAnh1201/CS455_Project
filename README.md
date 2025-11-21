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

- **Backend/Algorithms**: Python 3.12
- **Frontend**: JavaScript, React
- **Visualization**: Real-time rendering with React components

## Installation

```bash
# Clone the repository
git clone [repository-url]

# Navigate to project directory
cd maze-solving-visualizer

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for the frontend
cd ui
npm install
cd ..
```

## Usage

```bash
# Start the Python backend (in one terminal)
python main.py

# Start the React frontend (in another terminal)
cd ui
npm start
```

1. Select a maze layout from the available options
2. Choose an algorithm (BFS, Flood Fill, or Randomized Search)
3. Click "Start" to visualize the algorithm solving the maze
4. Compare results across different algorithms

## Project Goals

- Full implementation of BFS and Flood Fill algorithms across multiple mazes
- Adaptation of random tree-based pathfinding theory for 2D maze environments
- Clear visualization of algorithm differences in performance and approach
- Accurate implementation demonstrating the strengths and weaknesses of each method

## Contributing

All team members contribute to core algorithm implementation. For specific questions or contributions related to different aspects:
- UI/UX: Contact Aayush
- Project coordination: Contact Tom
- Documentation: Contact Anthony or Josiah
