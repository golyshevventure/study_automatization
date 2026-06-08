/**
 * API-клиент для модуля «Календарь v2.0».
 */

import type { CalendarEvent, CalendarFilter } from "../types/calendar";

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

export interface CalendarMonthResponse {
  year: number;
  month: number;
  filter: string;
  days: Record<string, CalendarEvent[]>;
  total: number;
}

export interface CalendarWeekResponse {
  year: number;
  week: number;
  filter: string;
  days: Record<string, CalendarEvent[]>;
  total: number;
}

/** Получить события за месяц. */
export async function getCalendarMonth(
  year: number,
  month: number,
  filter: CalendarFilter = "all"
): Promise<CalendarMonthResponse> {
  const params = new URLSearchParams({
    year: String(year),
    month: String(month),
    filter,
  });
  const res = await fetchWithAuth(`/calendar/month?${params}`);
  return res.json();
}

/** Получить события за неделю (ISO). */
export async function getCalendarWeek(
  year: number,
  week: number,
  filter: CalendarFilter = "all"
): Promise<CalendarWeekResponse> {
  const params = new URLSearchParams({
    year: String(year),
    week: String(week),
    filter,
  });
  const res = await fetchWithAuth(`/calendar/week?${params}`);
  return res.json();
}
