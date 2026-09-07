import React from "react";

const URGENCY_ORDER = ["Critical", "High", "Moderate", "Low"];

export default function RiskAnalytics({ events }) {
  const counts = URGENCY_ORDER.map((urgency) => ({
    urgency,
    count: events.filter((event) => event.urgency === urgency).length,
  }));
  const maxCount = Math.max(...counts.map(({ count }) => count), 1);
  const averageRisk = events.length
    ? events.reduce((total, event) => total + event.risk_score, 0) / events.length
    : 0;
  const nearest = events.length
    ? Math.min(...events.map((event) => event.miss_distance_km))
    : 0;

  return (
    <div className="analytics-grid">
      <div className="analytics-summary">
        <span className="eyebrow">Screening profile</span>
        <strong>{averageRisk.toFixed(0)}<small>/100</small></strong>
        <span>Average risk score</span>
      </div>
      <div className="analytics-summary">
        <span className="eyebrow">Closest approach</span>
        <strong>{nearest.toFixed(2)}<small> km</small></strong>
        <span>Shortest miss distance</span>
      </div>
      <div className="urgency-chart" aria-label="Conjunctions by urgency">
        {counts.map(({ urgency, count }) => (
          <div className="urgency-row" key={urgency}>
            <span className={`urgency-key urgency-${urgency}`}>{urgency}</span>
            <span className="chart-track">
              <span
                className={`chart-fill urgency-fill-${urgency}`}
                style={{ width: `${(count / maxCount) * 100}%` }}
              />
            </span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}