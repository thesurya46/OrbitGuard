import React, { useState } from "react";
import ControlsBar from "./ControlsBar.jsx";
import StatCards from "./StatCards.jsx";
import RiskTable from "./RiskTable.jsx";
import OrbitView from "./OrbitView.jsx";
import { runConjunctionPipeline } from "../api.js";

const DEFAULT_SETTINGS = {
  group: "stations",
  thresholdKm: 25,
  windowHours: 72,
  stepSeconds: 60,
  useSampleData: true, // default to sample data so the dashboard works offline out of the box
};

export default function Dashboard() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [result, setResult] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runConjunctionPipeline(settings);
      setResult(data);
      setSelectedIndex(0);
    } catch (err) {
      setError(err.message || "Failed to run the screening pipeline.");
    } finally {
      setLoading(false);
    }
  };

  const selectedEvent = result?.events?.[selectedIndex] ?? null;

  return (
    <>
      <ControlsBar
        settings={settings}
        onChange={setSettings}
        onRun={handleRun}
        loading={loading}
      />

      {error && <div className="error-banner">{error}</div>}

      <StatCards result={result} />

      <div className="main-grid">
        <div className="panel">
          <h2>Ranked Conjunction Risk</h2>
          <RiskTable
            events={result?.events ?? []}
            selectedIndex={selectedIndex}
            onSelect={setSelectedIndex}
          />
        </div>

        <div className="panel">
          <h2>Orbit View</h2>
          <OrbitView event={selectedEvent} />
        </div>
      </div>
    </>
  );
}
