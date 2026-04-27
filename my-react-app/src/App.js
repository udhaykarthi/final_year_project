import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

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
