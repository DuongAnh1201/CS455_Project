import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../App.css";

function Visualizer() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { maze, algorithm } = state;

  const [grid, setGrid] = useState([]);
  const [steps, setSteps] = useState([]);
  const [path, setPath] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [finished, setFinished] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch from backend
  useEffect(() => {
    setLoading(true);

    fetch("http://localhost:8000/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ maze, algorithm }),
    })
      .then((res) => res.json())
      .then((data) => {
        setGrid(data.maze);
        setSteps(data.steps);
        setPath(data.path);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [maze, algorithm]);

  // Animation
  useEffect(() => {
    if (steps.length === 0) return;

    let i = 0;

    function animate() {
      setCurrentStep(i);
      i++;

      if (i < steps.length) {
        setTimeout(animate, 35);
      } else {
        setTimeout(() => setFinished(true), 100);
      }
    }

    animate();
  }, [steps]);

  function isExplored(r, c) {
    return steps.slice(0, currentStep).some((s) => s[0] === r && s[1] === c);
  }

  function isPathCell(r, c) {
    return finished && path.some((p) => p[0] === r && p[1] === c);
  }

  const isStart = (r, c) => r === 0 && c === 0;
  const isEnd = (r, c) =>
    r === grid.length - 1 && c === grid[0]?.length - 1;

  if (loading) {
    return (
      <div className="visualizer-wrapper">
        <div className="loading-box">
          <div className="loader"></div>
          <p>Running {algorithm.toUpperCase()}...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="visualizer-wrapper">
      <div className="visualizer-header">
        <button className="back-btn" onClick={() => navigate("/")}>
          ← Back
        </button>

        <h1 className="algo-title">
          {algorithm.toUpperCase()} Visualization
        </h1>

        <div className={`status ${finished ? "done" : "running"}`}>
          {finished ? "Finished" : "Searching..."}
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{currentStep}</div>
          <div className="stat-label">Visited</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">
            {finished ? path.length : "..."}
          </div>
          <div className="stat-label">Path Length</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">
            {grid.length} × {grid[0].length}
          </div>
          <div className="stat-label">Grid Size</div>
        </div>
      </div>

      {/* Legend */}
      <div className="legend">
        <div className="legend-item">
          <div className="legend-box start"></div> Start
        </div>
        <div className="legend-item">
          <div className="legend-box end"></div> End
        </div>
        <div className="legend-item">
          <div className="legend-box wall"></div> Wall
        </div>
        <div className="legend-item">
          <div className="legend-box explored"></div> Explored
        </div>
        <div className="legend-item">
          <div className="legend-box path"></div> Path
        </div>
      </div>

      {/* Maze Grid */}
      <div className="maze-box">
        {grid.map((row, r) => (
          <div key={r} className="maze-row">
            {row.map((cell, c) => {
              let className = "maze-cell";

              if (isStart(r, c)) className += " cell-start";
              else if (isEnd(r, c)) className += " cell-end";
              else if (isPathCell(r, c)) className += " cell-path";
              else if (isExplored(r, c)) className += " cell-explored";
              else if (cell === 1) className += " cell-wall";
              else className += " cell-empty";

              return <div key={c} className={className}></div>;
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

export default Visualizer;
