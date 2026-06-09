import { useMemo, useState } from "react";
import type { CalendarEvent } from "../../types/calendar";
import { formatDateKey } from "../../utils/date";
import CalendarDayCell, { WeekdayHeader } from "./CalendarDayCell";
import DaySheet from "./DaySheet";
import EventDetailModal from "./EventDetailModal";

interface Props {
  year: number;
  month: number;
  days: Record<string, CalendarEvent[]>;
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export default function CalendarMonthView({ year, month, days }: Props) {
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  const cells = useMemo(() => {
    const firstDayOfMonth = new Date(year, month - 1, 1);
    const lastDayOfMonth = new Date(year, month, 0);

    // Понедельник первой недели
    const firstMonday = new Date(firstDayOfMonth);
    const dow = firstDayOfMonth.getDay() || 7; // 1=Пн...7=Вс
    firstMonday.setDate(firstDayOfMonth.getDate() - (dow - 1));

    // Воскресенье последней недели
    const lastSunday = new Date(lastDayOfMonth);
    const lastDow = lastDayOfMonth.getDay() || 7;
    lastSunday.setDate(lastDayOfMonth.getDate() + (7 - lastDow));

    // Генерируем все дни между firstMonday и lastSunday
    const cells: {
      date: Date;
      isCurrentMonth: boolean;
      events: CalendarEvent[];
    }[] = [];

    const cursor = new Date(firstMonday);
    while (cursor <= lastSunday) {
      const d = new Date(cursor);
      const key = formatDateKey(d);
      cells.push({
        date: d,
        isCurrentMonth: d.getMonth() === month - 1,
        events: days[key] ?? [],
      });
      cursor.setDate(cursor.getDate() + 1);
    }

    return cells;
  }, [year, month, days]);

  const today = new Date();

  // При клике на ячейку открываем DaySheet со всеми событиями дня
  const handleCellClick = (date: Date) => {
    setSelectedDate(date);
  };

  return (
    <div className="px-2">
      <WeekdayHeader />
      <div className="grid grid-cols-7 gap-1">
        {cells.map((cell, idx) => (
          <CalendarDayCell
            key={idx}
            date={cell.date}
            events={cell.events}
            isCurrentMonth={cell.isCurrentMonth}
            isToday={isSameDay(cell.date, today)}
            onClick={() => handleCellClick(cell.date)}
          />
        ))}
      </div>

      {/* DaySheet — список событий дня */}
      <DaySheet
        date={selectedDate}
        events={selectedDate ? days[formatDateKey(selectedDate)] ?? [] : []}
        onClose={() => setSelectedDate(null)}
        onEventClick={(e) => setSelectedEvent(e)}
      />

      {/* Event detail modal */}
      <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}
