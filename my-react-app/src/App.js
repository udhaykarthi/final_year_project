import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, API_BASE } from './auth';

const WS_BASE = API_BASE.replace(/^http/, 'ws');

export default function App() {
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveAlerts, setLiveAlerts] = useState([]);
  // Cache-buster used to force the MJPEG <img> to (re)connect on demand.
  const [streamKey, setStreamKey] = useState(() => Date.now());
  const [streamOk, setStreamOk] = useState(true);
  const navigate = useNavigate();
  const imgRef = useRef(null);

  // ----- WebSocket alerts -----
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(`${WS_BASE}/ws/alerts`);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'alert') {
            const id = Date.now() + Math.random();
            setLiveAlerts((prev) => [{ id, ...data }, ...prev.slice(0, 4)]);
            setTimeout(() => {
              setLiveAlerts((prev) => prev.filter((a) => a.id !== id));
            }, 6000);
          }
        } catch {}
      };
    } catch {}
    return () => ws && ws.close();
  }, []);

  // ----- Live stream auto-recovery -----
  // 1. Restart stream whenever the page becomes visible again (tab focus / route change).
  useEffect(() => {
    const restart = () => setStreamKey(Date.now());
    window.addEventListener('focus', restart);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') restart();
    });
    return () => {
      window.removeEventListener('focus', restart);
    };
  }, []);

  // 2. If the stream errors, retry every 2 seconds until it loads.
  useEffect(() => {
    if (streamOk) return;
    const t = setInterval(() => setStreamKey(Date.now()), 2000);
    return () => clearInterval(t);
  }, [streamOk]);

  const reloadStream = () => {
    setStreamOk(true);
    setStreamKey(Date.now());
  };

  // ----- Detection -----
  // Don't block the live page. Navigate to /results immediately and let that
  // page run the analysis + show its own loading state.
  const runDetection = () => {
    setError(null);
    navigate('/results', { state: { pending: true, startedAt: Date.now() } });
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Live camera</h1>
          <p className="muted">
            Real-time webcam scene analysis powered by YOLO + Qwen2-VL.
          </p>
        </div>
        <div className={`status-pill ${wsConnected ? 'on' : 'off'}`}>
          <span className="dot" />
          {wsConnected ? 'Live alerts on' : 'Alerts offline'}
        </div>
      </div>

      {liveAlerts.length > 0 && (
        <div className="live-alerts">
          {liveAlerts.map((a) => (
            <div key={a.id} className="live-alert-item">
              ⚠ {a.alert_type} — risk {a.risk_score}/10
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="preview-card">
          <img
            ref={imgRef}
            key={streamKey}
            className="preview"
            src={`${API_BASE}/video_feed?t=${streamKey}`}
            alt="Live camera feed"
            onLoad={() => setStreamOk(true)}
            onError={() => setStreamOk(false)}
          />
          {!streamOk && (
            <div className="preview-overlay">
              <div>Reconnecting to camera…</div>
              <button className="btn btn-ghost small" onClick={reloadStream}>
                Retry now
              </button>
            </div>
          )}
        </div>

        <div className="actions-row">
          <button
            className="btn btn-primary big"
            onClick={runDetection}
          >
            ▶ Run detection
          </button>
          <button className="btn btn-ghost" onClick={reloadStream}>
            ↻ Reconnect feed
          </button>
          {error && <p className="error">{error}</p>}
        </div>

        <p className="muted small">
          The live feed automatically reconnects when you return to this page
          or after a detection finishes.
        </p>
      </div>
    </div>
  );
}
