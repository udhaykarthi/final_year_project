import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
const WS_BASE = API_BASE.replace('http://', 'ws://').replace('https://', 'ws://');

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const navigate = useNavigate();

  // WebSocket connection for real-time alerts
  useEffect(() => {
    let ws = null;
    try {
      ws = new WebSocket(`${WS_BASE}/ws/alerts`);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'alert') {
            // Add live alert notification
            setLiveAlerts(prev => [
              { id: Date.now(), ...data },
              ...prev.slice(0, 4) // Keep last 5 alerts
            ]);
            // Auto-remove after 5 seconds
            setTimeout(() => {
              setLiveAlerts(prev => prev.filter(a => a.id !== data.timestamp));
            }, 5000);
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setWsConnected(false);
      };

      ws.onerror = (err) => {
        console.error('[WebSocket] Error:', err);
        setWsConnected(false);
      };

    } catch (e) {
      console.error('WebSocket connection failed:', e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const runDetection = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/analyze`, { method: 'POST' });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`HTTP ${res.status}: ${t}`);
      }
      const data = await res.json();
      data.__apiBase = API_BASE;
      navigate('/results', { state: { result: data } });
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🛡️ Vision Safety System</h1>
        <p className="subtitle">
          Real-time webcam scene analysis powered by YOLO + Qwen-VL
        </p>

        {/* Connection status */}
        <div className="connection-status">
          <span className={`status-dot ${wsConnected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">{wsConnected ? 'Live' : 'Offline'}</span>
        </div>

        {/* Live alert notifications */}
        {liveAlerts.length > 0 && (
          <div className="live-alerts">
            {liveAlerts.map(alert => (
              <div key={alert.id} className="live-alert-item">
                ⚠️ {alert.alert_type} (Risk: {alert.risk_score}/10)
              </div>
            ))}
          </div>
        )}

        <div className="preview-card">
          <img
            className="preview"
            src={`${API_BASE}/video_feed`}
            alt="Live camera feed"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </div>

        <button
          className="run-btn"
          onClick={runDetection}
          disabled={loading}
        >
          {loading ? '🔍 Analyzing...' : '▶ Run Detection'}
        </button>

        {error && <p className="error">⚠ {error}</p>}

        <p className="hint">
          Make sure the API is running:&nbsp;
          <code>python api/server.py</code>
        </p>
      </header>
    </div>
  );
}

export default App;
