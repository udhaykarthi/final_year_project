import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from './auth';

function Stat({ label, value, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={accent ? { color: accent } : null}>
        {value}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, h, a] = await Promise.all([
          api('/dashboard/stats'),
          api('/history?limit=5'),
          api('/alerts?limit=5'),
        ]);
        setStats(s);
        setRecent(h.items || []);
        setAlerts(a.items || []);
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
          <h1>Dashboard</h1>
          <p className="muted">Your scene analyses and alert activity.</p>
        </div>
        <Link to="/live" className="btn btn-primary">Go to Live ▶</Link>
      </div>

      {err && <p className="error">{err}</p>}
      {loading ? (
        <p className="muted">Loading…</p>
      ) : (
        <>
          <div className="stats-grid">
            <Stat label="Total analyses" value={stats?.total ?? 0} />
            <Stat label="High-risk events" value={stats?.high_risk ?? 0} accent="#e07b00" />
            <Stat label="Alerts logged" value={stats?.alerts ?? 0} accent="#c0392b" />
            <Stat label="Avg risk score" value={stats?.avg_risk ?? 0} />
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-header">
                <h3>Recent analyses</h3>
                <Link to="/history" className="muted small">View all →</Link>
              </div>
              {recent.length === 0 ? (
                <p className="muted">No analyses yet. Run one from the Live page.</p>
              ) : (
                <ul className="list">
                  {recent.map((r) => (
                    <li key={r.id} className="list-row">
                      <span className={`pill pill-risk-${riskBucket(r.risk_score)}`}>
                        {r.risk_score}/10
                      </span>
                      <div className="list-main">
                        <div className="list-title">
                          {r.location || 'unknown'} •{' '}
                          <span className="muted small">
                            {fmtTime(r.timestamp)}
                          </span>
                        </div>
                        <div className="muted small">
                          {(r.objects || []).slice(0, 6).join(', ') || 'no objects'}
                        </div>
                      </div>
                      <Link to={`/history`} className="muted small">→</Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h3>Recent alerts</h3>
              </div>
              {alerts.length === 0 ? (
                <p className="muted">No alerts dispatched yet.</p>
              ) : (
                <ul className="list">
                  {alerts.map((a) => (
                    <li key={a.id} className="list-row">
                      <span className="pill pill-warn">⚠</span>
                      <div className="list-main">
                        <div className="list-title">{a.alert_type}</div>
                        <div className="muted small">
                          Risk {a.risk_score}/10 • {fmtTime(a.timestamp)}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function riskBucket(s) {
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

