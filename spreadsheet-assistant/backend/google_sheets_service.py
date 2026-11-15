import os
from typing import Optional
import pandas as pd


def export_to_google_sheets(
    df: pd.DataFrame,
    title: str,
    share_email: Optional[str] = None,
) -> dict:
    """
    Exports the generated DataFrame to Google Sheets using a Google Service Account.
    If credentials are not configured, returns a structured status so the app
    continues working locally with CSV/XLSX download.
    """
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    if not os.path.exists(creds_path):
        return {
            "synced": False,
            "url": None,
            "message": (
                "Google Sheets credentials (service_account.json) not found. "
                "Spreadsheet was created locally and is ready for CSV/XLSX export."
            ),
        }

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)

        spreadsheet = client.create(title)
        worksheet = spreadsheet.sheet1
        worksheet.update_title("Monthly_Profit_Loss")

        # Prepare header + rows (convert numpy/pandas types to native Python)
        headers = list(df.columns)
        rows = df.astype(object).where(pd.notnull(df), "").values.tolist()
        worksheet.update([headers] + rows)

        # Add a second tab with per-product summary
        summary_df = (
            df.groupby(["product_id", "product_name", "category"], as_index=False)
            .agg(
                total_revenue=("revenue", "sum"),
                total_cost=("cost", "sum"),
                net_profit_loss=("profit_loss", "sum"),
                avg_monthly_pl=("profit_loss", "mean"),
            )
            .round(2)
        )
        summary_ws = spreadsheet.add_worksheet(
            title="Product_Summary",
            rows=str(len(summary_df) + 10),
            cols="10",
        )
        summary_ws.update(
            [list(summary_df.columns)] + summary_df.values.tolist()
        )

        target_email = share_email or os.getenv("GOOGLE_SHARE_EMAIL", "").strip()
        if target_email:
            spreadsheet.share(target_email, perm_type="user", role="writer")

        return {
            "synced": True,
            "url": spreadsheet.url,
            "message": f"Successfully exported '{title}' to Google Sheets.",
        }
    except Exception as exc:
        return {
            "synced": False,
            "url": None,
            "message": f"Google Sheets sync skipped due to error: {exc}",
        }
