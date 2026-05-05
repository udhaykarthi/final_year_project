import React, { useEffect, useRef, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { api, API_BASE } from './auth';
import './App.css';

const STORAGE_KEY = 'rove:lastResult';

function riskColor(score) {
  if (score >= 8) return '#c0392b';
  if (score >= 5) return '#e07b00';
  if (score >= 2) return '#d4a300';
  return '#2e7d32';
}

// Fetch a remote image and convert it to a base64 data URL so we can persist
// it in localStorage and display it without needing the backend afterwards.
async function urlToDataUrl(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise((resolve) => {
      const fr = new FileReader();
      fr.onloadend = () => resolve(fr.result);
      fr.onerror = () => resolve(null);
      fr.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

function persistResult(result) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
  } catch {
    // Quota exceeded -> drop embedded images and retry.
    try {
      const { snapshot_data, annotated_data, ...rest } = result;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(rest));
    } catch {}
  }
}

function loadCachedResult() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function Results() {
  const { state } = useLocation();
  const initialResult = state?.result || null;
  const pending = !!state?.pending && !initialResult;

  const [result, setResult] = useState(initialResult);
  const [loading, setLoading] = useState(pending);
  const [error, setError] = useState(null);
  const [showBoxes, setShowBoxes] = useState(true);
  const startedRef = useRef(false);

  // Run analysis on mount when navigated with `pending` flag
  useEffect(() => {
    if (!pending || startedRef.current) return;
    startedRef.current = true;
    (async () => {
      try {
        const data = await api('/analyze', { method: 'POST' });
        data.__apiBase = API_BASE;
        const snapUrl = data.snapshot_url ? `${API_BASE}${data.snapshot_url}` : null;
        const annUrl = data.annotated_snapshot_url
          ? `${API_BASE}${data.annotated_snapshot_url}`
          : null;
        const [snapData, annData] = await Promise.all([
          snapUrl ? urlToDataUrl(snapUrl) : Promise.resolve(null),
          annUrl ? urlToDataUrl(annUrl) : Promise.resolve(null),
        ]);
        if (snapData) data.snapshot_data = snapData;
        if (annData) data.annotated_data = annData;
        persistResult(data);
        setResult(data);
      } catch (e) {
        setError(e.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [pending]);

  // Fallback: load cached result when arriving without state
  useEffect(() => {
    if (result || loading) return;
    const cached = loadCachedResult();
    if (cached) setResult(cached);
  }, [result, loading]);

  if (loading) {
    return (
      <div className="page">
        <div className="card center-text loading-card">
          <div className="spinner" />
          <h2>Analyzing scene…</h2>
          <p className="muted">
            Capturing frame, running YOLO detection and Qwen2-VL reasoning.
            This usually takes a few seconds.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="card">
          <h2>Detection failed</h2>
          <p className="error">{error}</p>
          <Link className="btn btn-primary" to="/live">← Back to Live</Link>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="page">
        <div className="card">
          <h2>No result data</h2>
          <Link className="btn btn-primary" to="/live">← Back to Live</Link>
        </div>
      </div>
    );
  }

  const apiBase = result.__apiBase || API_BASE || '';
  const snapshot =
    result.snapshot_data ||
    (result.snapshot_url ? `${apiBase}${result.snapshot_url}` : null);
  const annotated =
    result.annotated_data ||
    (result.annotated_snapshot_url
      ? `${apiBase}${result.annotated_snapshot_url}`
      : null);
  const displayImage = (showBoxes && annotated) ? annotated : snapshot;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Detection result</h1>
          <p className="muted">{result.timestamp} • {result.location}</p>
        </div>
        <Link to="/live" className="btn btn-ghost">← Run again</Link>
      </div>

      {result.risk_score >= 5 && (
        <div className="banner banner-info">
          ⚠ High-risk event recorded — this scene has been logged to your alert history.
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3>Snapshot</h3>
            {result.bounding_boxes?.length > 0 && (
              <label className="muted small">
                <input
                  type="checkbox"
                  checked={showBoxes}
                  onChange={(e) => setShowBoxes(e.target.checked)}
                />{' '}
                bounding boxes
              </label>
            )}
          </div>
          {displayImage ? (
            <img className="snapshot" src={displayImage} alt="captured" />
          ) : (
            <p className="muted">No snapshot available.</p>
          )}

          {result.bounding_boxes?.length > 0 && (
            <div className="bbox-legend">
              {result.bounding_boxes.map((b, i) => (
                <div key={i} className="bbox-item">
                  <span className="bbox-color-dot" style={{ background: b.color }} />
                  <span>{b.label}</span>
                  <span className="muted small">{(b.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card center-text">
          <h3>Risk score</h3>
          <div
            className="risk-circle"
            style={{ background: riskColor(result.risk_score) }}
          >
            {result.risk_score}<span className="small">/10</span>
          </div>
          <h4>Reasons</h4>
          {result.risk_reasons?.length === 0 ? (
            <p className="muted">No risk reasons.</p>
          ) : (
            <ul className="left">
              {result.risk_reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          )}
        </div>

        <div className="card">
          <h3>Alerts</h3>
          {result.alerts?.length === 0 ? (
            <p className="ok">✓ No threats detected</p>
          ) : (
            <ul className="alerts">
              {result.alerts.map((a, i) => <li key={i}>⚠ {a}</li>)}
            </ul>
          )}
        </div>

        <div className="card">
          <h3>Anomalies</h3>
          {result.anomalies?.length > 0 ? (
            <ul>{result.anomalies.map((a, i) => <li key={i}>🔍 {a}</li>)}</ul>
          ) : (
            <p className="ok">✓ No anomalies detected</p>
          )}
          {result.anomaly_stats && (
            <p className="muted small">
              Observations: {result.anomaly_stats.observations} •
              Avg risk: {result.anomaly_stats.avg_risk?.toFixed(1) || 0}
            </p>
          )}
        </div>

        <div className="card">
          <h3>Object counts</h3>
          {Object.keys(result.object_counts || {}).length === 0 ? (
            <p className="muted">None.</p>
          ) : (
            <ul>
              {Object.entries(result.object_counts).map(([k, v]) => (
                <li key={k}><b>{k}</b> × {v}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="card wide">
          <h3>Vision description</h3>
          {result.description ? (
            <pre className="description">{result.description}</pre>
          ) : (
            <p className="muted">
              {result.vision_status && result.vision_status !== 'ok'
                ? `Vision model unavailable for this frame (${result.vision_status}). Try Run Detection again.`
                : 'No description was produced for this frame.'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
