/**
 * API-клиент для модуля «Ближайшие события и дедлайны».
 */

import type { DeadlineEvent, DeadlineListResponse, DeadlineSyncResponse, DeadlineFilter } from "../types/deadline";

const API_BASE = "http://localhost:8000/api";

async function fetchWithAuth(path: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  return res;
}

/** Синхронизировать дедлайны с Netology API. */
export async function syncDeadlines(): Promise<DeadlineSyncResponse> {
  const res = await fetchWithAuth("/deadlines/sync", { method: "POST" });
  return res.json();
}

/** Получить список будущих событий. */
export async function getDeadlines(
  filter: DeadlineFilter = "all",
  limit = 100,
  offset = 0,
  program?: string
): Promise<DeadlineListResponse> {
  const params = new URLSearchParams({ filter, limit: String(limit), offset: String(offset) });
  if (program) params.set("program", program);
  const res = await fetchWithAuth(`/deadlines?${params}`);
  return res.json();
}

/** Получить детали одного события. */
export async function getDeadlineDetail(id: string): Promise<DeadlineEvent> {
  const res = await fetchWithAuth(`/deadlines/${id}`);
  return res.json();
}
