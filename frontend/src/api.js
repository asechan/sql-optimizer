// In Docker, nginx proxies /api → backend:8080. In dev, Vite proxies it.
const API_BASE = "/api";

export async function analyzeQuery(query) {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
