/** API-тип: сгруппированное событие (дедлайн / зачёт / экзамен / занятие). */
export interface DeadlineEvent {
  id: string;
  event_type: "task" | "test" | "webinar";
  sub_type: "lesson" | "consultation" | "credit" | "exam";
  title: string;
  program_title: string | null;
  event_date: string | null; // YYYY-MM-DD
  event_time: string | null; // HH:MM:SS
  status: "pending" | "approved" | "passed" | "overdue";
  source: "calendar" | "schedule" | "merged";
  item_count: number;
}

/** Доступные фильтры. */
export type DeadlineFilter = "lessons" | "works" | "control" | "all";

/** Ответ API на список событий. */
export interface DeadlineListResponse {
  events: DeadlineEvent[];
  total: number;
  filter: DeadlineFilter;
}

/** Ответ API на синхронизацию. */
export interface DeadlineSyncResponse {
  synced: number;
  duration_ms: number;
  message: string;
}
