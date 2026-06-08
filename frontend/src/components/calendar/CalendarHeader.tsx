import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, LayoutGrid, RefreshCw } from "lucide-react";
import type { CalendarView } from "../../types/calendar";

const MONTH_NAMES = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];

interface Props {
  view: CalendarView;
  onViewChange: (v: CalendarView) => void;
  currentDate: Date;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
  isSyncing: boolean;
  onSync: () => void;
}

export default function CalendarHeader({
  view,
  onViewChange,
  currentDate,
  onPrev,
  onNext,
  onToday,
  isSyncing,
  onSync,
}: Props) {
  const monthLabel = `${MONTH_NAMES[currentDate.getMonth()]} ${currentDate.getFullYear()}`;

  // Для недели: "2–8 июня 2026"
  const getWeekLabel = () => {
    const d = new Date(currentDate);
    const day = d.getDay() || 7;
    const monday = new Date(d);
    monday.setDate(d.getDate() - day + 1);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    const sameMonth = monday.getMonth() === sunday.getMonth();
    const m1 = monday.getDate();
    const m2 = sunday.getDate();
    if (sameMonth) {
      return `${m1}–${m2} ${MONTH_NAMES[monday.getMonth()]} ${monday.getFullYear()}`;
    }
    return `${m1} ${MONTH_NAMES[monday.getMonth()]} – ${m2} ${MONTH_NAMES[sunday.getMonth()]} ${monday.getFullYear()}`;
  };

  const title = view === "month" ? monthLabel : getWeekLabel();

  return (
    <div className="px-4 pt-8 pb-4">
      {/* Title + sync */}
      <div className="flex items-center justify-between mb-4">
        <h1
          className="text-xl font-bold"
          style={{ color: "#fff", textShadow: "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)" }}
        >
          Календарь
        </h1>
        <button
          onClick={onSync}
          disabled={isSyncing}
          className="p-2 rounded-xl transition-all active:scale-90 disabled:opacity-50"
          style={{ background: "rgba(138, 43, 226, 0.15)" }}
          title="Синхронизировать"
        >
          <RefreshCw size={18} color="#B794F6" className={isSyncing ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button
            onClick={onPrev}
            className="p-1.5 rounded-lg transition-all active:scale-90 hover:bg-white/5"
          >
            <ChevronLeft size={20} color="#94A3B8" />
          </button>
          <span className="text-sm font-medium min-w-[140px] text-center" style={{ color: "#fff" }}>
            {title}
          </span>
          <button
            onClick={onNext}
            className="p-1.5 rounded-lg transition-all active:scale-90 hover:bg-white/5"
          >
            <ChevronRight size={20} color="#94A3B8" />
          </button>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={onToday}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all active:scale-90 hover:bg-white/5"
            style={{ color: "#B794F6", border: "1px solid rgba(138, 43, 226, 0.3)" }}
          >
            Сегодня
          </button>
          <button
            onClick={() => onViewChange(view === "month" ? "week" : "month")}
            className="p-1.5 rounded-lg transition-all active:scale-90 hover:bg-white/5"
            title={view === "month" ? "Неделя" : "Месяц"}
          >
            {view === "month" ? (
              <CalendarIcon size={18} color="#94A3B8" />
            ) : (
              <LayoutGrid size={18} color="#94A3B8" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
