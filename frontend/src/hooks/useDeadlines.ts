import { useState, useEffect, useCallback, useRef } from "react";
import type { DeadlineItem, EnrichedDeadlineItem, DeadlineFilter } from "../types/deadline";
import { getTopDeadlines, getAllDeadlines, getNowMsk, getDeadlineCounts } from "../utils/deadlineUtils";
import { realDeadlines } from "../data/realDeadlines";

/**
 * Интервал обновления данных по умолчанию — 1 час (в миллисекундах).
 */
const DEFAULT_REFRESH_INTERVAL = 60 * 60 * 1000;

/**
 * Режим работы хука:
 *   - "top3": возвращает только топ-3 дедлайна (для главной страницы)
 *   - "all": возвращает все дедлайны (для страницы «Все дедлайны»)
 */
type UseDeadlinesMode = "top3" | "all";

interface UseDeadlinesResult {
  /** Текущий список дедлайнов для отображения */
  deadlines: EnrichedDeadlineItem[];
  /** Время последнего обновления */
  lastUpdated: Date | null;
  /** Идёт ли сейчас загрузка/обновление */
  isLoading: boolean;
  /** Форсированно перезапросить данные */
  refetch: () => void;
  /** Количества по фильтрам */
  counts: { all: number; normal: number; urgent: number; overdue: number };
}

/**
 * Кастомный хук для получения и автообновления дедлайнов.
 *
 * Логика:
 *   1. При mount выполняется первый запрос данных (immediate)
 *   2. Запускается setInterval с заданным интервалом
 *   3. При каждом тике:
 *        - имитируем fetch (сейчас — реальные данные из кэша API)
 *        - пересчитываем фильтрацию, сортировку, обогащение
 *        - обновляем state
 *   4. При unmount — clearInterval
 *
 * В будущем заменить fetcher на реальный API-запрос:
 *   const response = await fetch("/backend/api/user/student_learning/calendar");
 *   const raw = await response.json();
 *   return extractDeadlines(raw);
 */
export function useDeadlines(
  mode: UseDeadlinesMode = "top3",
  filter: DeadlineFilter = "all",
  refreshInterval: number = DEFAULT_REFRESH_INTERVAL
): UseDeadlinesResult {
  const [deadlines, setDeadlines] = useState<EnrichedDeadlineItem[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [counts, setCounts] = useState({ all: 0, normal: 0, urgent: 0, overdue: 0 });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /**
   * Симуляция получения данных с сервера.
   * В текущей реализации возвращает реальные данные из кэша API.
   */
  const fetchDeadlines = useCallback(async (): Promise<DeadlineItem[]> => {
    const delay = 200 + Math.random() * 400;
    await new Promise((resolve) => setTimeout(resolve, delay));

    // TODO: заменить на реальный API-запрос
    return realDeadlines;
  }, []);

  /**
   * Основная функция обновления данных.
   */
  const refetch = useCallback(async () => {
    setIsLoading(true);

    try {
      const rawItems = await fetchDeadlines();
      const now = getNowMsk();

      let enriched: EnrichedDeadlineItem[];
      if (mode === "top3") {
        enriched = getTopDeadlines(rawItems, 3, now);
      } else {
        enriched = getAllDeadlines(rawItems, filter, now);
      }

      setDeadlines(enriched);
      setLastUpdated(now);
      setCounts(getDeadlineCounts(rawItems, now));
    } catch (err) {
      console.error("[useDeadlines] Ошибка получения дедлайнов:", err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchDeadlines, mode, filter]);

  // Первичная загрузка + interval
  useEffect(() => {
    refetch();

    intervalRef.current = setInterval(() => {
      refetch();
    }, refreshInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [refetch, refreshInterval]);

  return {
    deadlines,
    lastUpdated,
    isLoading,
    refetch,
    counts,
  };
}
