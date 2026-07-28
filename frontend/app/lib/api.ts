const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type MetricsSummary = {
  timestamp: string;
  total_flights_today: number;
  avg_dep_delay_minutes: number;
  cancellation_rate_pct: number;
  top_congested_hub: string | null;
};

export async function getSummary(): Promise<MetricsSummary> {
  const res = await fetch(`${API_URL}/api/v1/metrics/summary`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch summary: ${res.status}`);
  return res.json();
}

export type FlightPath = {
  origin_lat: number;
  origin_lon: number;
  dest_lat: number;
  dest_lon: number;
  delayed: boolean;
};

export async function getFlightPaths(): Promise<{ flight_paths: FlightPath[] }> {
  const res = await fetch(`${API_URL}/api/v1/metrics/flight-paths`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch flight paths: ${res.status}`);
  return res.json();
}
