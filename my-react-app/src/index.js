import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';
import './App.css';

import App from './App';
import Results from './Results';
import Login from './Login';
import Register from './Register';
import Dashboard from './Dashboard';
import History from './History';
import Settings from './Settings';
import NavBar from './NavBar';
import ProtectedRoute from './ProtectedRoute';
import { isLoggedIn } from './auth';
import reportWebVitals from './reportWebVitals';

function Layout({ children }) {
  return (
    <>
      <NavBar />
      <main className="app-main">{children}</main>
    </>
  );
}

function HomeRedirect() {
  return <Navigate to={isLoggedIn() ? '/dashboard' : '/login'} replace />;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            path="/dashboard"
            element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
          />
          <Route
            path="/live"
            element={<ProtectedRoute><App /></ProtectedRoute>}
          />
          <Route
            path="/results"
            element={<ProtectedRoute><Results /></ProtectedRoute>}
          />
          <Route
            path="/history"
            element={<ProtectedRoute><History /></ProtectedRoute>}
          />
          <Route
            path="/settings"
            element={<ProtectedRoute><Settings /></ProtectedRoute>}
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>
);

reportWebVitals();
