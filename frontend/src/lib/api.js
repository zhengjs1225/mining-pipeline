const BASE = import.meta.env.PROD ? "" : "http://localhost:8000";

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error("API unavailable");
  return res.json();
}

export async function query({ question, topK = 5, generateAnswer = true, sourceFilter, categoryFilter }) {
  const res = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      top_k: topK,
      generate_answer: generateAnswer,
      source_filter: sourceFilter || null,
      category_filter: categoryFilter || null,
    }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Query failed");
  }
  return res.json();
}

// ── Schedule API ────────────────────────────────────────
export async function listSchedules() {
  const res = await fetch(`${BASE}/schedules`);
  if (!res.ok) throw new Error("Failed to list schedules");
  return res.json();
}

export async function createSchedule(data) {
  const res = await fetch(`${BASE}/schedules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create schedule");
  return res.json();
}

export async function updateSchedule(id, data) {
  const res = await fetch(`${BASE}/schedules/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update schedule");
  return res.json();
}

export async function deleteSchedule(id) {
  const res = await fetch(`${BASE}/schedules/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete schedule");
  return res.json();
}
