import React from 'react';
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

  return (
    <div className="App results-page">
      <div className="results-container">
        <div className="results-header">
          <h1>🧠 Detection Result</h1>
          <Link to="/" className="back-link">← Run again</Link>
        </div>

        <div className="grid">
          <div className="card">
            <h3>Snapshot</h3>
            {snapshot ? (
              <img className="snapshot" src={snapshot} alt="captured frame" />
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

          <div className="card">
            <h3>Detected Objects</h3>
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

