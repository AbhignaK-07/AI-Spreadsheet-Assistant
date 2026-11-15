import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { BarChart2, LineChart as LineIcon } from "lucide-react";

const COLORS = ["#4f46e5", "#10b981", "#f43f5e", "#f59e0b", "#06b6d4"];

export default function AnalyticsCharts({ chartData, chartType, onChartTypeChange }) {
  if (!chartData || !chartData.chart_labels?.length) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-slate-500">
        Create a spreadsheet or ask the assistant a question to visualize Bar and Line graphs.
      </div>
    );
  }

  const formattedData = chartData.chart_labels.map((label, idx) => {
    const point = { name: label };
    chartData.chart_datasets.forEach((ds) => {
      point[ds.label] = ds.data[idx] ?? 0;
    });
    return point;
  });

  const formatDollar = (v) =>
    Math.abs(v) >= 1_000_000
      ? `$${(v / 1_000_000).toFixed(1)}M`
      : Math.abs(v) >= 1_000
      ? `$${(v / 1_000).toFixed(0)}k`
      : `$${v}`;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            {chartData.chart_title || "Profit & Loss Analytics"}
          </h3>
          <p className="text-xs text-slate-500">
            Switch between Bar Graph and Line Graph views
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
          <button
            type="button"
            onClick={() => onChartTypeChange("bar")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              chartType === "bar"
                ? "bg-white text-indigo-600 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <BarChart2 className="w-4 h-4" />
            Bar Graph
          </button>
          <button
            type="button"
            onClick={() => onChartTypeChange("line")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
              chartType === "line"
                ? "bg-white text-indigo-600 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <LineIcon className="w-4 h-4" />
            Line Graph
          </button>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "bar" ? (
            <BarChart data={formattedData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={formatDollar} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value) =>
                  new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD",
                  }).format(value)
                }
              />
              <Legend />
              {chartData.chart_datasets.map((ds, idx) => (
                <Bar
                  key={ds.label}
                  dataKey={ds.label}
                  fill={COLORS[idx % COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          ) : (
            <LineChart data={formattedData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={formatDollar} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value) =>
                  new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD",
                  }).format(value)
                }
              />
              <Legend />
              {chartData.chart_datasets.map((ds, idx) => (
                <Line
                  key={ds.label}
                  type="monotone"
                  dataKey={ds.label}
                  stroke={COLORS[idx % COLORS.length]}
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
