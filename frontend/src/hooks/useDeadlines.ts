import { useState, useCallback } from "react";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
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
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const syncMutation = useMutation({
    mutationFn: syncDeadlines,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deadlines"] });
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
    try {
      await syncDeadlines();
      queryClient.invalidateQueries({ queryKey: ["deadlines"] });
    } catch (e) {
      // Бесшумно — пользователь не должен видеть ошибку фоновой синхронизации
      console.warn("[SilentSync] Фоновая синхронизация не удалась:", e);
    }
  }, [queryClient]);

  const events = data?.pages.flatMap((p) => p.events) ?? [];
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
