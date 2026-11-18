
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8001",
  timeout: 90000,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function checkHealth() {
  const response = await api.get("/health");
  return response.data;
}

export async function getTools() {
  const response = await api.get("/tools");
  return response.data;
}

export async function sendMessage(message, sessionId) {
  const response = await api.post("/chat", {
    message,
    session_id: sessionId,
  });
  return response.data;
}

export async function getHistory(sessionId) {
  const response = await api.get(`/history/${sessionId}`);
  return response.data;
}

export async function deleteHistory(sessionId) {
  const response = await api.delete(`/history/${sessionId}`);
  return response.data;
}

export default api;
