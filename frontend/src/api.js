/**
 * Thin wrapper around the OrbitGuard backend REST API. Every function
 * returns a parsed JSON payload and throws on a non-2xx response so
 * callers can handle errors with a plain try/catch.
 */

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

export function getHealth() {
  return request("/api/health");
}

export function runConjunctionPipeline({
  group = "stations",
  thresholdKm = 25,
  windowHours = 72,
  stepSeconds = 60,
  useSampleData = false,
  forceRefresh = false,
} = {}) {
  return request("/api/conjunctions/run", {
    method: "POST",
    body: JSON.stringify({
      group,
      threshold_km: thresholdKm,
      window_hours: windowHours,
      step_seconds: stepSeconds,
      use_sample_data: useSampleData,
      force_refresh: forceRefresh,
    }),
  });
}
