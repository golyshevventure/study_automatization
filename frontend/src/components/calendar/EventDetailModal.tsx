import { X, Clock, BookOpen, GraduationCap, CalendarDays, FileText, ExternalLink, CheckCircle2 } from "lucide-react";
import type { CalendarEvent } from "../../types/calendar";

interface Props {
  event: CalendarEvent | null;
  onClose: () => void;
}

function EventIcon({ type, subType }: { type: string; subType: string }) {
  if (type === "task") return <FileText size={20} color={subType === "credit" || subType === "exam" ? "#EF4444" : "#F97316"} />;
  if (type === "test") return <CalendarDays size={20} color="#EAB308" />;
  if (subType === "exam" || subType === "credit") return <GraduationCap size={20} color="#EF4444" />;
  return <BookOpen size={20} color="#3B82F6" />;
}

function getTypeLabel(type: string, subType: string): string {
  if (type === "task") return "Домашнее задание";
  if (type === "test") return "Тест";
  if (subType === "exam") return "Экзамен";
  if (subType === "credit") return "Зачёт";
  if (subType === "consultation") return "Консультация";
  return "Занятие";
}

function formatDate(dateStr: string | null, timeStr: string | null): string {
  if (!dateStr) return "Дата не указана";
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const formatted = date.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
  if (timeStr) return `${formatted}, ${timeStr} МСК`;
  return formatted;
}

export default function EventDetailModal({ event, onClose }: Props) {
  if (!event) return null;

  const isPassed = event.status === "passed" || event.status === "approved";

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center"
      onClick={onClose}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Sheet */}
      <div
        className="relative w-full max-w-[420px] rounded-t-[32px] p-6 animate-in slide-in-from-bottom"
        style={{ background: "#0B1120", borderTop: "1px solid rgba(138, 43, 226, 0.2)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="flex justify-center mb-4">
          <div className="w-10 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.2)" }} />
        </div>

        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/5 transition-colors"
        >
          <X size={18} color="#94A3B8" />
        </button>

        {/* Icon + Type */}
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${event.color}20` }}
          >
            <EventIcon type={event.event_type} subType={event.sub_type} />
          </div>
          <div>
            <p className="text-xs font-medium" style={{ color: event.color }}>
              {getTypeLabel(event.event_type, event.sub_type)}
            </p>
            {isPassed && (
              <span className="text-xs font-medium flex items-center gap-1" style={{ color: "#10B981" }}>
                <CheckCircle2 size={10} />
                Выполнено
              </span>
            )}
          </div>
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold mb-1" style={{ color: "#fff" }}>
          {event.title}
        </h3>

        {/* Program */}
        {event.program_title && (
          <p className="text-xs mb-4" style={{ color: "#64748B" }}>
            {event.program_title}
          </p>
        )}

        {/* Date */}
        <div className="flex items-center gap-2 mb-4">
          <Clock size={16} color="#94A3B8" />
          <span className="text-sm" style={{ color: "#94A3B8" }}>
            {formatDate(event.event_date, event.time_str)}
          </span>
        </div>

        {/* Variants */}
        {event.item_count > 1 && (
          <div
            className="rounded-xl px-3 py-2 mb-4 text-xs"
            style={{ background: "rgba(183, 148, 246, 0.1)", color: "#B794F6" }}
          >
            {event.item_count} вариант{event.item_count > 1 ? "а" : ""} (группы / потоки)
          </div>
        )}

        {/* Action */}
        <button
          className="w-full py-3 rounded-2xl text-sm font-medium flex items-center justify-center gap-2 transition-all active:scale-95"
          style={{
            background: `${event.color}20`,
            color: event.color,
            border: `1px solid ${event.color}40`,
          }}
          onClick={() => {
            // TODO: открыть ссылку на задание/вебинар если есть
            window.open("https://netology.ru", "_blank");
          }}
        >
          <ExternalLink size={14} />
          Открыть в Netology
        </button>
      </div>
    </div>
  );
}
