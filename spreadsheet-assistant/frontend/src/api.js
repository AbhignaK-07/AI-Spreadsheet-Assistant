import axios from "axios";

const API_HOST = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/$/, "")
  : "";

const api = axios.create({
  baseURL: `${API_HOST}/api`,
});

export async function createSpreadsheet(payload) {
  const { data } = await api.post("/spreadsheets/create", payload);
  return data;
}

export async function uploadSpreadsheetFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/spreadsheets/upload", formData);
  return data;
}

export async function createSpreadsheetFromText({ text, title, file }) {
  const formData = new FormData();
  if (text) formData.append("text", text);
  if (title) formData.append("title", title);
  if (file) formData.append("file", file);
  const { data } = await api.post("/spreadsheets/from-text", formData);
  return data;
}

export async function fetchSpreadsheetRows(spreadsheetId, params = {}) {
  const { data } = await api.get(`/spreadsheets/${spreadsheetId}/rows`, { params });
  return data;
}

export async function fetchProductStats(spreadsheetId) {
  const { data } = await api.get(`/spreadsheets/${spreadsheetId}/stats`);
  return data;
}

export async function fetchMonthlyStats(spreadsheetId) {
  const { data } = await api.get(`/spreadsheets/${spreadsheetId}/monthly-stats`);
  return data;
}

export async function queryAssistant(payload) {
  const { data } = await api.post("/assistant/query", payload);
  return data;
}