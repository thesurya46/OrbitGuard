import React, { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard.jsx";
import { getHealth } from "./api.js";

export default function App() {
  const [backendOnline, setBackendOnline] = useState(null);

  useEffect(() => {
    getHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>OrbitGuard</h1>
          <div className="tagline">
            Satellite conjunction &amp; collision risk dashboard
          </div>
        </div>
        <div className="status-pill">
          <span
            className={`status-dot ${backendOnline === false ? "offline" : ""}`}
          />
          {backendOnline === null
            ? "Checking backend..."
            : backendOnline
            ? "Backend connected"
            : "Backend unreachable — start the API on :8000"}
        </div>
      </header>

      <Dashboard />
    </div>
  );
}
