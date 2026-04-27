import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import './App.css';

function riskColor(score) {
  if (score >= 8) return '#ff3b30';
  if (score >= 5) return '#ff9500';
  if (score >= 2) return '#ffcc00';
  return '#34c759';
}

export default function Results() {
  const { state } = useLocation();
  const result = state?.result;
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);

  if (!result) {
    return (
      <div className="App">
        <header className="App-header">
          <h2>No result data</h2>
          <Link className="run-btn" to="/">← Back</Link>
        </header>
      </div>
    );
  }

  const apiBase = result.__apiBase || '';
  const snapshot = result.snapshot_url ? `${apiBase}${result.snapshot_url}` : null;
  const annotatedSnapshot = result.annotated_snapshot_url
    ? `${apiBase}${result.annotated_snapshot_url}`
    : null;

  // Use annotated image if available, otherwise fall back to regular snapshot
  const displayImage = annotatedSnapshot || snapshot;

  return (
    <div className="App results-page">
      <div className="results-container">
        <div className="results-header">
          <h1>🧠 Detection Result</h1>
          <Link to="/" className="back-link">← Run again</Link>
        </div>

        {/* Bounding box toggle */}
        {result.bounding_boxes && result.bounding_boxes.length > 0 && (
          <div className="bbox-toggle">
            <label>
              <input
                type="checkbox"
                checked={showBoundingBoxes}
                onChange={(e) => setShowBoundingBoxes(e.target.checked)}
              />
              {' '}Show Bounding Boxes
            </label>
          </div>
        )}

        <div className="grid">
          <div className="card">
            <h3>Snapshot</h3>
            {displayImage ? (
              <>
                <img
                  className="snapshot"
                  src={showBoundingBoxes && annotatedSnapshot ? annotatedSnapshot : snapshot}
                  alt="captured frame"
                />
                {result.bounding_boxes && result.bounding_boxes.length > 0 && (
                  <div className="bbox-legend">
                    <h4>Detected Objects</h4>
                    <div className="bbox-items">
                      {result.bounding_boxes.map((box, idx) => (
                        <div key={idx} className="bbox-item">
                          <span
                            className="bbox-color-dot"
                            style={{ backgroundColor: box.color }}
                          ></span>
                          <span className="bbox-label">{box.label}</span>
                          <span className="bbox-confidence">{(box.confidence * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p>No snapshot available.</p>
            )}
            <p className="meta">
              <b>Time:</b> {result.timestamp}<br />
              <b>Location:</b> {result.location}
            </p>
          </div>

          <div className="card">
            <h3>Risk Score</h3>
            <div
              className="risk-circle"
              style={{ background: riskColor(result.risk_score) }}
            >
              {result.risk_score}/10
            </div>
            <h4>Reasons</h4>
            {result.risk_reasons.length === 0 ? (
              <p>No risk reasons.</p>
            ) : (
              <ul>{result.risk_reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
            )}
          </div>

          <div className="card">
            <h3>Alerts</h3>
            {result.alerts.length === 0 ? (
              <p className="ok">✓ No threats detected</p>
            ) : (
              <ul className="alerts">
                {result.alerts.map((a, i) => <li key={i}>⚠ {a}</li>)}
              </ul>
            )}
          </div>

          {/* Anomalies card - new feature */}
          <div className="card">
            <h3>Anomalies</h3>
            {result.anomalies && result.anomalies.length > 0 ? (
              <ul className="anomalies">
                {result.anomalies.map((a, i) => <li key={i}>🔍 {a}</li>)}
              </ul>
            ) : (
              <p className="ok">✓ No anomalies detected</p>
            )}
            {result.anomaly_stats && (
              <div className="anomaly-stats">
                <small>
                  Observations: {result.anomaly_stats.observations} |
                  Avg Risk: {result.anomaly_stats.avg_risk?.toFixed(1) || 0}
                </small>
              </div>
            )}
          </div>

          <div className="card">
            <h3>Object Counts</h3>
            {Object.keys(result.object_counts || {}).length === 0 ? (
              <p>None.</p>
            ) : (
              <ul>
                {Object.entries(result.object_counts).map(([k, v]) => (
                  <li key={k}><b>{k}</b> × {v}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="card wide">
            <h3>Vision Description</h3>
            <pre className="description">
              {result.description || '(vision model disabled)'}
            </pre>
          </div>

          <div className="card wide">
            <h3>Scene History</h3>
            <pre className="history">
              {JSON.stringify(result.history, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

