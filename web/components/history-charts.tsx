"use client";

import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Provenance } from "@/components/provenance";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import type { HistoryResponse } from "@/lib/types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const AXIS = { fontSize: 12, fill: "var(--muted)" };

function Chart({ title, caption, children, ariaLabel }: { title: string; caption: string; children: React.ReactElement; ariaLabel: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <Provenance kind="HISTORIC" />
      </CardHeader>
      <CardBody>
        <div role="img" aria-label={ariaLabel} className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {children}
          </ResponsiveContainer>
        </div>
        <p className="mt-2 text-xs text-muted">{caption}</p>
      </CardBody>
    </Card>
  );
}

export function HistoryCharts({ history }: { history: HistoryResponse }) {
  const w = history.weather;
  const years = w.years.map((y) => ({
    year: y,
    "Days 105°F+": w.per_year[y].days_ge_105f,
    "Days 110°F+": w.per_year[y].days_ge_110f,
    "Nights 32°F−": w.per_year[y].nights_le_32f,
    "Nights 28°F−": w.per_year[y].nights_le_28f,
    "Monsoon rain (in)": w.per_year[y].monsoon_precip_in,
  }));
  const normals = w.monthly_normals.map((m) => ({ month: MONTHS[m.month - 1], "Avg high": m.mean_max_f, "Avg low": m.mean_min_f, "Rain (in)": m.mean_precip_in }));
  const storms = Object.entries(history.storm_events.summary.by_type)
    .slice(0, 7)
    .map(([type, count]) => ({ type, count }));
  const tick = { ...AXIS };
  const tip = { contentStyle: { background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 8, color: "var(--ink)" } };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Chart title="Hot days per year" caption={`${w.source}. Reanalysis grid values, not a weather-station record.`} ariaLabel="Bar chart of days at or above 105 and 110 degrees per year">
        <BarChart data={years}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="year" tick={tick} />
          <YAxis tick={tick} allowDecimals={false} />
          <Tooltip {...tip} />
          <Legend />
          <Bar dataKey="Days 105°F+" fill="var(--amber)" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Days 110°F+" fill="var(--clay)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </Chart>
      <Chart title="Freeze nights per year" caption="Nights at or below 32°F and 28°F." ariaLabel="Bar chart of freezing nights per year">
        <BarChart data={years}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="year" tick={tick} />
          <YAxis tick={tick} allowDecimals={false} />
          <Tooltip {...tip} />
          <Legend />
          <Bar dataKey="Nights 32°F−" fill="var(--accent)" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Nights 28°F−" fill="var(--accent-strong)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </Chart>
      <Chart title="Typical month" caption={`${w.normals_period} monthly averages: temperatures and rain.`} ariaLabel="Line chart of average monthly high and low temperatures">
        <LineChart data={normals}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="month" tick={tick} />
          <YAxis tick={tick} unit="°" />
          <Tooltip {...tip} />
          <Legend />
          <Line type="monotone" dataKey="Avg high" stroke="var(--clay)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Avg low" stroke="var(--accent)" strokeWidth={2} dot={false} />
        </LineChart>
      </Chart>
      <Chart title={`Storm events, ${history.storm_events.county}`} caption="NOAA Storm Events, 2016–2025 (county and forecast-zone records). Event counts, not claims." ariaLabel="Bar chart of storm event counts by type">
        <BarChart data={storms} layout="vertical" margin={{ left: 24 }}>
          <CartesianGrid stroke="var(--line)" horizontal={false} />
          <XAxis type="number" tick={tick} />
          <YAxis type="category" dataKey="type" tick={tick} width={110} />
          <Tooltip {...tip} />
          <Bar dataKey="count" fill="var(--accent-strong)" radius={[0, 4, 4, 0]} />
        </BarChart>
      </Chart>
    </div>
  );
}
