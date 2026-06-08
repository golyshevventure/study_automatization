import { useState, useMemo } from "react";
import type { CalendarEvent } from "../../types/calendar";
import EventDetailModal from "./EventDetailModal";

interface Props {
  currentDate: Date;
  days: Record<string, CalendarEvent[]>;
}

const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function formatDayMonth(date: Date): string {
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

/** Одно событие в колонке недели. */
function WeekEventItem({ event, onClick }: { event: CalendarEvent; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left px-2 py-1.5 rounded-lg mb-1 transition-all active:scale-95"
      style={{
        background: `${event.color}15`,
        borderLeft: `3px solid ${event.color}`,
      }}
    >
      <p className="text-[11px] font-medium truncate" style={{ color: "#fff" }}>
        {event.title}
      </p>
      {event.time_str && (
        <p className="text-[10px]" style={{ color: event.color }}>
          {event.time_str}
        </p>
      )}
    </button>
  );
}

export default function CalendarWeekView({ currentDate, days }: Props) {
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  const weekDays = useMemo(() => {
    const d = new Date(currentDate);
    const day = d.getDay() || 7;
    const monday = new Date(d);
    monday.setDate(d.getDate() - day + 1);

    const result: { date: Date; weekday: string; events: CalendarEvent[] }[] = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      const key = date.toISOString().split("T")[0];
      result.push({
        date,
        weekday: WEEKDAYS[i],
        events: days[key] ?? [],
      });
    }
    return result;
  }, [currentDate, days]);

  const today = new Date();

  // Разделяем события на "занятия" (с time_str) и "дедлайны" (без time_str)
  const deadlines: { date: Date; events: CalendarEvent[] }[] = [];
  weekDays.forEach((d) => {
    const dl = d.events.filter((e) => !e.time_str && (e.event_type === "task" || e.event_type === "test"));
    if (dl.length > 0) deadlines.push({ date: d.date, events: dl });
  });

  return (
    <div className="px-2">
      {/* Header row */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {weekDays.map((d, i) => {
          const isToday = isSameDay(d.date, today);
          return (
            <div key={i} className="text-center py-2">
              <p className="text-[10px] font-medium" style={{ color: isToday ? "#B794F6" : "#64748B" }}>
                {d.weekday}
              </p>
              <p
                className="text-sm font-semibold mt-0.5"
                style={{ color: isToday ? "#fff" : "#CBD5E1" }}
              >
                {d.date.getDate()}
              </p>
            </div>
          );
        })}
      </div>

      {/* Events grid */}
      <div className="grid grid-cols-7 gap-1 min-h-[200px]">
        {weekDays.map((d, i) => (
          <div key={i} className="rounded-xl p-1" style={{ background: "rgba(15, 23, 42, 0.4)" }}>
            {d.events.map((e) => (
              <WeekEventItem
                key={e.id}
                event={e}
                onClick={() => setSelectedEvent(e)}
              />
            ))}
          </div>
        ))}
      </div>

      {/* Deadlines bar (как в YetAnotherCalendar) */}
      {deadlines.length > 0 && (
        <div
          className="mt-3 rounded-2xl p-3"
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            border: "1px solid rgba(249, 115, 22, 0.2)",
          }}
        >
          <p className="text-xs font-medium mb-2" style={{ color: "#F97316" }}>
            Дедлайны
          </p>
          <div className="flex flex-wrap gap-2">
            {deadlines.map((d) =>
              d.events.map((e) => (
                <button
                  key={e.id}
                  onClick={() => setSelectedEvent(e)}
                  className="text-left px-2.5 py-1.5 rounded-lg text-xs transition-all active:scale-95"
                  style={{
                    background: `${e.color}15`,
                    color: "#fff",
                    border: `1px solid ${e.color}30`,
                  }}
                >
                  <span style={{ color: e.color }}>{formatDayMonth(d.date)}</span>
                  {" — "}
                  {e.title}
                </button>
              ))
            )}
          </div>
        </div>
      )}

      <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}
