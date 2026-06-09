import { X, Plus, Clock, BookOpen, GraduationCap, CalendarDays, FileText } from "lucide-react";
import type { CalendarEvent } from "../../types/calendar";
import { formatFullDate } from "../../utils/date";

interface Props {
  date: Date | null;
  events: CalendarEvent[];
  onClose: () => void;
  onEventClick: (event: CalendarEvent) => void;
}

function EventIcon({ type, subType }: { type: string; subType: string }) {
  if (type === "task") return <FileText size={16} color={subType === "credit" || subType === "exam" ? "#EF4444" : "#F97316"} />;
  if (type === "test") return <CalendarDays size={16} color="#EAB308" />;
  if (subType === "exam" || subType === "credit") return <GraduationCap size={16} color="#EF4444" />;
  return <BookOpen size={16} color="#3B82F6" />;
}

function getTypeLabel(type: string, subType: string): string {
  if (type === "task") return "ДЗ";
  if (type === "test") return "Тест";
  if (subType === "exam") return "Экзамен";
  if (subType === "credit") return "Зачёт";
  if (subType === "consultation") return "Консультация";
  return "Занятие";
}

export default function DaySheet({ date, events, onClose, onEventClick }: Props) {
  if (!date) return null;

  // Сортируем: сначала с временем (по возрастанию), потом без времени
  const sorted = [...events].sort((a, b) => {
    if (a.time_str && b.time_str) return a.time_str.localeCompare(b.time_str);
    if (a.time_str) return -1;
    if (b.time_str) return 1;
    return 0;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center" onClick={onClose}>
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" />

      {/* Sheet */}
      <div
        className="relative w-full max-w-[420px] rounded-t-[32px] p-5 animate-in slide-in-from-bottom duration-300"
        style={{ background: "#0B1120", borderTop: "1px solid rgba(138, 43, 226, 0.2)", maxHeight: "75vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Handle */}
        <div className="flex justify-center mb-3">
          <div className="w-10 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.2)" }} />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold" style={{ color: "#fff" }}>
            {formatFullDate(date)}
          </h3>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-white/5 transition-colors">
            <X size={18} color="#94A3B8" />
          </button>
        </div>

        {/* Add button */}
        <button
          onClick={() => alert("Добавление событий появится в следующем обновлении!")}
          className="w-full py-2.5 rounded-xl text-sm font-medium flex items-center justify-center gap-2 mb-4 transition-all active:scale-95"
          style={{
            background: "rgba(138, 43, 226, 0.15)",
            color: "#B794F6",
            border: "1px solid rgba(138, 43, 226, 0.3)",
          }}
        >
          <Plus size={16} />
          Добавить событие
        </button>

        {/* Events list */}
        {sorted.length === 0 ? (
          <p className="text-sm text-center py-6" style={{ color: "#64748B" }}>
            Нет событий в этот день
          </p>
        ) : (
          <div className="flex flex-col gap-2 overflow-y-auto" style={{ maxHeight: "50vh" }}>
            {sorted.map((event) => (
              <button
                key={event.id}
                onClick={() => onEventClick(event)}
                className="flex items-center gap-3 p-3 rounded-xl text-left transition-all active:scale-[0.98] hover:bg-white/5"
                style={{
                  background: `${event.color}10`,
                  border: `1px solid ${event.color}20`,
                }}
              >
                <div
                  className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                  style={{ background: `${event.color}20` }}
                >
                  <EventIcon type={event.event_type} subType={event.sub_type} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: "#fff" }}>
                    {event.title}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[11px]" style={{ color: event.color }}>
                      {getTypeLabel(event.event_type, event.sub_type)}
                    </span>
                    {event.time_str && (
                      <span className="text-[11px] flex items-center gap-0.5" style={{ color: "#94A3B8" }}>
                        <Clock size={10} />
                        {event.time_str}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
