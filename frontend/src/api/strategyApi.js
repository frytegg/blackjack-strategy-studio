// frontend/src/api/strategyApi.js

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function fetchStrategy(config) {
  const res = await fetch(`${API_BASE_URL}/strategy`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(config)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Erreur API /strategy: ${res.status} ${text}`);
  }

  return res.json();
}

export async function downloadStrategyPdf(config) {
  const res = await fetch(`${API_BASE_URL}/strategy/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(config)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Erreur API /strategy/pdf: ${res.status} ${text}`);
  }

  return res.blob();
}
