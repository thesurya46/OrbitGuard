import React from "react";

function Stat({ value, label }) {
  return (
    <div className="stat-card">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

export default function StatCards({ result }) {
  if (!result) {
    return null;
  }

  const critical = result.events.filter((e) => e.urgency === "Critical").length;
  const topRisk = result.events[0]?.risk_score ?? 0;

  return (
    <div className="stat-grid">
      <Stat value={result.objects_tracked} label="Objects tracked" />
      <Stat value={result.events.length} label="Flagged conjunctions" />
      <Stat value={critical} label="Critical (< 6h)" />
      <Stat value={`${topRisk.toFixed(0)}/100`} label="Highest risk score" />
    </div>
  );
}
