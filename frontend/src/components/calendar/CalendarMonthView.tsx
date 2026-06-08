import { useMemo, useState } from "react";
import type { CalendarEvent } from "../../types/calendar";
import CalendarDayCell, { WeekdayHeader } from "./CalendarDayCell";
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
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  const cells = useMemo(() => {
    const firstDayOfMonth = new Date(year, month - 1, 1);
    const daysInMonth = new Date(year, month, 0).getDate();

    // День недели первого числа (0=Вс, 1=Пн...)
    let startDay = firstDayOfMonth.getDay();
    if (startDay === 0) startDay = 7; // Вс = 7

    const totalCells = 42; // 7×6
    const cells: {
      date: Date;
      isCurrentMonth: boolean;
      events: CalendarEvent[];
    }[] = [];

    // Дни предыдущего месяца
    const prevMonthDays = new Date(year, month - 1, 0).getDate();
    for (let i = startDay - 2; i >= 0; i--) {
      const d = new Date(year, month - 2, prevMonthDays - i);
      const key = d.toISOString().split("T")[0];
      cells.push({ date: d, isCurrentMonth: false, events: days[key] ?? [] });
    }

    // Дни текущего месяца
    for (let i = 1; i <= daysInMonth; i++) {
      const d = new Date(year, month - 1, i);
      const key = d.toISOString().split("T")[0];
      cells.push({ date: d, isCurrentMonth: true, events: days[key] ?? [] });
    }

    // Дни следующего месяца
    const remaining = totalCells - cells.length;
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month, i);
      const key = d.toISOString().split("T")[0];
      cells.push({ date: d, isCurrentMonth: false, events: days[key] ?? [] });
    }

    return cells;
  }, [year, month, days]);

  const today = new Date();

  // При клике на ячейку: если есть события — показываем первое (в будущем можно сделать список)
  const handleCellClick = (events: CalendarEvent[]) => {
    if (events.length > 0) {
      setSelectedEvent(events[0]);
    }
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
            onClick={() => handleCellClick(cell.events)}
          />
        ))}
      </div>

      {/* Event detail modal */}
      <EventDetailModal event={selectedEvent} onClose={() => setSelectedEvent(null)} />
    </div>
  );
}
