import { Clock, CheckCircle2, BookOpen, GraduationCap, CalendarDays, FileText } from "lucide-react";
import type { DeadlineEvent } from "../types/deadline";

/** Плюрализация русских слов (вариант/варианта/вариантов). */
function pluralize(count: number, one: string, few: string, many: string): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod100 >= 11 && mod100 <= 19) return `${count} ${many}`;
  if (mod10 === 1) return `${count} ${one}`;
  if (mod10 >= 2 && mod10 <= 4) return `${count} ${few}`;
  return `${count} ${many}`;
}

/** Проверяет, что событие уже прошло (дата < сегодня). */
function isEventPast(event: DeadlineEvent): boolean {
  if (!event.event_date) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const [year, month, day] = event.event_date.split("-").map(Number);
  const eventDate = new Date(year, month - 1, day);
  return eventDate < today;
}

interface DeadlineCardProps {
  event: DeadlineEvent;
}

/** Иконка по типу события. */
function EventIcon({ type, subType }: { type: string; subType: string }) {
  if (type === "task") return <FileText size={16} color="#F59E0B" />;
  if (type === "test") return <CalendarDays size={16} color="#F59E0B" />;
  if (subType === "exam") return <GraduationCap size={16} color="#EF4444" />;
  if (subType === "credit") return <GraduationCap size={16} color="#EF4444" />;
  return <BookOpen size={16} color="#3B82F6" />;
}

/** Цвет полоски-индикатора. */
function getStripColor(type: string, subType: string, status: string): string {
  if (status === "passed" || status === "approved") return "#10B981";
  if (type === "task" || type === "test") return "#F59E0B";
  if (subType === "exam") return "#EF4444";
  if (subType === "credit") return "#EF4444";
  return "#3B82F6";
}

/** Подпись типа события. */
function getTypeLabel(type: string, subType: string): string {
  if (type === "task") return "ДЗ / Работа";
  if (type === "test") return "Тест";
  if (subType === "exam") return "Экзамен";
  if (subType === "credit") return "Зачёт";
  if (subType === "consultation") return "Консультация";
  return "Занятие";
}

/** Форматирование даты. */
function formatDate(dateStr: string | null, timeStr: string | null): string {
  if (!dateStr) return "Дата не указана";
  const [year, month, day] = dateStr.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  const formatted = date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
  });
  if (timeStr) {
    const [h, m] = timeStr.split(":");
    return `${formatted}, ${h}:${m} МСК`;
  }
  return formatted;
}

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

export default function DeadlineCard({ event }: DeadlineCardProps) {
  const stripColor = getStripColor(event.event_type, event.sub_type, event.status);
  // "Выполнено" показываем только если статус passed/approved И событие уже прошло
  // (для зачётов/экзаменов статус может приходить заранее из API, но бейдж неактуален до даты)
  const isPassed =
    (event.status === "passed" || event.status === "approved") && isEventPast(event);

  return (
    <div
      className="rounded-2xl p-4 flex items-start gap-3 transition-transform active:scale-[0.98]"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        boxShadow: neonShadow,
        opacity: isPassed ? 0.75 : 1,
      }}
    >
      {/* Левая цветная полоска */}
      <div
        className="w-1.5 self-stretch rounded-full shrink-0"
        style={{
          background: stripColor,
          boxShadow: `0 0 8px ${stripColor}66`,
        }}
      />

      <div className="flex-1 min-w-0">
        {/* Название программы */}
        {event.program_title && (
          <p
            className="text-xs font-medium uppercase tracking-wider mb-1 truncate"
            style={{ color: "#64748B" }}
          >
            {event.program_title}
          </p>
        )}

        {/* Название события */}
        <p className="text-sm font-medium leading-snug" style={{ color: "#fff" }}>
          {event.title}
        </p>

        {/* Тип + статус */}
        <div className="flex items-center gap-2 mt-1.5">
          <EventIcon type={event.event_type} subType={event.sub_type} />
          <span className="text-xs" style={{ color: "#94A3B8" }}>
            {getTypeLabel(event.event_type, event.sub_type)}
          </span>
          {isPassed && (
            <span
              className="text-xs font-medium px-1.5 py-0.5 rounded-full flex items-center gap-1"
              style={{
                background: "rgba(16, 185, 129, 0.15)",
                color: "#10B981",
              }}
            >
              <CheckCircle2 size={10} />
              Выполнено
            </span>
          )}
          {event.item_count > 1 && (
            <span
              className="text-xs font-medium px-1.5 py-0.5 rounded-full"
              style={{
                background: "rgba(183, 148, 246, 0.15)",
                color: "#B794F6",
              }}
            >
              {pluralize(event.item_count, "вариант", "варианта", "вариантов")}
            </span>
          )}
        </div>

        {/* Дата */}
        <div className="flex items-center gap-1.5 mt-2.5">
          <Clock size={14} color={isPassed ? "#10B981" : "#94A3B8"} />
          <span className="text-xs font-medium" style={{ color: isPassed ? "#10B981" : "#94A3B8" }}>
            {formatDate(event.event_date, event.event_time)}
          </span>
        </div>
      </div>
    </div>
  );
}
