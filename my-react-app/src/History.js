import React, { useEffect, useState } from 'react';
import { api, API_BASE } from './auth';

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await api('/history?limit=100');
        setItems(data.items || []);
      } catch (e) {
        setErr(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>History</h1>
          <p className="muted">All saved analyses for your account.</p>
        </div>
      </div>

      {err && <p className="error">{err}</p>}
      {loading ? (
        <p className="muted">Loading…</p>
      ) : items.length === 0 ? (
        <p className="muted">No analyses yet.</p>
      ) : (
        <div className="grid-2">
          <div className="card">
            <h3>Saved scenes ({items.length})</h3>
            <ul className="list">
              {items.map((r) => (
                <li
                  key={r.id}
                  className={`list-row clickable ${selected?.id === r.id ? 'active' : ''}`}
                  onClick={() => setSelected(r)}
                >
                  <span className={`pill pill-risk-${bucket(r.risk_score)}`}>
                    {r.risk_score}
                  </span>
                  <div className="list-main">
                    <div className="list-title">{r.location || 'unknown'}</div>
                    <div className="muted small">{fmtTime(r.timestamp)}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h3>Details</h3>
            {!selected ? (
              <p className="muted">Select a scene to view details.</p>
            ) : (
              <div>
                {selected.image_filename && (
                  <img
                    className="snapshot"
                    src={`${API_BASE}/annotated/annotated_${selected.image_filename}`}
                    alt="snapshot"
                    onError={(e) => {
                      e.target.src = `${API_BASE}/snapshot/${selected.image_filename}`;
                    }}
                  />
                )}
                <p className="meta">
                  <b>Time:</b> {fmtTime(selected.timestamp)}<br />
                  <b>Location:</b> {selected.location}<br />
                  <b>Risk:</b> {selected.risk_score}/10
                </p>

                <h4>Alerts</h4>
                {(selected.alerts || []).length === 0 ? (
                  <p className="muted">None</p>
                ) : (
                  <ul>{selected.alerts.map((a, i) => <li key={i}>⚠ {a}</li>)}</ul>
                )}

                <h4>Objects</h4>
                <p>{(selected.objects || []).join(', ') || '—'}</p>

                <h4>Description</h4>
                <pre className="description">{selected.description || '—'}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function bucket(s) {
  if (s >= 8) return 'crit';
  if (s >= 5) return 'high';
  if (s >= 2) return 'mid';
  return 'low';
}
function fmtTime(t) {
  if (!t) return '';
  try {
    return new Date(t).toLocaleString();
  } catch {
    return String(t);
  }
}

