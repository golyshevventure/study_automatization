import type { CalendarEvent } from "../../types/calendar";

interface Props {
  date: Date;
  events: CalendarEvent[];
  isCurrentMonth: boolean;
  isToday: boolean;
  onClick: () => void;
}

const WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export default function CalendarDayCell({ date, events, isCurrentMonth, isToday, onClick }: Props) {
  const dayNum = date.getDate();
  const isWeekend = date.getDay() === 0 || date.getDay() === 6;

  // Максимум 4 точки
  const dots = events.slice(0, 4);

  return (
    <button
      onClick={onClick}
      className="relative flex flex-col items-center justify-start py-1 rounded-lg transition-all active:scale-95 min-h-[52px] sm:min-h-[64px]"
      style={{
        background: isToday ? "rgba(138, 43, 226, 0.2)" : "transparent",
        border: isToday ? "1px solid rgba(138, 43, 226, 0.4)" : "1px solid transparent",
        opacity: isCurrentMonth ? 1 : 0.35,
      }}
    >
      <span
        className="text-[11px] sm:text-xs font-medium w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center rounded-full"
        style={{
          color: isToday ? "#fff" : isWeekend ? "#EF4444" : "#CBD5E1",
          background: isToday ? "#8A2BE2" : "transparent",
        }}
      >
        {dayNum}
      </span>

      {/* Dots */}
      {dots.length > 0 && (
        <div className="flex gap-0.5 mt-1 flex-wrap justify-center px-1">
          {dots.map((e, i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: e.color }}
            />
          ))}
        </div>
      )}

      {/* Count badge if more than 4 */}
      {events.length > 4 && (
        <span className="text-[9px] mt-0.5" style={{ color: "#94A3B8" }}>
          +{events.length - 4}
        </span>
      )}
    </button>
  );
}

/** Заголовки дней недели. */
export function WeekdayHeader() {
  return (
    <div className="grid grid-cols-7 gap-1 mb-1">
      {WEEKDAYS_SHORT.map((d) => (
        <div key={d} className="text-center text-[10px] font-medium py-1" style={{ color: "#64748B" }}>
          {d}
        </div>
      ))}
    </div>
  );
}
