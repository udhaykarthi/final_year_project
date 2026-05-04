import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { clearSession, getUser, isLoggedIn } from './auth';

export default function NavBar() {
  const navigate = useNavigate();
  const user = getUser();
  const loggedIn = isLoggedIn();

  const onLogout = () => {
    clearSession();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">◇</span>
          <span className="brand-text">Rov-E</span>
        </Link>

        <div className="nav-links">
          {loggedIn ? (
            <>
              <NavLink to="/dashboard" className="nav-link">Dashboard</NavLink>
              <NavLink to="/live" className="nav-link">Live</NavLink>
              <NavLink to="/history" className="nav-link">History</NavLink>
              <NavLink to="/settings" className="nav-link">Settings</NavLink>
              <span className="nav-user">{user?.email}</span>
              <button className="btn btn-ghost" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="nav-link">Login</NavLink>
              <NavLink to="/register" className="btn btn-primary">Sign up</NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

