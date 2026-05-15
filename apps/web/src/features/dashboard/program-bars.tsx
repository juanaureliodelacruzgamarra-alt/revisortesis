"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ProgramGrade } from "@/lib/api/stats";

export function ProgramBars({ data }: { data: ProgramGrade[] }) {
  if (data.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-zinc-500">
        Aún no hay calificaciones IA registradas.
      </p>
    );
  }

  const chartData = data.map((p) => ({
    program: p.program_code,
    grade: Number(p.average_grade.toFixed(2)),
    submissions: p.submissions_count,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
          <XAxis dataKey="program" stroke="#71717a" fontSize={12} />
          <YAxis domain={[0, 20]} stroke="#71717a" fontSize={12} />
          <Tooltip
            formatter={(v, name) =>
              name === "grade"
                ? [`${v} / 20`, "Nota IA promedio"]
                : [String(v), "Avances"]
            }
          />
          <Bar dataKey="grade" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
