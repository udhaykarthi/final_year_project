import React, { useEffect, useState } from 'react';
import { api, getUser, setSession, getToken } from './auth';

export default function Settings() {
  const [user, setUser] = useState(getUser());
  const [err, setErr] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const me = await api('/auth/me');
        setUser(me);
        setSession(getToken(), me);
      } catch (e) {
        setErr(e.message);
      }
    })();
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="muted">Your account information.</p>
        </div>
      </div>

      {err && <p className="error">{err}</p>}

      <div className="card">
        <h3>Account</h3>
        <p><b>Name:</b> {user?.name || '—'}</p>
        <p><b>Email:</b> {user?.email || '—'}</p>
        <p className="muted small">
          Signed-in sessions are stored locally in your browser. Click
          <i> Logout </i> in the top bar to end this session.
        </p>
      </div>
    </div>
  );
}
