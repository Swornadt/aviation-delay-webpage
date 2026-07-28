"use client";

import { useEffect, useState } from "react";
import { getSummary, MetricsSummary } from "@/lib/api";

export default function KpiTicker() {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSummary()
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="text-red-400 text-sm">Failed to load KPIs: {error}</div>;
  if (!summary) return <div className="text-slate-400 text-sm">Loading KPIs…</div>;

  const cards = [
    { label: "Flights Today", value: summary.total_flights_today },
    { label: "Avg Dep Delay (min)", value: summary.avg_dep_delay_minutes },
    { label: "Cancellation Rate (%)", value: summary.cancellation_rate_pct },
    { label: "Worst Hub", value: summary.top_congested_hub ?? "—" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl bg-slate-900 border border-slate-800 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-400">{c.label}</div>
          <div className="text-2xl font-semibold mt-1">{c.value}</div>
        </div>
      ))}
    </div>
  );
}
