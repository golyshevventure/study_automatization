import { useState, useCallback, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import type { CalendarEvent, CalendarFilter, CalendarView } from "../types/calendar";
import { getCalendarMonth, getCalendarWeek, type CalendarMonthResponse, type CalendarWeekResponse } from "../api/calendar";
import { syncDeadlines } from "../api/deadlines";

interface UseCalendarResult {
  events: CalendarEvent[];
  days: Record<string, CalendarEvent[]>;
  total: number;
  isLoading: boolean;
  error: string | null;
  view: CalendarView;
  setView: (v: CalendarView) => void;
  currentDate: Date;
  goToPrev: () => void;
  goToNext: () => void;
  goToToday: () => void;
  filter: CalendarFilter;
  setFilter: (f: CalendarFilter) => void;
  isSyncing: boolean;
  doSync: () => void;
  doSilentSync: () => Promise<void>;
}

const FILTER_LABELS: Record<CalendarFilter, string> = {
  lessons: "Занятия",
  works: "Работы",
  control: "Контроль",
  all: "Все",
};

const VIEW_LABELS: Record<CalendarView, string> = {
  month: "Месяц",
  week: "Неделя",
};

/** Получить ISO-неделю из даты. */
function getISOWeek(date: Date): { year: number; week: number } {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((+d - +yearStart) / 86400000 + 1) / 7);
  return { year: d.getUTCFullYear(), week };
}

export function useCalendar(): UseCalendarResult {
  const [view, setView] = useState<CalendarView>("month");
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [filter, setFilter] = useState<CalendarFilter>("all");
  const [error, setError] = useState<string | null>(null);

  const silentSyncLock = useRef(false);

  const { year, week } = getISOWeek(currentDate);
  const month = currentDate.getMonth() + 1;
  const yearMonth = currentDate.getFullYear();

  const queryKey =
    view === "month"
      ? ["calendar", "month", yearMonth, month, filter]
      : ["calendar", "week", year, week, filter];

  const queryFn = async (): Promise<CalendarMonthResponse | CalendarWeekResponse> => {
    if (view === "month") {
      return getCalendarMonth(yearMonth, month, filter);
    }
    return getCalendarWeek(year, week, filter);
  };

  const {
    data,
    isLoading,
    refetch,
  } = useQuery<CalendarMonthResponse | CalendarWeekResponse, Error>({
    queryKey,
    queryFn,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  const syncMutation = useMutation({
    mutationFn: syncDeadlines,
    onSuccess: () => refetch(),
    onError: (err: Error) => setError(err.message),
  });

  const doSync = useCallback(() => {
    setError(null);
    syncMutation.mutate();
  }, [syncMutation]);

  const doSilentSync = useCallback(async () => {
    if (silentSyncLock.current) return;
    silentSyncLock.current = true;
    try {
      await syncDeadlines();
      await refetch();
    } catch (e) {
      console.warn("[Calendar] Silent sync failed:", e);
    } finally {
      silentSyncLock.current = false;
    }
  }, [refetch]);

  const goToPrev = useCallback(() => {
    setCurrentDate((d) => {
      const nd = new Date(d);
      if (view === "month") {
        nd.setMonth(nd.getMonth() - 1);
      } else {
        nd.setDate(nd.getDate() - 7);
      }
      return nd;
    });
  }, [view]);

  const goToNext = useCallback(() => {
    setCurrentDate((d) => {
      const nd = new Date(d);
      if (view === "month") {
        nd.setMonth(nd.getMonth() + 1);
      } else {
        nd.setDate(nd.getDate() + 7);
      }
      return nd;
    });
  }, [view]);

  const goToToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  // Дни и события
  const days = (data as CalendarMonthResponse | CalendarWeekResponse | undefined)?.days ?? {};
  const events = Object.values(days).flat() as CalendarEvent[];
  const total = (data as CalendarMonthResponse | CalendarWeekResponse | undefined)?.total ?? 0;

  return {
    events,
    days,
    total,
    isLoading,
    error: error || (syncMutation.error?.message ?? null),
    view,
    setView,
    currentDate,
    goToPrev,
    goToNext,
    goToToday,
    filter,
    setFilter,
    isSyncing: syncMutation.isPending,
    doSync,
    doSilentSync,
  };
}

export { FILTER_LABELS, VIEW_LABELS, getISOWeek };
