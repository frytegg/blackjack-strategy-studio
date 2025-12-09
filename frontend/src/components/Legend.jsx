// frontend/src/components/Legend.jsx

import React from "react";

function Legend() {
  return (
    <div className="legend-box">
      <strong>Légende :</strong>{" "}
      <span className="legend-item">
        <span className="legend-color legend-H" /> H = Hit
      </span>
      <span className="legend-item">
        <span className="legend-color legend-S" /> S = Stand
      </span>
      <span className="legend-item">
        <span className="legend-color legend-D" /> D = Double
      </span>
      <span className="legend-item">
        <span className="legend-color legend-P" /> P = Split
      </span>
      <span className="legend-item">
        <span className="legend-color legend-R" /> R = Surrender
      </span>
    </div>
  );
}

export default Legend;
