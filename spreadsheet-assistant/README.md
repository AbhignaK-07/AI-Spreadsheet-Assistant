# AI Spreadsheet Assistant (React + Python FastAPI + Google Sheets)

An interactive full-stack spreadsheet dashboard and AI assistant for generating and analyzing **100-product, 5-year monthly Profit & Loss** datasets.

## Features
- **Chatbot Spreadsheet Generator**: Enter a natural-language prompt (e.g., *"Create a Google Sheet for 100 products over 5 years profit and loss"*) to generate 6,000 monthly records (`PRD-001` to `PRD-100` across 60 months).
- **In-Spreadsheet AI Query Assistant**: Ask questions without writing manual formulas:
  - Total loss, total profit, and net P&L
  - Monthly and per-product averages
  - Multi-year product comparisons (*"Compare Product 1 and Product 5 over 5 years"*)
  - Top/worst performing products and per-product statistics
- **Interactive Bar & Line Graphs**: Toggle between Bar Graph and Line Graph views powered by Recharts.
- **Google Sheets & Local Exports**: Optional live sync to Google Sheets (`gspread`) plus one-click CSV and Excel (`.xlsx`) downloads.

## Running in VS Code

### 1. Backend (Python FastAPI)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### 2. Frontend (React + Vite)
Open a second terminal in VS Code:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser. (You can also run **Terminal -> Run Task -> Start Full Stack** in VS Code.)

### 3. Run Backend Tests
```bash
cd backend
pytest
```

## Optional: Enable Live Google Sheets Sync
1. Create a project in Google Cloud Console and enable **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account**, download the JSON key, and save it as `backend/service_account.json`.
3. Optionally set `GOOGLE_SHARE_EMAIL=your-email@gmail.com` in `backend/.env`.

## Deploying to GitHub
```bash
git init
git add .
git commit -m "Initial commit: AI Spreadsheet Assistant"
git branch -M main
git remote add origin https://github.com/<your-username>/spreadsheet-assistant.git
git push -u origin main
```
