"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { SUBMISSION_STATUS_LABELS, type SubmissionStatus } from "@/lib/api/types";

const COLORS: Record<SubmissionStatus, string> = {
  draft: "#a1a1aa",
  in_progress: "#3b82f6",
  observed: "#f59e0b",
  approved: "#10b981",
  rejected: "#ef4444",
};

export function StatusDonut({
  data,
}: {
  data: { status: string; count: number }[];
}) {
  const chartData = data
    .filter((d) => d.count > 0)
    .map((d) => ({
      name: SUBMISSION_STATUS_LABELS[d.status as SubmissionStatus] ?? d.status,
      value: d.count,
      raw: d.status,
    }));

  if (chartData.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-zinc-500">
        Sin avances registrados aún.
      </p>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={chartData}
            innerRadius={50}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
          >
            {chartData.map((d) => (
              <Cell
                key={d.raw}
                fill={COLORS[d.raw as SubmissionStatus] ?? "#71717a"}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={32} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
