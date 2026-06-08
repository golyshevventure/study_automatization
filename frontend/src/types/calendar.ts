/** API-тип: событие в календаре. */
export interface CalendarEvent {
  id: string;
  event_type: "task" | "test" | "webinar";
  sub_type: "lesson" | "consultation" | "credit" | "exam";
  title: string;
  program_title: string | null;
  event_date: string | null; // YYYY-MM-DD
  status: "pending" | "approved" | "passed" | "overdue";
  source: "calendar" | "schedule" | "merged";
  color: string; // hex
  time_str: string | null; // HH:MM
  item_count: number;
}

/** Доступные фильтры. */
export type CalendarFilter = "lessons" | "works" | "control" | "all";

/** Вид календаря. */
export type CalendarView = "month" | "week";
