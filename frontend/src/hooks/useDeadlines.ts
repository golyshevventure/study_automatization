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
    staleTime: Infinity,           // данные никогда не считаются устаревшими автоматически
    refetchOnWindowFocus: false,   // не refetch при возврате на вкладку
    retry: 1,
  });

  const silentSyncLock = useRef(false);

  const syncMutation = useMutation({
    mutationFn: syncDeadlines,
    onSuccess: () => {
      refetch(); // обновляем данные немедленно, без инвалидации других экранов
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
    try {
      await syncDeadlines();
      await refetch(); // фоновый refetch: isLoading остаётся false
    } catch (e) {
      console.warn("[SilentSync] Фоновая синхронизация не удалась:", e);
    } finally {
      silentSyncLock.current = false;
    }
  }, [refetch]);

  // Дедупликация: если бэкенд вернул дубли — убираем их по id
  const events =
    data?.pages
      .flatMap((p) => p.events)
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
