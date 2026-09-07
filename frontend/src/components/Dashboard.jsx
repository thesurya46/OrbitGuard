import React, { useState } from "react";
import ControlsBar from "./ControlsBar.jsx";
import StatCards from "./StatCards.jsx";
import RiskTable from "./RiskTable.jsx";
import OrbitView from "./OrbitView.jsx";
import RiskAnalytics from "./RiskAnalytics.jsx";
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
  const [urgencyFilter, setUrgencyFilter] = useState("All");
  const [search, setSearch] = useState("");

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

  const filteredEvents = (result?.events ?? []).filter((event) => {
    const matchesUrgency = urgencyFilter === "All" || event.urgency === urgencyFilter;
    const query = search.trim().toLowerCase();
    const matchesSearch = !query || `${event.object_a} ${event.object_b}`.toLowerCase().includes(query);
    return matchesUrgency && matchesSearch;
  });
  const selectedEvent = filteredEvents[selectedIndex] ?? null;

  const exportCsv = () => {
    const headers = ["Object A", "Object B", "Miss distance (km)", "Relative velocity (km/s)", "Time to CA (hours)", "Risk score", "Urgency"];
    const rows = filteredEvents.map((event) => [
      event.object_a,
      event.object_b,
      event.miss_distance_km,
      event.relative_velocity_kmps,
      event.time_to_closest_approach_hours,
      event.risk_score,
      event.urgency,
    ]);
    const csv = [headers, ...rows]
      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))
      .join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    link.download = "orbitguard-screening.csv";
    link.click();
    URL.revokeObjectURL(link.href);
  };

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

      {result && (
        <section className="panel analytics-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Decision support</span>
              <h2>Risk overview</h2>
            </div>
            <span className="run-meta">Updated {new Date(result.generated_at_iso).toLocaleTimeString()}</span>
          </div>
          <RiskAnalytics events={result.events} />
        </section>
      )}

      <div className="main-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Prioritized events</span>
              <h2>Ranked Conjunction Risk</h2>
            </div>
            <button className="quiet-button" onClick={exportCsv} disabled={!filteredEvents.length}>
              Export CSV
            </button>
          </div>
          <div className="table-tools">
            <input
              aria-label="Search conjunctions"
              placeholder="Search objects..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <select aria-label="Filter by urgency" value={urgencyFilter} onChange={(event) => setUrgencyFilter(event.target.value)}>
              <option>All</option>
              <option>Critical</option>
              <option>High</option>
              <option>Moderate</option>
              <option>Low</option>
            </select>
            <span className="result-count">{filteredEvents.length} of {result?.events?.length ?? 0}</span>
          </div>
          <RiskTable
            events={filteredEvents}
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
