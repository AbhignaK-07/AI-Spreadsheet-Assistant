import React, { useState } from "react";
import { Download, ExternalLink, Search, Table, BarChart, Calendar } from "lucide-react";

const money = (v) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(v ?? 0);

export default function SpreadsheetGrid({
  spreadsheetId,
  summary,
  rows,
  totalRows,
  productStats,
  monthlyStats,
  yearFilter,
  onYearFilterChange,
  searchTerm,
  onSearchTermChange,
  onSelectProduct,
}) {
  const [viewMode, setViewMode] = useState("rows"); // "rows" | "stats" | "monthly"

  const years = summary
    ? Array.from({ length: summary.num_years }, (_, i) => summary.start_year + i)
    : [];

  const filteredStats = productStats.filter((p) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (
      p.product_id.toLowerCase().includes(q) ||
      p.product_name.toLowerCase().includes(q) ||
      p.category.toLowerCase().includes(q)
    );
  });

  const filteredMonths = (monthlyStats || []).filter((m) => {
    if (!yearFilter) return true;
    return String(m.year) === String(yearFilter);
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setViewMode("rows")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
              viewMode === "rows"
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            Sheet Rows ({totalRows.toLocaleString()})
          </button>
          <button
            type="button"
            onClick={() => setViewMode("monthly")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
              viewMode === "monthly"
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Month-Wise Stats ({(monthlyStats || []).length})
          </button>
          <button
            type="button"
            onClick={() => setViewMode("stats")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
              viewMode === "stats"
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <BarChart className="w-3.5 h-3.5" />
            Product Stats ({productStats.length})
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => onSearchTermChange(e.target.value)}
              placeholder="Search PRD-001, category..."
              className="pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {(viewMode === "rows" || viewMode === "monthly") && (
            <select
              value={yearFilter}
              onChange={(e) => onYearFilterChange(e.target.value)}
              className="px-2.5 py-1.5 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Years</option>
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          )}

          {spreadsheetId && (
            <>
              <a
                href={`/api/spreadsheets/${spreadsheetId}/export/csv`}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
              >
                <Download className="w-3.5 h-3.5" />
                CSV
              </a>
              <a
                href={`/api/spreadsheets/${spreadsheetId}/export/xlsx`}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
              >
                <Download className="w-3.5 h-3.5" />
                Excel (.xlsx)
              </a>
            </>
          )}

          {summary?.google_sheet_url && (
            <a
              href={summary.google_sheet_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-700"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open Google Sheet
            </a>
          )}
        </div>
      </div>

      <div className="overflow-x-auto max-h-[420px]">
        {viewMode === "rows" && (
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-600">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Product ID</th>
                <th className="py-2.5 px-3 font-semibold">Product Name</th>
                <th className="py-2.5 px-3 font-semibold">Category</th>
                <th className="py-2.5 px-3 font-semibold">Year</th>
                <th className="py-2.5 px-3 font-semibold">Month</th>
                <th className="py-2.5 px-3 font-semibold text-right">Revenue</th>
                <th className="py-2.5 px-3 font-semibold text-right">Cost</th>
                <th className="py-2.5 px-3 font-semibold text-right">Profit / Loss</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r, i) => (
                <tr
                  key={`${r.product_id}-${r.period}-${i}`}
                  onClick={() => onSelectProduct(r.product_id)}
                  className="hover:bg-indigo-50/40 cursor-pointer"
                >
                  <td className="py-2 px-3 font-mono font-medium text-indigo-600">{r.product_id}</td>
                  <td className="py-2 px-3">{r.product_name}</td>
                  <td className="py-2 px-3 text-slate-500">{r.category}</td>
                  <td className="py-2 px-3">{r.year}</td>
                  <td className="py-2 px-3">{r.month}</td>
                  <td className="py-2 px-3 text-right font-mono">{money(r.revenue)}</td>
                  <td className="py-2 px-3 text-right font-mono">{money(r.cost)}</td>
                  <td
                    className={`py-2 px-3 text-right font-mono font-semibold ${
                      r.profit_loss >= 0 ? "text-emerald-600" : "text-rose-600"
                    }`}
                  >
                    {money(r.profit_loss)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {viewMode === "monthly" && (
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-600">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Period</th>
                <th className="py-2.5 px-3 font-semibold">Month</th>
                <th className="py-2.5 px-3 font-semibold text-right">Records</th>
                <th className="py-2.5 px-3 font-semibold text-right">Total Revenue</th>
                <th className="py-2.5 px-3 font-semibold text-right">Total Cost</th>
                <th className="py-2.5 px-3 font-semibold text-right">Net P&amp;L</th>
                <th className="py-2.5 px-3 font-semibold text-right">Total Loss</th>
                <th className="py-2.5 px-3 font-semibold text-right">Avg P&amp;L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredMonths.map((m) => (
                <tr key={m.period} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-mono font-medium text-indigo-600">{m.period}</td>
                  <td className="py-2 px-3">{m.month} {m.year}</td>
                  <td className="py-2 px-3 text-right">{m.record_count}</td>
                  <td className="py-2 px-3 text-right font-mono">{money(m.total_revenue)}</td>
                  <td className="py-2 px-3 text-right font-mono">{money(m.total_cost)}</td>
                  <td
                    className={`py-2 px-3 text-right font-mono font-semibold ${
                      m.net_profit_loss >= 0 ? "text-emerald-600" : "text-rose-600"
                    }`}
                  >
                    {money(m.net_profit_loss)}
                  </td>
                  <td className="py-2 px-3 text-right font-mono text-rose-600">{money(m.total_loss_only)}</td>
                  <td className="py-2 px-3 text-right font-mono">{money(m.avg_profit_loss)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {viewMode === "stats" && (
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-600">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Product ID</th>
                <th className="py-2.5 px-3 font-semibold">Name</th>
                <th className="py-2.5 px-3 font-semibold">Category</th>
                <th className="py-2.5 px-3 font-semibold text-right">Total Revenue</th>
                <th className="py-2.5 px-3 font-semibold text-right">Net P&amp;L</th>
                <th className="py-2.5 px-3 font-semibold text-right">Total Loss</th>
                <th className="py-2.5 px-3 font-semibold text-right">Avg / Month</th>
                <th className="py-2.5 px-3 font-semibold text-center">Profit / Loss Mos</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStats.map((p) => (
                <tr
                  key={p.product_id}
                  onClick={() => onSelectProduct(p.product_id)}
                  className="hover:bg-indigo-50/40 cursor-pointer"
                >
                  <td className="py-2 px-3 font-mono font-medium text-indigo-600">{p.product_id}</td>
                  <td className="py-2 px-3">{p.product_name}</td>
                  <td className="py-2 px-3 text-slate-500">{p.category}</td>
                  <td className="py-2 px-3 text-right font-mono">{money(p.total_revenue)}</td>
                  <td
                    className={`py-2 px-3 text-right font-mono font-semibold ${
                      p.net_profit_loss >= 0 ? "text-emerald-600" : "text-rose-600"
                    }`}
                  >
                    {money(p.net_profit_loss)}
                  </td>
                  <td className="py-2 px-3 text-right font-mono text-rose-600">
                    {money(p.total_loss_only)}
                  </td>
                  <td className="py-2 px-3 text-right font-mono">{money(p.avg_monthly_pl)}</td>
                  <td className="py-2 px-3 text-center">
                    <span className="text-emerald-600 font-medium">{p.profitable_months}</span>
                    {" / "}
                    <span className="text-rose-600 font-medium">{p.loss_months}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}