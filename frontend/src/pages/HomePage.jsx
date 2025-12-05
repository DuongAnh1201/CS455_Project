import { useNavigate } from "react-router-dom";
import { useState } from "react";
import "../App.css";

function HomePage() {
  const navigate = useNavigate();

  const [mode, setMode] = useState("single");
  const [maze, setMaze] = useState("easy");

  const [algo1, setAlgo1] = useState("bfs");
  const [algo2, setAlgo2] = useState("dfs");

  const handleStart = () => {
    if (mode === "single") {
      navigate("/visualize", {
        state: { maze, algorithm: algo1 },
      });
    } else {
      navigate("/compare", {
        state: { maze, algo1, algo2 },
      });
    }
  };

  return (
    <div className="home-wrapper">
      <div className="home-container">

        <header className="home-header">
          <h1 className="home-title">Pathfinding Visualizer</h1>
          <p className="home-subtitle">Explore & Compare Algorithms</p>
        </header>

        {/* Mode */}
        <section className="section">
          <h2 className="section-label">Mode</h2>

          <div className="button-group">
            <button
              onClick={() => setMode("single")}
              className={`option-btn ${mode === "single" ? "selected" : ""}`}
            >
              Single Algorithm
            </button>

            <button
              onClick={() => setMode("compare")}
              className={`option-btn ${mode === "compare" ? "selected" : ""}`}
            >
              Compare Two
            </button>
          </div>
        </section>

        {/* Maze Difficulty */}
        <section className="section">
          <h2 className="section-label">Maze Difficulty</h2>

          <div className="button-group">
            <button onClick={() => setMaze("easy")}
              className={`option-btn ${maze === "easy" ? "selected" : ""}`}>
              Easy
            </button>
            <button onClick={() => setMaze("medium")}
              className={`option-btn ${maze === "medium" ? "selected" : ""}`}>
              Medium
            </button>
            <button onClick={() => setMaze("hard")}
              className={`option-btn ${maze === "hard" ? "selected" : ""}`}>
              Hard
            </button>
          </div>
        </section>

        {/* Algorithm Section */}
        {mode === "single" ? (
          <section className="section">
            <h2 className="section-label">Algorithm</h2>

            <div className="button-group">
              <button onClick={() => setAlgo1("bfs")}
                className={`option-btn ${algo1 === "bfs" ? "selected" : ""}`}>
                BFS
              </button>

              <button onClick={() => setAlgo1("dfs")}
                className={`option-btn ${algo1 === "dfs" ? "selected" : ""}`}>
                DFS
              </button>

              <button onClick={() => setAlgo1("flood")}
                className={`option-btn ${algo1 === "flood" ? "selected" : ""}`}>
                Flood Fill
              </button>

              {/* NEW A* OPTIONS */}
              <button onClick={() => setAlgo1("astar_manhattan")}
                className={`option-btn ${algo1 === "astar_manhattan" ? "selected" : ""}`}>
                A* (Manhattan)
              </button>

              <button onClick={() => setAlgo1("astar_euclidean")}
                className={`option-btn ${algo1 === "astar_euclidean" ? "selected" : ""}`}>
                A* (Euclidean + Diag)
              </button>
            </div>
          </section>
        ) : (
          <section className="section">
            <h2 className="section-label">Select Algorithms</h2>

            {/* Algorithm 1 */}
            <div className="button-group">
              <button onClick={() => setAlgo1("bfs")}
                className={`option-btn ${algo1 === "bfs" ? "selected" : ""}`}>
                BFS
              </button>

              <button onClick={() => setAlgo1("dfs")}
                className={`option-btn ${algo1 === "dfs" ? "selected" : ""}`}>
                DFS
              </button>

              <button onClick={() => setAlgo1("flood")}
                className={`option-btn ${algo1 === "flood" ? "selected" : ""}`}>
                Flood Fill
              </button>

              <button onClick={() => setAlgo1("astar_manhattan")}
                className={`option-btn ${algo1 === "astar_manhattan" ? "selected" : ""}`}>
                A* (Manhattan)
              </button>

              <button onClick={() => setAlgo1("astar_euclidean")}
                className={`option-btn ${algo1 === "astar_euclidean" ? "selected" : ""}`}>
                A* (Euclidean + Diag)
              </button>
            </div>

            {/* Algorithm 2 */}
            <div className="button-group" style={{ marginTop: "10px" }}>
              <button onClick={() => setAlgo2("bfs")}
                className={`option-btn ${algo2 === "bfs" ? "selected" : ""}`}>
                BFS
              </button>

              <button onClick={() => setAlgo2("dfs")}
                className={`option-btn ${algo2 === "dfs" ? "selected" : ""}`}>
                DFS
              </button>

              <button onClick={() => setAlgo2("flood")}
                className={`option-btn ${algo2 === "flood" ? "selected" : ""}`}>
                Flood Fill
              </button>

              <button onClick={() => setAlgo2("astar_manhattan")}
                className={`option-btn ${algo2 === "astar_manhattan" ? "selected" : ""}`}>
                A* (Manhattan)
              </button>

              <button onClick={() => setAlgo2("astar_euclidean")}
                className={`option-btn ${algo2 === "astar_euclidean" ? "selected" : ""}`}>
                A* (Euclidean + Diag)
              </button>
            </div>
          </section>
        )}

        <button onClick={handleStart} className="start-btn">
          {mode === "single" ? "Start Visualization" : "Compare Algorithms"}
        </button>

      </div>
    </div>
  );
}

export default HomePage;
