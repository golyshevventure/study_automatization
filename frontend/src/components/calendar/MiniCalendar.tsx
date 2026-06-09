import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getCalendarWeek } from "../../api/calendar";
import type { CalendarEvent } from "../../types/calendar";
import { formatDateKey } from "../../utils/date";
import DaySheet from "./DaySheet";
import EventDetailModal from "./EventDetailModal";

const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function getISOWeek(date: Date): { year: number; week: number } {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((+d - +yearStart) / 86400000 + 1) / 7);
  return { year: d.getUTCFullYear(), week };
}

export default function MiniCalendar() {
  const navigate = useNavigate();
  const today = new Date();
  const { year, week } = getISOWeek(today);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  const { data } = useQuery({
    queryKey: ["calendar", "week", year, week, "all"],
    queryFn: () => getCalendarWeek(year, week, "all"),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  const days = useMemo(() => {
    const d = new Date(today);
    const day = d.getDay() || 7;
    const monday = new Date(d);
    monday.setDate(d.getDate() - day + 1);

    const result: { date: Date; weekday: string; events: CalendarEvent[] }[] = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      const key = formatDateKey(date);
      result.push({
        date,
        weekday: WEEKDAYS[i],
        events: data?.days[key] ?? [],
      });
    }
    return result;
  }, [today, data]);

  return (
    <div
      className="rounded-2xl p-4 transition-transform active:scale-[0.98]"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        boxShadow: "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)",
      }}
      onClick={() => navigate("/calendar")}
    >
      <div className="flex justify-between items-center mb-3">
        <p className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.5)" }}>
          Эта неделя
        </p>
        <p className="text-xs" style={{ color: "#B794F6" }}>
          {data?.total ?? 0} событий
        </p>
      </div>

      <div className="flex justify-between">
        {days.map((d, i) => {
          const isToday = isSameDay(d.date, today);
          const hasEvents = d.events.length > 0;
          const colors = d.events.slice(0, 3).map((e) => e.color);

          const handleDayClick = (e: React.MouseEvent) => {
            e.stopPropagation();
            if (hasEvents) {
              setSelectedDate(d.date);
            }
          };

          return (
            <button key={i} className="flex flex-col items-center gap-1.5" onClick={handleDayClick}>
              <span
                className="text-[10px] font-medium"
                style={{ color: isToday ? "#B794F6" : "#64748B" }}
              >
                {d.weekday}
              </span>
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold"
                style={{
                  background: isToday ? "#8A2BE2" : "rgba(255,255,255,0.05)",
                  color: isToday ? "#fff" : "#CBD5E1",
                }}
              >
                {d.date.getDate()}
              </div>
              {/* Event dots */}
              <div className="flex gap-0.5 h-1">
                {hasEvents ? (
                  colors.map((c, idx) => (
                    <div key={idx} className="w-1 h-1 rounded-full" style={{ background: c }} />
                  ))
                ) : (
                  <div className="w-1 h-1 rounded-full" style={{ background: "transparent" }} />
                )}
              </div>
            </button>
          );
        })}
      </div>

      <DaySheet
        date={selectedDate}
        events={selectedDate ? data?.days[formatDateKey(selectedDate)] ?? [] : []}
        onClose={() => setSelectedDate(null)}
        onEventClick={(e) => setSelectedEvent(e)}
      />
      <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}
