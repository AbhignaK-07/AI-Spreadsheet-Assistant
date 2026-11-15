from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateSpreadsheetRequest(BaseModel):
    prompt: str = Field(
        default="Create a spreadsheet for 100 products with monthly profit and loss over 5 years",
        description="Natural language prompt describing the spreadsheet to generate",
    )
    num_products: Optional[int] = Field(default=None, ge=1, le=1000)
    num_years: Optional[int] = Field(default=None, ge=1, le=20)
    start_year: int = Field(default=2022, ge=2000, le=2035)
    sync_google_sheets: bool = Field(default=False)
    sheet_title: Optional[str] = None


class AssistantQueryRequest(BaseModel):
    spreadsheet_id: str
    query: str
    chart_type: Optional[str] = Field(default="bar", pattern="^(bar|line)$")


class ChartSeries(BaseModel):
    label: str
    data: List[float]


class AssistantQueryResponse(BaseModel):
    answer: str
    intent: str
    metrics: Dict[str, Any] = {}
    chart_type: str = "bar"
    chart_title: str = ""
    chart_labels: List[str] = []
    chart_datasets: List[Dict[str, Any]] = []
    table_rows: List[Dict[str, Any]] = []


class SpreadsheetSummary(BaseModel):
    spreadsheet_id: str
    title: str
    num_products: int
    num_years: int
    start_year: int
    total_rows: int
    total_revenue: float
    total_cost: float
    net_profit_loss: float
    total_profit_only: float
    total_loss_only: float
    avg_monthly_profit_loss: float
    avg_product_profit_loss: float
    google_sheet_url: Optional[str] = None
