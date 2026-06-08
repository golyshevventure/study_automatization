import { useState, useCallback, useRef } from "react";
import { useInfiniteQuery, useMutation } from "@tanstack/react-query";
import type { DeadlineEvent, DeadlineFilter } from "../types/deadline";
import { getDeadlines, syncDeadlines } from "../api/deadlines";

interface UseDeadlinesResult {
  events: DeadlineEvent[];
  total: number;
  isLoading: boolean;
  isFetchingMore: boolean;
  isSyncing: boolean;
  hasMore: boolean;
  error: string | null;
  refetch: () => void;
  loadMore: () => void;
  doSync: () => void;
  doSilentSync: () => Promise<void>;
}

const FILTER_LABELS: Record<DeadlineFilter, string> = {
  lessons: "Занятия",
  works: "Работы",
  control: "Контроль",
  all: "Все",
};

const PAGE_SIZE = 20;

/** Проверяет, что событие не в прошлом (защита от протухших данных в кэше). */
function isEventUpcoming(event: DeadlineEvent): boolean {
  if (!event.event_date) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const [year, month, day] = event.event_date.split("-").map(Number);
  const eventDate = new Date(year, month - 1, day);
  return eventDate >= today;
}

export function useDeadlines(
  filter: DeadlineFilter = "all",
  limit = PAGE_SIZE,
  program?: string
): UseDeadlinesResult {
  const [error, setError] = useState<string | null>(null);

  const {
    data,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    refetch,
  } = useInfiniteQuery({
    queryKey: ["deadlines", filter, limit, program],
    queryFn: ({ pageParam = 0 }) => getDeadlines(filter, limit, pageParam, program),
    getNextPageParam: (lastPage, allPages) => {
      const loaded = allPages.reduce((sum, p) => sum + p.events.length, 0);
      return loaded < lastPage.total ? loaded : undefined;
    },
    initialPageParam: 0,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    gcTime: 10 * 60 * 1000, // 10 минут — кэш очищается после размонтирования
    retry: 1,
  });

  const silentSyncLock = useRef(false);

  const syncMutation = useMutation({
    mutationFn: syncDeadlines,
    onSuccess: () => {
      refetch();
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const doSync = useCallback(() => {
    setError(null);
    syncMutation.mutate();
  }, [syncMutation]);

  const doSilentSync = useCallback(async () => {
    if (silentSyncLock.current) return;
    silentSyncLock.current = true;

    const attempt = async (retriesLeft: number): Promise<void> => {
      try {
        await syncDeadlines();
        await refetch();
      } catch (e) {
        if (retriesLeft > 0) {
          console.warn(
            `[SilentSync] Повторная попытка через 3с... (${retriesLeft} осталось)`
          );
          await new Promise((r) => setTimeout(r, 3000));
          return attempt(retriesLeft - 1);
        }
        console.warn("[SilentSync] Фоновая синхронизация не удалась:", e);
      }
    };

    try {
      await attempt(3);
    } finally {
      silentSyncLock.current = false;
    }
  }, [refetch]);

  // Дедупликация + фильтрация прошедших событий (защита от протухшего кэша)
  const events =
    data?.pages
      .flatMap((p) => p.events)
      .filter(isEventUpcoming)
      .filter((e, idx, arr) => arr.findIndex((x) => x.id === e.id) === idx) ?? [];
  const total = data?.pages[0]?.total ?? 0;

  return {
    events,
    total,
    isLoading,
    isFetchingMore: isFetchingNextPage,
    isSyncing: syncMutation.isPending,
    hasMore: !!hasNextPage,
    error: error || (syncMutation.error?.message ?? null),
    refetch,
    loadMore: fetchNextPage,
    doSync,
    doSilentSync,
  };
}

export { FILTER_LABELS };
export type { DeadlineFilter };
