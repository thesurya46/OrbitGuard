import React from "react";

const urgencyColor = {
  Critical: "var(--critical)",
  High: "var(--high)",
  Moderate: "var(--moderate)",
  Low: "var(--low)",
};

export default function RiskTable({ events, selectedIndex, onSelect }) {
  if (!events || events.length === 0) {
    return (
      <div className="empty-state">
        No conjunctions flagged yet. Configure the screening parameters
        above and click "Run Screening".
      </div>
    );
  }

  return (
    <table className="risk-table">
      <thead>
        <tr>
          <th>Objects</th>
          <th>Miss dist.</th>
          <th>Rel. velocity</th>
          <th>Time to CA</th>
          <th>Risk</th>
          <th>Urgency</th>
        </tr>
      </thead>
      <tbody>
        {events.map((event, i) => (
          <tr
            key={`${event.norad_id_a}-${event.norad_id_b}-${i}`}
            className={i === selectedIndex ? "selected" : ""}
            onClick={() => onSelect(i)}
          >
            <td>
              {event.object_a}
              <br />
              <span style={{ color: "var(--text-dim)", fontSize: 11 }}>
                vs {event.object_b}
              </span>
            </td>
            <td>{event.miss_distance_km.toFixed(2)} km</td>
            <td>{event.relative_velocity_kmps.toFixed(2)} km/s</td>
            <td>{event.time_to_closest_approach_hours.toFixed(1)} h</td>
            <td>
              <span className="risk-bar-track">
                <span
                  className="risk-bar-fill"
                  style={{
                    width: `${event.risk_score}%`,
                    background: urgencyColor[event.urgency],
                  }}
                />
              </span>
              <span style={{ marginLeft: 8 }}>{event.risk_score.toFixed(0)}</span>
            </td>
            <td>
              <span className={`urgency-badge urgency-${event.urgency}`}>
                {event.urgency}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
