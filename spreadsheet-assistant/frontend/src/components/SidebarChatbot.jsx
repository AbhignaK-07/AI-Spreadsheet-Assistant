import React, { useRef, useState } from "react";
import { Send, Sparkles, FileSpreadsheet, Bot, Upload, FileText, X } from "lucide-react";

const QUICK_QUERIES = [
  "Show month-wise statistics",
  "What is the total loss?",
  "What is the total average?",
  "Compare Product 1 and Product 5 over 5 years",
  "Top 10 most profitable products",
  "Worst 10 loss-making products",
];

export default function SidebarChatbot({
  messages,
  onCreateFromPrompt,
  onAskAssistant,
  onUploadFile,
  onBuildFromText,
  hasSpreadsheet,
  loading,
}) {
  const [input, setInput] = useState("");
  const [syncGoogleSheets, setSyncGoogleSheets] = useState(false);
  const [showTextModal, setShowTextModal] = useState(false);
  const [rawText, setRawText] = useState(
    "Product: Laptop, Month: Jan, Revenue: 12000, Cost: 8500\nProduct: Laptop, Month: Feb, Revenue: 9800, Cost: 10200\nProduct: Phone, Month: Jan, Revenue: 15000, Cost: 11000"
  );
  const [docTitle, setDocTitle] = useState("Text to Excel Report");
  const excelInputRef = useRef(null);
  const textFileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");

    const lower = text.toLowerCase();
    const isCreation =
      !hasSpreadsheet ||
      lower.includes("create") ||
      lower.includes("generate") ||
      lower.includes("new spreadsheet");

    if (isCreation) {
      onCreateFromPrompt(text, syncGoogleSheets);
    } else {
      onAskAssistant(text);
    }
  };

  const handleExcelSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadFile(file);
      e.target.value = "";
    }
  };

  const handleTextFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onBuildFromText({ file, title: file.name });
      setShowTextModal(false);
      e.target.value = "";
    }
  };

  return (
    <aside className="w-full lg:w-96 bg-white border-r border-slate-200 flex flex-col h-[calc(100vh-57px)] sticky top-[57px]">
      <div className="p-4 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Spreadsheet AI Chatbot</h2>
            <p className="text-xs text-slate-500">Create, upload Excel, or convert text</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`rounded-xl p-3 text-xs leading-relaxed ${
              m.role === "user"
                ? "bg-indigo-600 text-white ml-8"
                : "bg-slate-100 text-slate-800 mr-4"
            }`}
          >
            {m.text}
          </div>
        ))}
        {loading && (
          <div className="bg-slate-100 text-slate-500 rounded-xl p-3 text-xs mr-4 animate-pulse">
            Processing spreadsheet data...
          </div>
        )}
      </div>

      <div className="p-3 border-t border-slate-100 bg-slate-50/70 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <input
            ref={excelInputRef}
            type="file"
            accept=".xlsx,.xls,.csv,.txt,.md"
            onChange={handleExcelSelect}
            className="hidden"
          />
          <button
            type="button"
            disabled={loading}
            onClick={() => excelInputRef.current?.click()}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg border border-slate-200 bg-white text-slate-700 text-xs font-medium hover:border-indigo-400 hover:text-indigo-600 disabled:opacity-50"
          >
            <Upload className="w-3.5 h-3.5" />
            Upload Excel/CSV
          </button>

          <button
            type="button"
            disabled={loading}
            onClick={() => setShowTextModal(true)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg border border-slate-200 bg-white text-slate-700 text-xs font-medium hover:border-indigo-400 hover:text-indigo-600 disabled:opacity-50"
          >
            <FileText className="w-3.5 h-3.5" />
            Text/Doc → Excel
          </button>
        </div>

        {!hasSpreadsheet ? (
          <button
            type="button"
            disabled={loading}
            onClick={() =>
              onCreateFromPrompt(
                "Create a Google Sheet for 100 products with monthly profit and loss over 5 years",
                syncGoogleSheets
              )
            }
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            <FileSpreadsheet className="w-4 h-4" />
            Generate 100-Product 5-Year Sheet
          </button>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {QUICK_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                disabled={loading}
                onClick={() => onAskAssistant(q)}
                className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-700 hover:border-indigo-400 hover:text-indigo-600 transition"
              >
                <Sparkles className="w-3 h-3 inline mr-1 text-indigo-500" />
                {q}
              </button>
            ))}
          </div>
        )}

        <label className="flex items-center gap-2 text-[11px] text-slate-600 pt-1">
          <input
            type="checkbox"
            checked={syncGoogleSheets}
            onChange={(e) => setSyncGoogleSheets(e.target.checked)}
            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
          />
          Also push to Google Sheets (requires service_account.json)
        </label>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              hasSpreadsheet
                ? "Ask: month-wise stats, total loss, compare..."
                : "e.g., Create Google Sheet for 100 products over 5 years"
            }
            className="flex-1 px-3 py-2 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {showTextModal && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Convert Text or Document to Excel</h3>
              <button type="button" onClick={() => setShowTextModal(false)}>
                <X className="w-4 h-4 text-slate-500" />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Paste CSV, pipe-delimited tables, or &ldquo;Key: Value&rdquo; lines—or upload a <code>.txt</code> / <code>.md</code> file.
            </p>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder="Spreadsheet Title"
              className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg"
            />
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono border border-slate-200 rounded-lg"
            />
            <div className="flex items-center justify-between gap-2">
              <input
                ref={textFileInputRef}
                type="file"
                accept=".txt,.md,.csv,.tsv"
                onChange={handleTextFileSelect}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => textFileInputRef.current?.click()}
                className="px-3 py-2 text-xs font-medium rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
              >
                Upload .txt / .md File
              </button>
              <button
                type="button"
                onClick={() => {
                  onBuildFromText({ text: rawText, title: docTitle });
                  setShowTextModal(false);
                }}
                className="px-4 py-2 text-xs font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Build Excel &amp; Analyze
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}