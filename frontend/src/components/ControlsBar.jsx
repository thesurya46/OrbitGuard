import React from "react";

export default function ControlsBar({ settings, onChange, onRun, loading }) {
  const update = (key) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    onChange({ ...settings, [key]: value });
  };

  return (
    <div className="controls-bar">
      <div className="field">
        <label htmlFor="group">TLE group</label>
        <select id="group" value={settings.group} onChange={update("group")}>
          <option value="stations">Stations (ISS &amp; Tiangong vs Debris)</option>
          <option value="active">Active satellites</option>
          <option value="starlink">Starlink</option>
          <option value="debris">Debris</option>
        </select>
      </div>

      <div className="field">
        <label htmlFor="threshold">Threshold (km)</label>
        <input
          id="threshold"
          type="number"
          min="1"
          max="500"
          value={settings.thresholdKm}
          onChange={update("thresholdKm")}
        />
      </div>

      <div className="field">
        <label htmlFor="window">Window (hours)</label>
        <input
          id="window"
          type="number"
          min="1"
          max="240"
          value={settings.windowHours}
          onChange={update("windowHours")}
        />
      </div>

      <div className="field">
        <label htmlFor="step">Step (seconds)</label>
        <input
          id="step"
          type="number"
          min="10"
          max="600"
          value={settings.stepSeconds}
          onChange={update("stepSeconds")}
        />
      </div>

      <div className="field">
        <label htmlFor="sample">
          <input
            id="sample"
            type="checkbox"
            checked={settings.useSampleData}
            onChange={update("useSampleData")}
            style={{ marginRight: 6 }}
          />
          Use offline sample data
        </label>
      </div>

      <button className="run-button" onClick={onRun} disabled={loading}>
        {loading ? "Screening orbits..." : "Run Screening"}
      </button>
    </div>
  );
}
