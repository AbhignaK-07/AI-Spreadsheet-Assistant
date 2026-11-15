import io
import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

CATEGORIES = [
    "Electronics",
    "Apparel",
    "Home & Kitchen",
    "Fitness & Sports",
    "Office Supplies",
]


def parse_creation_prompt(prompt: str) -> Tuple[int, int, bool]:
    """Extract (num_products, num_years, wants_google_sheets) from user prompt."""
    text = prompt.lower()

    prod_match = re.search(r"(\d+)\s*(?:products?|items?|skus?)", text)
    num_products = int(prod_match.group(1)) if prod_match else 100
    num_products = max(1, min(num_products, 1000))

    year_match = re.search(r"(\d+|five|three|two|four|ten)\s*(?:years?|yrs?)", text)
    word_to_num = {"two": 2, "three": 3, "four": 4, "five": 5, "ten": 10}
    if year_match:
        raw = year_match.group(1)
        num_years = word_to_num.get(raw, int(raw) if raw.isdigit() else 5)
    else:
        num_years = 5
    num_years = max(1, min(num_years, 20))

    wants_gsheets = "google sheet" in text or "sheets" in text
    return num_products, num_years, wants_gsheets


def generate_profit_loss_dataset(
    num_products: int = 100,
    num_years: int = 5,
    start_year: int = 2022,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Generate a realistic monthly profit & loss dataset for `num_products` across `num_years` * 12 months."""
    rng = np.random.default_rng(seed if seed is not None else 42)
    records: List[Dict[str, Any]] = []

    for p_idx in range(1, num_products + 1):
        product_id = f"PRD-{p_idx:03d}"
        product_name = f"Product {p_idx}"
        category = CATEGORIES[(p_idx - 1) % len(CATEGORIES)]

        base_revenue = float(rng.uniform(8000, 45000))
        margin_bias = float(rng.choice([0.18, 0.08, 0.02, -0.06], p=[0.45, 0.25, 0.15, 0.15]))
        annual_growth = float(rng.uniform(-0.04, 0.10))

        month_counter = 0
        for y_offset in range(num_years):
            year = start_year + y_offset
            year_factor = (1.0 + annual_growth) ** y_offset

            for m_idx, month_name in enumerate(MONTH_NAMES, start=1):
                month_counter += 1
                seasonal = 1.0 + 0.15 * np.sin((m_idx - 3) * np.pi / 6.0)
                noise = float(rng.normal(1.0, 0.12))
                revenue = max(500.0, base_revenue * year_factor * seasonal * noise)

                cost_ratio = max(0.45, 1.0 - margin_bias + float(rng.normal(0.0, 0.09)))
                cost = revenue * cost_ratio
                profit_loss = revenue - cost

                records.append(
                    {
                        "product_id": product_id,
                        "product_name": product_name,
                        "category": category,
                        "year": year,
                        "month_num": m_idx,
                        "month": month_name,
                        "period": f"{year}-{m_idx:02d}",
                        "month_index": month_counter,
                        "revenue": round(revenue, 2),
                        "cost": round(cost, 2),
                        "profit_loss": round(profit_loss, 2),
                    }
                )

    return pd.DataFrame(records)


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    for col_lower, orig in lower_map.items():
        if any(cand in col_lower for cand in candidates):
            return orig
    return None


def normalize_uploaded_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize any uploaded Excel/CSV/text DataFrame so it works seamlessly with
    the dashboard, month-wise statistics, product statistics, and NL assistant.
    """
    df = raw_df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    # Detect or synthesize product_id / product_name / category
    pid_col = _find_col(df, ["product_id", "sku", "id", "item_id", "code"])
    pname_col = _find_col(df, ["product_name", "product", "item", "name", "title", "description"])
    cat_col = _find_col(df, ["category", "department", "group", "type", "region"])

    if pname_col and "product_name" not in df.columns:
        df["product_name"] = df[pname_col].astype(str)
    elif "product_name" not in df.columns:
        df["product_name"] = [f"Item {i + 1}" for i in range(len(df))]

    if pid_col and "product_id" not in df.columns:
        df["product_id"] = df[pid_col].astype(str)
    elif "product_id" not in df.columns:
        unique_names = {name: f"PRD-{idx + 1:03d}" for idx, name in enumerate(df["product_name"].unique())}
        df["product_id"] = df["product_name"].map(unique_names)

    if cat_col and "category" not in df.columns:
        df["category"] = df[cat_col].astype(str)
    elif "category" not in df.columns:
        df["category"] = "General"

    # Detect or synthesize date / year / month / period
    date_col = _find_col(df, ["date", "timestamp", "order_date", "created_at"])
    year_col = _find_col(df, ["year", "yr"])
    month_col = _find_col(df, ["month", "month_name", "mo"])
    period_col = _find_col(df, ["period", "year_month", "ym"])

    if date_col:
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
        if parsed_dates.notna().any():
            df["year"] = parsed_dates.dt.year.fillna(2024).astype(int)
            df["month_num"] = parsed_dates.dt.month.fillna(1).astype(int)
            df["month"] = df["month_num"].apply(lambda m: MONTH_NAMES[(int(m) - 1) % 12])
            df["period"] = parsed_dates.dt.strftime("%Y-%m").fillna("2024-01")

    if "year" not in df.columns:
        if year_col:
            df["year"] = pd.to_numeric(df[year_col], errors="coerce").fillna(2024).astype(int)
        else:
            df["year"] = 2024

    if "month" not in df.columns or "month_num" not in df.columns:
        if month_col:
            raw_m = df[month_col]
            if pd.api.types.is_numeric_dtype(raw_m):
                df["month_num"] = pd.to_numeric(raw_m, errors="coerce").fillna(1).astype(int).clip(1, 12)
                df["month"] = df["month_num"].apply(lambda m: MONTH_NAMES[m - 1])
            else:
                month_lookup = {name.lower(): idx + 1 for idx, name in enumerate(MONTH_NAMES)}
                df["month_num"] = raw_m.astype(str).str.strip().str[:3].str.lower().map(month_lookup).fillna(1).astype(int)
                df["month"] = df["month_num"].apply(lambda m: MONTH_NAMES[m - 1])
        else:
            df["month_num"] = 1
            df["month"] = "Jan"

    if "period" not in df.columns:
        if period_col:
            df["period"] = df[period_col].astype(str)
        else:
            df["period"] = df.apply(lambda r: f"{int(r['year'])}-{int(r['month_num']):02d}", axis=1)

    # Detect or synthesize revenue, cost, profit_loss
    rev_col = _find_col(df, ["revenue", "sales", "income", "gross"])
    cost_col = _find_col(df, ["cost", "expense", "cogs", "spend"])
    pl_col = _find_col(df, ["profit_loss", "profit/loss", "profit", "net_profit", "pnl", "p&l", "amount", "total", "value"])

    if rev_col and "revenue" not in df.columns:
        df["revenue"] = pd.to_numeric(df[rev_col], errors="coerce").fillna(0.0)
    if cost_col and "cost" not in df.columns:
        df["cost"] = pd.to_numeric(df[cost_col], errors="coerce").fillna(0.0)
    if pl_col and "profit_loss" not in df.columns:
        df["profit_loss"] = pd.to_numeric(df[pl_col], errors="coerce").fillna(0.0)

    if "revenue" not in df.columns and "profit_loss" in df.columns:
        df["revenue"] = df["profit_loss"].apply(lambda v: max(0.0, float(v)))
    if "cost" not in df.columns:
        if "revenue" in df.columns and "profit_loss" in df.columns:
            df["cost"] = (df["revenue"] - df["profit_loss"]).round(2)
        else:
            df["cost"] = 0.0
    if "revenue" not in df.columns:
        # Fallback: pick first numeric column not already used
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in {"year", "month_num"}]
        if numeric_cols:
            df["revenue"] = df[numeric_cols[0]].fillna(0.0)
        else:
            df["revenue"] = 0.0
    if "profit_loss" not in df.columns:
        df["profit_loss"] = (df["revenue"] - df["cost"]).round(2)

    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0).round(2)
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0).round(2)
    df["profit_loss"] = pd.to_numeric(df["profit_loss"], errors="coerce").fillna(0.0).round(2)
    return df


def parse_text_to_dataframe(text: str) -> pd.DataFrame:
    """
    Convert raw text (CSV, TSV, pipe-delimited table, or key:value lines)
    into a normalized DataFrame ready for Excel export and analytics.
    """
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Text input is empty.")

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]

    # 1. Markdown / pipe-delimited table
    if any("|" in ln for ln in lines[:3]):
        table_lines = [ln for ln in lines if not re.match(r"^[\|\-\:\s]+$", ln)]
        rows = [[cell.strip() for cell in ln.strip("|").split("|")] for ln in table_lines]
        if len(rows) >= 2:
            raw_df = pd.DataFrame(rows[1:], columns=rows[0])
            return normalize_uploaded_dataframe(raw_df)

    # 2. Key-value lines (check before CSV so "Product: X, Revenue: Y" is not treated as CSV header)
    if ":" in lines[0] or "=" in lines[0]:
        kv_records: List[Dict[str, Any]] = []
        for ln in lines:
            ln_clean = re.sub(r"^[\-\*\d\.\)\s]+", "", ln)
            pairs = re.findall(r"([A-Za-z0-9_ /&-]+?)\s*[:=]\s*([^,;|\n]+)", ln_clean)
            if pairs:
                kv_records.append({k.strip(): v.strip() for k, v in pairs})
        if kv_records:
            return normalize_uploaded_dataframe(pd.DataFrame(kv_records))

    # 3. CSV or TSV
    for sep in [",", "\t", ";"]:
        if sep in lines[0]:
            try:
                raw_df = pd.read_csv(io.StringIO("\n".join(lines)), sep=sep)
                if len(raw_df.columns) >= 2 and len(raw_df) >= 1:
                    return normalize_uploaded_dataframe(raw_df)
            except Exception:
                pass

    # 3. Key-value lines (e.g. "Product: Shoes, Month: Jan, Revenue: 5000, Cost: 3200")
    kv_records: List[Dict[str, Any]] = []
    for ln in lines:
        ln_clean = re.sub(r"^[\-\*\d\.\)\s]+", "", ln)
        pairs = re.findall(r"([A-Za-z0-9_ /&-]+?)\s*[:=]\s*([^,;|\n]+)", ln_clean)
        if pairs:
            record = {k.strip(): v.strip() for k, v in pairs}
            kv_records.append(record)

    if kv_records:
        raw_df = pd.DataFrame(kv_records)
        return normalize_uploaded_dataframe(raw_df)

    # 4. Whitespace-delimited fallback
    try:
        raw_df = pd.read_csv(io.StringIO("\n".join(lines)), sep=r"\s{2,}", engine="python")
        if len(raw_df.columns) >= 2:
            return normalize_uploaded_dataframe(raw_df)
    except Exception:
        pass

    raise ValueError(
        "Could not parse text into a table. Try comma-separated, pipe-delimited, or 'Key: Value' lines."
    )


def get_monthly_statistics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Compute month-wise statistics (by period YYYY-MM) across the dataset."""
    rows: List[Dict[str, Any]] = []
    for period, grp in df.groupby("period", sort=True):
        pl = grp["profit_loss"]
        rows.append(
            {
                "period": str(period),
                "year": int(grp["year"].iloc[0]),
                "month": str(grp["month"].iloc[0]),
                "record_count": int(len(grp)),
                "total_revenue": round(float(grp["revenue"].sum()), 2),
                "total_cost": round(float(grp["cost"].sum()), 2),
                "net_profit_loss": round(float(pl.sum()), 2),
                "total_profit_only": round(float(pl[pl > 0].sum()), 2),
                "total_loss_only": round(float(pl[pl < 0].sum()), 2),
                "avg_profit_loss": round(float(pl.mean()), 2),
                "max_profit_loss": round(float(pl.max()), 2),
                "min_profit_loss": round(float(pl.min()), 2),
            }
        )
    return rows


def get_column_statistics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Compute descriptive statistics for every numeric column in any uploaded Excel sheet."""
    stats: List[Dict[str, Any]] = []
    for col in df.select_dtypes(include=[np.number]).columns:
        series = df[col].dropna()
        if series.empty:
            continue
        stats.append(
            {
                "column": str(col),
                "count": int(series.count()),
                "sum": round(float(series.sum()), 2),
                "mean": round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
                "std_dev": round(float(series.std(ddof=0)), 2),
            }
        )
    return stats


def compute_summary(
    df: pd.DataFrame,
    spreadsheet_id: str,
    title: str,
    google_sheet_url: Optional[str] = None,
) -> Dict[str, Any]:
    total_revenue = float(df["revenue"].sum())
    total_cost = float(df["cost"].sum())
    net_pl = float(df["profit_loss"].sum())
    total_profit_only = float(df.loc[df["profit_loss"] > 0, "profit_loss"].sum())
    total_loss_only = float(df.loc[df["profit_loss"] < 0, "profit_loss"].sum())

    monthly_totals = df.groupby("period")["profit_loss"].sum()
    product_totals = df.groupby("product_id")["profit_loss"].sum()

    return {
        "spreadsheet_id": spreadsheet_id,
        "title": title,
        "num_products": int(df["product_id"].nunique()),
        "num_years": int(df["year"].nunique()),
        "start_year": int(df["year"].min()),
        "total_rows": int(len(df)),
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "net_profit_loss": round(net_pl, 2),
        "total_profit_only": round(total_profit_only, 2),
        "total_loss_only": round(total_loss_only, 2),
        "avg_monthly_profit_loss": round(float(monthly_totals.mean()), 2) if len(monthly_totals) else 0.0,
        "avg_product_profit_loss": round(float(product_totals.mean()), 2) if len(product_totals) else 0.0,
        "google_sheet_url": google_sheet_url,
    }


def _extract_product_ids(query: str, df: pd.DataFrame) -> List[str]:
    found: List[str] = []
    valid_ids = set(df["product_id"].unique())

    for match in re.findall(r"\bprd[-_]?(\d{1,3})\b", query, flags=re.IGNORECASE):
        pid = f"PRD-{int(match):03d}"
        if pid in valid_ids and pid not in found:
            found.append(pid)

    for match in re.findall(r"\bproduct\s*#?\s*(\d{1,3})\b", query, flags=re.IGNORECASE):
        pid = f"PRD-{int(match):03d}"
        if pid in valid_ids and pid not in found:
            found.append(pid)

    return found


def _extract_years(query: str, df: pd.DataFrame) -> List[int]:
    valid_years = set(int(y) for y in df["year"].unique())
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", query) if int(y) in valid_years]
    return sorted(set(years))


def get_product_statistics(df: pd.DataFrame, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
    target_df = df if product_id is None else df[df["product_id"] == product_id]
    stats: List[Dict[str, Any]] = []

    for pid, grp in target_df.groupby("product_id", sort=True):
        pl = grp["profit_loss"]
        stats.append(
            {
                "product_id": pid,
                "product_name": str(grp["product_name"].iloc[0]),
                "category": str(grp["category"].iloc[0]),
                "total_revenue": round(float(grp["revenue"].sum()), 2),
                "total_cost": round(float(grp["cost"].sum()), 2),
                "net_profit_loss": round(float(pl.sum()), 2),
                "total_profit_only": round(float(pl[pl > 0].sum()), 2),
                "total_loss_only": round(float(pl[pl < 0].sum()), 2),
                "avg_monthly_pl": round(float(pl.mean()), 2),
                "max_monthly_pl": round(float(pl.max()), 2),
                "min_monthly_pl": round(float(pl.min()), 2),
                "profitable_months": int((pl > 0).sum()),
                "loss_months": int((pl < 0).sum()),
            }
        )
    return stats


def _try_openai_summary(query: str, metrics: Dict[str, Any]) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise financial spreadsheet assistant. "
                        "Summarize the verified metrics in 2-3 clear sentences. "
                        "Never invent numbers not present in the JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": f"User query: {query}\nVerified metrics: {json.dumps(metrics)}",
                },
            ],
            temperature=0.2,
            max_tokens=160,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def answer_query(
    df: pd.DataFrame,
    query: str,
    preferred_chart_type: str = "bar",
) -> Dict[str, Any]:
    q = query.lower().strip()
    years_filter = _extract_years(q, df)
    work_df = df[df["year"].isin(years_filter)] if years_filter else df
    product_ids = _extract_product_ids(q, work_df)

    # 0. Month-wise statistics
    if any(k in q for k in ["month wise", "month-wise", "monthly", "by month", "per month"]):
        m_stats = get_monthly_statistics(work_df)
        labels = [r["period"] for r in m_stats]
        datasets = [
            {"label": "Monthly Revenue ($)", "data": [r["total_revenue"] for r in m_stats]},
            {"label": "Monthly Net P&L ($)", "data": [r["net_profit_loss"] for r in m_stats]},
            {"label": "Monthly Loss ($)", "data": [r["total_loss_only"] for r in m_stats]},
        ]
        best_m = max(m_stats, key=lambda r: r["net_profit_loss"])
        worst_m = min(m_stats, key=lambda r: r["net_profit_loss"])
        metrics = {
            "months_count": len(m_stats),
            "best_month": f"{best_m['period']} (${best_m['net_profit_loss']:,.2f})",
            "worst_month": f"{worst_m['period']} (${worst_m['net_profit_loss']:,.2f})",
        }
        answer = _try_openai_summary(query, metrics) or (
            f"Month-wise statistics across {len(m_stats)} month(s): "
            f"Best month was {best_m['period']} (${best_m['net_profit_loss']:,.2f}) and "
            f"worst month was {worst_m['period']} (${worst_m['net_profit_loss']:,.2f})."
        )
        return {
            "answer": answer,
            "intent": "monthly_statistics",
            "metrics": metrics,
            "chart_type": preferred_chart_type,
            "chart_title": "Month-Wise Revenue, Net P&L & Loss",
            "chart_labels": labels,
            "chart_datasets": datasets,
            "table_rows": m_stats,
        }

    # 1. Product Comparison
    if len(product_ids) >= 2 or ("compare" in q and len(product_ids) >= 1):
        if len(product_ids) == 1:
            top_pid = work_df.groupby("product_id")["profit_loss"].sum().idxmax()
            if top_pid != product_ids[0]:
                product_ids.append(top_pid)

        comp_df = work_df[work_df["product_id"].isin(product_ids)]
        yearly = (
            comp_df.groupby(["year", "product_id"])["profit_loss"]
            .sum()
            .unstack(fill_value=0)
            .round(2)
        )
        labels = [str(y) for y in yearly.index.tolist()]
        datasets = [
            {
                "label": f"{pid} ({comp_df.loc[comp_df['product_id'] == pid, 'product_name'].iloc[0]})",
                "data": [float(v) for v in yearly[pid].tolist()],
            }
            for pid in product_ids
            if pid in yearly.columns
        ]
        stats_rows = get_product_statistics(comp_df)
        metrics = {"compared_products": product_ids, "yearly_totals": yearly.to_dict()}
        answer = _try_openai_summary(query, metrics) or (
            f"Compared {', '.join(product_ids)} across {len(labels)} year(s). "
            + " ".join(
                f"{r['product_id']} net P&L: ${r['net_profit_loss']:,.2f} (avg ${r['avg_monthly_pl']:,.2f}/mo)."
                for r in stats_rows
            )
        )
        return {
            "answer": answer,
            "intent": "product_comparison",
            "metrics": metrics,
            "chart_type": preferred_chart_type,
            "chart_title": f"Yearly Profit/Loss Comparison: {' vs '.join(product_ids)}",
            "chart_labels": labels,
            "chart_datasets": datasets,
            "table_rows": stats_rows,
        }

    # 2. Single Product Statistics
    if len(product_ids) == 1:
        pid = product_ids[0]
        p_df = work_df[work_df["product_id"] == pid]
        stats = get_product_statistics(p_df, pid)[0]
        yearly = p_df.groupby("year")["profit_loss"].sum().round(2)
        labels = [str(y) for y in yearly.index.tolist()]
        datasets = [{"label": f"{pid} Yearly Profit/Loss ($)", "data": [float(v) for v in yearly.values.tolist()]}]
        answer = _try_openai_summary(query, stats) or (
            f"{stats['product_name']} ({pid}, {stats['category']}): "
            f"Net P&L is ${stats['net_profit_loss']:,.2f} "
            f"(Total Profit: ${stats['total_profit_only']:,.2f}, Total Loss: ${stats['total_loss_only']:,.2f}). "
            f"Monthly average is ${stats['avg_monthly_pl']:,.2f}."
        )
        return {
            "answer": answer,
            "intent": "product_statistics",
            "metrics": stats,
            "chart_type": preferred_chart_type,
            "chart_title": f"{stats['product_name']} ({pid}) — Yearly Profit & Loss",
            "chart_labels": labels,
            "chart_datasets": datasets,
            "table_rows": [stats],
        }

    # 3. Top / Worst Products Ranking
    if any(k in q for k in ["top", "best", "highest", "worst", "lowest", "most loss", "biggest loss"]):
        n_match = re.search(r"\b(\d+)\b", q)
        top_n = min(20, max(3, int(n_match.group(1)))) if n_match else 10
        is_worst = any(k in q for k in ["worst", "lowest", "most loss", "biggest loss"])

        grouped = (
            work_df.groupby(["product_id", "product_name", "category"], as_index=False)["profit_loss"]
            .sum()
            .round(2)
            .sort_values("profit_loss", ascending=is_worst)
            .head(top_n)
        )
        labels = grouped["product_id"].tolist()
        datasets = [{"label": "Net Profit/Loss ($)", "data": [float(v) for v in grouped["profit_loss"].tolist()]}]
        direction = "lowest (worst)" if is_worst else "highest (top)"
        lead = grouped.iloc[0]
        metrics = {"ranking": direction, "count": top_n, "leader": f"{lead['product_id']} (${lead['profit_loss']:,.2f})"}
        answer = _try_openai_summary(query, metrics) or (
            f"Showing the {top_n} products with the {direction} net profit/loss. "
            f"#1 is {lead['product_name']} ({lead['product_id']}) at ${lead['profit_loss']:,.2f}."
        )
        return {
            "answer": answer,
            "intent": "product_ranking",
            "metrics": metrics,
            "chart_type": "bar",
            "chart_title": f"{'Worst' if is_worst else 'Top'} {top_n} Products by Net Profit/Loss",
            "chart_labels": labels,
            "chart_datasets": datasets,
            "table_rows": grouped.to_dict(orient="records"),
        }

    # 4. Total Loss / Total Profit / Average / Overall Statistics
    total_loss = float(work_df.loc[work_df["profit_loss"] < 0, "profit_loss"].sum())
    total_profit = float(work_df.loc[work_df["profit_loss"] > 0, "profit_loss"].sum())
    net_pl = float(work_df["profit_loss"].sum())
    avg_monthly_per_record = float(work_df["profit_loss"].mean())
    avg_monthly_company = float(work_df.groupby("period")["profit_loss"].sum().mean())
    avg_per_product = float(work_df.groupby("product_id")["profit_loss"].sum().mean())
    loss_rows_count = int((work_df["profit_loss"] < 0).sum())

    yearly_summary = (
        work_df.groupby("year", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_cost=("cost", "sum"),
            net_profit_loss=("profit_loss", "sum"),
        )
        .round(2)
    )
    yearly_losses = (
        work_df[work_df["profit_loss"] < 0]
        .groupby("year")["profit_loss"]
        .sum()
        .reindex(yearly_summary["year"], fill_value=0)
        .round(2)
    )
    yearly_profits = (
        work_df[work_df["profit_loss"] > 0]
        .groupby("year")["profit_loss"]
        .sum()
        .reindex(yearly_summary["year"], fill_value=0)
        .round(2)
    )

    labels = [str(y) for y in yearly_summary["year"].tolist()]
    datasets = [
        {"label": "Total Profit ($)", "data": [float(v) for v in yearly_profits.values.tolist()]},
        {"label": "Total Loss ($)", "data": [float(v) for v in yearly_losses.values.tolist()]},
        {"label": "Net P&L ($)", "data": [float(v) for v in yearly_summary["net_profit_loss"].tolist()]},
    ]

    metrics = {
        "total_loss": round(total_loss, 2),
        "total_profit": round(total_profit, 2),
        "net_profit_loss": round(net_pl, 2),
        "avg_monthly_per_product": round(avg_monthly_per_record, 2),
        "avg_monthly_total": round(avg_monthly_company, 2),
        "avg_5yr_per_product": round(avg_per_product, 2),
        "loss_month_entries": loss_rows_count,
    }

    if "loss" in q and "average" not in q and "avg" not in q:
        intent = "total_loss"
        default_answer = (
            f"Total cumulative loss across {loss_rows_count:,} loss-making product-months is "
            f"${total_loss:,.2f} (Net P&L after profits: ${net_pl:,.2f})."
        )
    elif "average" in q or "avg" in q or "mean" in q:
        intent = "total_average"
        default_answer = (
            f"Average monthly P&L per product is ${avg_monthly_per_record:,.2f}. "
            f"Average company-wide monthly P&L is ${avg_monthly_company:,.2f}, and "
            f"average total P&L per product is ${avg_per_product:,.2f}."
        )
    else:
        intent = "overall_statistics"
        default_answer = (
            f"Overall Net P&L is ${net_pl:,.2f} "
            f"(Total Profit: ${total_profit:,.2f}, Total Loss: ${total_loss:,.2f}). "
            f"Average monthly P&L per product is ${avg_monthly_per_record:,.2f}."
        )

    answer = _try_openai_summary(query, metrics) or default_answer
    return {
        "answer": answer,
        "intent": intent,
        "metrics": metrics,
        "chart_type": preferred_chart_type,
        "chart_title": "Yearly Profit, Loss & Net P&L Breakdown",
        "chart_labels": labels,
        "chart_datasets": datasets,
        "table_rows": yearly_summary.to_dict(orient="records"),
    }


def create_spreadsheet_id() -> str:
    return str(uuid.uuid4())[:8]