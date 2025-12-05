import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "../App.css";

function CompareVisualizer() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const { maze, algo1, algo2 } = state;

  // ALGO 1
  const [grid1, setGrid1] = useState([]);
  const [steps1, setSteps1] = useState([]);
  const [path1, setPath1] = useState([]);
  const [step1, setStep1] = useState(0);
  const [done1, setDone1] = useState(false);

  // ALGO 2
  const [grid2, setGrid2] = useState([]);
  const [steps2, setSteps2] = useState([]);
  const [path2, setPath2] = useState([]);
  const [step2, setStep2] = useState(0);
  const [done2, setDone2] = useState(false);

  // FETCH BOTH ALGORITHMS USING PROMISE.ALL
  useEffect(() => {
    Promise.all([
      fetch("http://localhost:8000/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ maze, algorithm: algo1 }),
      }).then((r) => r.json()),

      fetch("http://localhost:8000/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ maze, algorithm: algo2 }),
      }).then((r) => r.json()),
    ]).then(([a1, a2]) => {
      setGrid1(a1.maze);
      setSteps1(a1.steps);
      setPath1(a1.path);

      setGrid2(a2.maze);
      setSteps2(a2.steps);
      setPath2(a2.path);
    });
  }, []);

  // ANIMATE ALGO 1
  useEffect(() => {
    if (steps1.length === 0) return;
    let i = 0;
    function animate() {
      setStep1(i);
      i++;
      if (i < steps1.length) setTimeout(animate, 35);
      else setTimeout(() => setDone1(true), 150);
    }
    animate();
  }, [steps1]);

  // ANIMATE ALGO 2
  useEffect(() => {
    if (steps2.length === 0) return;
    let i = 0;
    function animate() {
      setStep2(i);
      i++;
      if (i < steps2.length) setTimeout(animate, 35);
      else setTimeout(() => setDone2(true), 150);
    }
    animate();
  }, [steps2]);

  // highlight logic
  const isExplored = (steps, s, r, c) =>
    steps.slice(0, s).some(([rr, cc]) => rr === r && cc === c);

  const isPath = (path, done, r, c) =>
    done && path.some(([rr, cc]) => rr === r && cc === c);

  const isStart = (r, c) => r === 0 && c === 0;
  const isEnd = (grid, r, c) =>
    r === grid.length - 1 && c === grid[0]?.length - 1;

  // GRID RENDERER
  const renderGrid = (grid, steps, path, stepCount, done) => (
    <div className="maze-box">
      {grid.map((row, r) => (
        <div key={r} className="maze-row">
          {row.map((cell, c) => {
            let cls = "maze-cell";
            if (isStart(r, c)) cls += " cell-start";
            else if (isEnd(grid, r, c)) cls += " cell-end";
            else if (isPath(path, done, r, c)) cls += " cell-path";
            else if (isExplored(steps, stepCount, r, c)) cls += " cell-explored";
            else if (cell === 1) cls += " cell-wall";
            else cls += " cell-empty";
            return <div key={c} className={cls}></div>;
          })}
        </div>
      ))}
    </div>
  );

  return (
    <div className="visualizer-wrapper">

      <div className="visualizer-header">
        <button className="back-btn" onClick={() => navigate("/")}>
          ← Back
        </button>
        <h1 className="algo-title">Algorithm Comparison</h1>
        <div></div>
      </div>

      {/* Side-by-side */}
      <div style={{ display: "flex", gap: "20px", justifyContent: "center" }}>
        <div>
          <h2 style={{ textAlign: "center" }}>{algo1.toUpperCase()}</h2>
          {renderGrid(grid1, steps1, path1, step1, done1)}
        </div>

        <div>
          <h2 style={{ textAlign: "center" }}>{algo2.toUpperCase()}</h2>
          {renderGrid(grid2, steps2, path2, step2, done2)}
        </div>
      </div>

    </div>
  );
}

export default CompareVisualizer;
