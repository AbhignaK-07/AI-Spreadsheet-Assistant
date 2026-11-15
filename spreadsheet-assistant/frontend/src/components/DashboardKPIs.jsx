import React from "react";
import { TrendingUp, TrendingDown, DollarSign, BarChart3 } from "lucide-react";

const fmt = (val) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(val || 0);

export default function DashboardKPIs({ summary }) {
  if (!summary) return null;

  const cards = [
    {
      label: "Net Profit / Loss (5 Yrs)",
      value: fmt(summary.net_profit_loss),
      sub: `${summary.num_products} products · ${summary.total_rows.toLocaleString()} rows`,
      icon: DollarSign,
      color: summary.net_profit_loss >= 0 ? "text-emerald-600 bg-emerald-50" : "text-rose-600 bg-rose-50",
    },
    {
      label: "Total Profitable Months Sum",
      value: fmt(summary.total_profit_only),
      sub: `Total Revenue: ${fmt(summary.total_revenue)}`,
      icon: TrendingUp,
      color: "text-indigo-600 bg-indigo-50",
    },
    {
      label: "Total Cumulative Loss",
      value: fmt(summary.total_loss_only),
      sub: `Total Cost: ${fmt(summary.total_cost)}`,
      icon: TrendingDown,
      color: "text-rose-600 bg-rose-50",
    },
    {
      label: "Avg Monthly Net P&L",
      value: fmt(summary.avg_monthly_profit_loss),
      sub: `Avg / Product (5 Yrs): ${fmt(summary.avg_product_profit_loss)}`,
      icon: BarChart3,
      color: "text-amber-600 bg-amber-50",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div
            key={c.label}
            className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-start justify-between"
          >
            <div>
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                {c.label}
              </p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{c.value}</p>
              <p className="text-xs text-slate-500 mt-1">{c.sub}</p>
            </div>
            <div className={`p-2.5 rounded-lg ${c.color}`}>
              <Icon className="w-5 h-5" />
            </div>
          </div>
        );
      })}
    </div>
  );
}
