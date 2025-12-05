import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import Visualizer from "./pages/Visualizer";
import CompareVisualizer from "./pages/CompareVisualizer";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/visualize" element={<Visualizer />} />
      <Route path="/compare" element={<CompareVisualizer />} />
    </Routes>
  );
}

export default App;
