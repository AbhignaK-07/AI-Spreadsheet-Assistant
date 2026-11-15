import React, { useEffect, useState } from "react";
import { FileSpreadsheet } from "lucide-react";
import {
  createSpreadsheet,
  createSpreadsheetFromText,
  fetchMonthlyStats,
  fetchProductStats,
  fetchSpreadsheetRows,
  queryAssistant,
  uploadSpreadsheetFile,
} from "./api";
import SidebarChatbot from "./components/SidebarChatbot";
import DashboardKPIs from "./components/DashboardKPIs";
import AnalyticsCharts from "./components/AnalyticsCharts";
import SpreadsheetGrid from "./components/SpreadsheetGrid";

export default function App() {
  const [spreadsheetId, setSpreadsheetId] = useState(null);
  const [summary, setSummary] = useState(null);
  const [rows, setRows] = useState([]);
  const [totalRows, setTotalRows] = useState(0);
  const [productStats, setProductStats] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [chartType, setChartType] = useState("bar");
  const [yearFilter, setYearFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! Generate a 100-product 5-year sheet, upload any Excel/CSV file for month-wise stats, or convert a text document into an Excel sheet.",
    },
  ]);

  const hydrateDashboard = async (sid, initialQuery = "Show month-wise statistics") => {
    const [gridRes, statsRes, monthRes, chartRes] = await Promise.all([
      fetchSpreadsheetRows(sid, { limit: 200 }),
      fetchProductStats(sid),
      fetchMonthlyStats(sid),
      queryAssistant({
        spreadsheet_id: sid,
        query: initialQuery,
        chart_type: chartType,
      }),
    ]);
    setRows(gridRes.rows);
    setTotalRows(gridRes.total);
    setProductStats(statsRes.products);
    setMonthlyStats(monthRes.months);
    setChartData(chartRes);
  };

  useEffect(() => {
    if (spreadsheetId) {
      fetchSpreadsheetRows(spreadsheetId, {
        year: yearFilter || undefined,
        search: searchTerm || undefined,
        limit: 200,
      }).then((res) => {
        setRows(res.rows);
        setTotalRows(res.total);
      });
    }
  }, [yearFilter, searchTerm]);

  const handleCreateFromPrompt = async (prompt, syncGoogleSheets) => {
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: prompt }]);
    try {
      const data = await createSpreadsheet({ prompt, sync_google_sheets: syncGoogleSheets });
      const sid = data.summary.spreadsheet_id;
      setSpreadsheetId(sid);
      setSummary(data.summary);
      await hydrateDashboard(sid, "Show overall profit and loss statistics");
      setMessages((prev) => [...prev, { role: "assistant", text: data.bot_message }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err?.response?.data?.detail || err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadFile = async (file) => {
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: `Uploaded file: ${file.name}` }]);
    try {
      const data = await uploadSpreadsheetFile(file);
      const sid = data.summary.spreadsheet_id;
      setSpreadsheetId(sid);
      setSummary(data.summary);
      await hydrateDashboard(sid, "Show month-wise statistics");
      setMessages((prev) => [...prev, { role: "assistant", text: data.bot_message }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Upload failed: ${err?.response?.data?.detail || err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleBuildFromText = async (payload) => {
    setLoading(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", text: `Convert text/doc to Excel: ${payload.title || "Document"}` },
    ]);
    try {
      const data = await createSpreadsheetFromText(payload);
      const sid = data.summary.spreadsheet_id;
      setSpreadsheetId(sid);
      setSummary(data.summary);
      await hydrateDashboard(sid, "Show month-wise statistics");
      setMessages((prev) => [...prev, { role: "assistant", text: data.bot_message }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Conversion failed: ${err?.response?.data?.detail || err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAskAssistant = async (query) => {
    if (!spreadsheetId) return;
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    try {
      const res = await queryAssistant({
        spreadsheet_id: spreadsheetId,
        query,
        chart_type: chartType,
      });
      setChartData(res);
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Query failed: ${err?.response?.data?.detail || err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2.5">
          <FileSpreadsheet className="w-6 h-6 text-indigo-600" />
          <div>
            <h1 className="text-base font-bold text-slate-900">AI Spreadsheet Assistant</h1>
            <p className="text-[11px] text-slate-500">
              {summary ? summary.title : "React + FastAPI + Pandas + Excel/Text Builder"}
            </p>
          </div>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 font-medium">
          {summary ? `${summary.num_products} Items · ${summary.total_rows.toLocaleString()} Rows` : "Ready"}
        </span>
      </header>

      <div className="flex flex-col lg:flex-row flex-1">
        <SidebarChatbot
          messages={messages}
          onCreateFromPrompt={handleCreateFromPrompt}
          onAskAssistant={handleAskAssistant}
          onUploadFile={handleUploadFile}
          onBuildFromText={handleBuildFromText}
          hasSpreadsheet={Boolean(spreadsheetId)}
          loading={loading}
        />

        <main className="flex-1 p-6 space-y-6 overflow-x-hidden">
          {!summary ? (
            <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
              <FileSpreadsheet className="w-12 h-12 text-indigo-500 mx-auto mb-3" />
              <h2 className="text-lg font-semibold text-slate-900">No Spreadsheet Loaded Yet</h2>
              <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                Generate a 100-product 5-year sheet, upload any Excel/CSV file for month-wise
                statistics, or convert raw text/documents into an Excel workbook.
              </p>
            </div>
          ) : (
            <>
              <DashboardKPIs summary={summary} />
              <AnalyticsCharts
                chartData={chartData}
                chartType={chartType}
                onChartTypeChange={setChartType}
              />
              <SpreadsheetGrid
                spreadsheetId={spreadsheetId}
                summary={summary}
                rows={rows}
                totalRows={totalRows}
                productStats={productStats}
                monthlyStats={monthlyStats}
                yearFilter={yearFilter}
                onYearFilterChange={setYearFilter}
                searchTerm={searchTerm}
                onSearchTermChange={setSearchTerm}
                onSelectProduct={(pid) => handleAskAssistant(`Show statistics for ${pid}`)}
              />
            </>
          )}
        </main>
      </div>
    </div>
  );
}