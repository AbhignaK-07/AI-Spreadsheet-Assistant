import io
from typing import Dict, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
from pydantic import BaseModel

from google_sheets_service import export_to_google_sheets
from models import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    CreateSpreadsheetRequest,
    SpreadsheetSummary,
)
from spreadsheet_engine import (
    answer_query,
    compute_summary,
    create_spreadsheet_id,
    generate_profit_loss_dataset,
    get_column_statistics,
    get_monthly_statistics,
    get_product_statistics,
    normalize_uploaded_dataframe,
    parse_creation_prompt,
    parse_text_to_dataframe,
)

load_dotenv()

app = FastAPI(
    title="AI Spreadsheet Assistant API",
    description="Python FastAPI + Pandas backend for spreadsheets, Excel uploads, text-to-Excel conversion, and month-wise analytics.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SPREADSHEET_STORE: Dict[str, Dict] = {}


class TextToExcelRequest(BaseModel):
    text: str
    title: Optional[str] = "Converted Text Spreadsheet"


@app.get("/api/health")
def health_check():
    return {"status": "ok", "active_spreadsheets": len(SPREADSHEET_STORE)}


@app.post("/api/spreadsheets/create")
def create_spreadsheet(req: CreateSpreadsheetRequest):
    parsed_products, parsed_years, wants_gsheets = parse_creation_prompt(req.prompt)
    num_products = req.num_products or parsed_products
    num_years = req.num_years or parsed_years
    sync_gsheets = req.sync_google_sheets or wants_gsheets

    df = generate_profit_loss_dataset(
        num_products=num_products,
        num_years=num_years,
        start_year=req.start_year,
    )
    sid = create_spreadsheet_id()
    title = req.sheet_title or f"{num_products} Products — {num_years}-Year Profit & Loss"

    gsheet_result = {"synced": False, "url": None, "message": "Local mode"}
    if sync_gsheets:
        gsheet_result = export_to_google_sheets(df, title=title)

    SPREADSHEET_STORE[sid] = {
        "title": title,
        "df": df,
        "google_sheet_url": gsheet_result.get("url"),
    }

    summary = compute_summary(
        df,
        spreadsheet_id=sid,
        title=title,
        google_sheet_url=gsheet_result.get("url"),
    )
    return {
        "summary": SpreadsheetSummary(**summary),
        "google_sheets_status": gsheet_result,
        "bot_message": (
            f"Created '{title}' with {num_products} products across {num_years} years "
            f"({len(df):,} monthly rows). Net P&L: ${summary['net_profit_loss']:,.2f}. "
            f"{gsheet_result['message']}"
        ),
    }


@app.post("/api/spreadsheets/upload")
async def upload_spreadsheet(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_sheet"
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    raw_bytes = await file.read()

    try:
        if ext in {"xlsx", "xls"}:
            raw_df = pd.read_excel(io.BytesIO(raw_bytes))
        elif ext == "csv":
            raw_df = pd.read_csv(io.BytesIO(raw_bytes))
        elif ext in {"txt", "md", "tsv"}:
            raw_df = parse_text_to_dataframe(raw_bytes.decode("utf-8", errors="replace"))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Upload .xlsx, .xls, .csv, .txt, or .md.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {exc}")

    df = normalize_uploaded_dataframe(raw_df)
    sid = create_spreadsheet_id()
    title = f"Uploaded: {filename}"

    SPREADSHEET_STORE[sid] = {"title": title, "df": df, "google_sheet_url": None}
    summary = compute_summary(df, spreadsheet_id=sid, title=title)
    col_stats = get_column_statistics(raw_df)

    return {
        "summary": SpreadsheetSummary(**summary),
        "column_statistics": col_stats,
        "bot_message": (
            f"Loaded '{filename}' ({len(df):,} rows, {summary['num_products']} items). "
            f"Net P&L: ${summary['net_profit_loss']:,.2f}. Ask for month-wise or product statistics!"
        ),
    }


@app.post("/api/spreadsheets/from-text")
async def create_from_text(
    text: Optional[str] = Form(default=None),
    title: Optional[str] = Form(default="Converted Text Spreadsheet"),
    file: Optional[UploadFile] = File(default=None),
):
    raw_text = text or ""
    if file is not None:
        raw_bytes = await file.read()
        raw_text = raw_bytes.decode("utf-8", errors="replace")
        if title == "Converted Text Spreadsheet" and file.filename:
            title = f"Converted: {file.filename}"

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Provide raw text or upload a .txt/.md document.")

    try:
        df = parse_text_to_dataframe(raw_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    sid = create_spreadsheet_id()
    SPREADSHEET_STORE[sid] = {"title": title, "df": df, "google_sheet_url": None}
    summary = compute_summary(df, spreadsheet_id=sid, title=title)

    return {
        "summary": SpreadsheetSummary(**summary),
        "column_statistics": get_column_statistics(df),
        "bot_message": (
            f"Built Excel spreadsheet '{title}' from your text ({len(df):,} rows). "
            f"You can now view month-wise stats, charts, or download the .xlsx file!"
        ),
    }


@app.get("/api/spreadsheets/{spreadsheet_id}/rows")
def get_spreadsheet_rows(
    spreadsheet_id: str,
    year: Optional[int] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=6000),
    offset: int = Query(default=0, ge=0),
):
    entry = SPREADSHEET_STORE.get(spreadsheet_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")

    df: pd.DataFrame = entry["df"]
    filtered = df
    if year is not None:
        filtered = filtered[filtered["year"] == year]
    if search:
        term = search.strip().lower()
        filtered = filtered[
            filtered["product_id"].str.lower().str.contains(term)
            | filtered["product_name"].str.lower().str.contains(term)
            | filtered["category"].str.lower().str.contains(term)
        ]

    total = len(filtered)
    page_df = filtered.iloc[offset : offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "rows": page_df.to_dict(orient="records")}


@app.get("/api/spreadsheets/{spreadsheet_id}/stats")
def get_all_product_stats(spreadsheet_id: str):
    entry = SPREADSHEET_STORE.get(spreadsheet_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    stats = get_product_statistics(entry["df"])
    return {"count": len(stats), "products": stats}


@app.get("/api/spreadsheets/{spreadsheet_id}/monthly-stats")
def get_monthwise_stats(spreadsheet_id: str):
    entry = SPREADSHEET_STORE.get(spreadsheet_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    m_stats = get_monthly_statistics(entry["df"])
    c_stats = get_column_statistics(entry["df"])
    return {"count": len(m_stats), "months": m_stats, "columns": c_stats}


@app.post("/api/assistant/query", response_model=AssistantQueryResponse)
def query_assistant(req: AssistantQueryRequest):
    entry = SPREADSHEET_STORE.get(req.spreadsheet_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    result = answer_query(
        df=entry["df"],
        query=req.query,
        preferred_chart_type=req.chart_type or "bar",
    )
    return AssistantQueryResponse(**result)


@app.get("/api/spreadsheets/{spreadsheet_id}/export/csv")
def export_csv(spreadsheet_id: str):
    entry = SPREADSHEET_STORE.get(spreadsheet_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    buf = io.StringIO()
    entry["df"].to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=spreadsheet_{spreadsheet_id}.csv"},
    )


@app.get("/api/spreadsheets/{spreadsheet_id}/export/xlsx")
def export_xlsx(spreadsheet_id: str):
    entry = SPREADSHEET_STORE.get(spreadsheet_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Spreadsheet not found")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        entry["df"].to_excel(writer, sheet_name="Monthly_Data", index=False)
        pd.DataFrame(get_product_statistics(entry["df"])).to_excel(
            writer, sheet_name="Product_Statistics", index=False
        )
        pd.DataFrame(get_monthly_statistics(entry["df"])).to_excel(
            writer, sheet_name="Month_Wise_Stats", index=False
        )
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=spreadsheet_{spreadsheet_id}.xlsx"},
    )