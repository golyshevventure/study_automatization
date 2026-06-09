import { useCalendar } from "../hooks/useCalendar";
import CalendarHeader from "../components/calendar/CalendarHeader";
import CalendarFilterBar from "../components/calendar/CalendarFilterBar";
import CalendarMonthView from "../components/calendar/CalendarMonthView";
import CalendarWeekView from "../components/calendar/CalendarWeekView";
import { BookOpen, CalendarDays, GraduationCap, FileText } from "lucide-react";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

const LEGEND = [
  { label: "Занятие", color: "#3B82F6", icon: BookOpen },
  { label: "Тест", color: "#EAB308", icon: CalendarDays },
  { label: "Зачёт / Экзамен", color: "#EF4444", icon: GraduationCap },
  { label: "ДЗ", color: "#F97316", icon: FileText },
];

/** Skeleton сетка месяца — 7×6 серых ячеек. */
function MonthSkeleton() {
  return (
    <div className="px-2 animate-pulse">
      <div className="grid grid-cols-7 gap-1 mb-1">
        {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => (
          <div key={d} className="text-center text-[10px] py-1" style={{ color: "#334155" }}>
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: 42 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl min-h-[64px]"
            style={{ background: "rgba(30, 41, 59, 0.4)" }}
          />
        ))}
      </div>
    </div>
  );
}

/** Skeleton недели — 7 колонок. */
function WeekSkeleton() {
  return (
    <div className="px-2 animate-pulse">
      <div className="grid grid-cols-7 gap-1 mb-2">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="text-center py-2">
            <div className="h-3 w-8 mx-auto rounded" style={{ background: "#334155" }} />
            <div className="h-4 w-6 mx-auto rounded mt-1" style={{ background: "#334155" }} />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1 min-h-[200px]">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="rounded-xl p-1" style={{ background: "rgba(30, 41, 59, 0.4)" }}>
            <div className="h-8 rounded-lg mb-1" style={{ background: "#334155" }} />
            <div className="h-8 rounded-lg" style={{ background: "#334155" }} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Calendar() {
  const {
    days,
    total,
    isLoading,
    error,
    view,
    setView,
    currentDate,
    goToPrev,
    goToNext,
    goToToday,
    filter,
    setFilter,
    isSyncing,
    doSync,
  } = useCalendar();

  return (
    <div
      className="pb-4 min-h-full"
      style={{
        background:
          "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
      }}
    >
      <CalendarHeader
        view={view}
        onViewChange={setView}
        currentDate={currentDate}
        onPrev={goToPrev}
        onNext={goToNext}
        onToday={goToToday}
        isSyncing={isSyncing}
        onSync={doSync}
      />

      <CalendarFilterBar filter={filter} onChange={setFilter} />

      {/* Legend */}
      <div className="px-4 mb-3 flex gap-3 overflow-x-auto hide-scrollbar pb-1">
        {LEGEND.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex items-center gap-1.5 shrink-0">
              <Icon size={12} color={item.color} />
              <span className="text-[11px]" style={{ color: "#94A3B8" }}>
                {item.label}
              </span>
            </div>
          );
        })}
      </div>

      {error && (
        <p className="px-4 text-xs mb-2" style={{ color: "#EF4444" }}>
          {error}
        </p>
      )}

      {isLoading ? (
        view === "month" ? <MonthSkeleton /> : <WeekSkeleton />
      ) : total === 0 ? (
        <div
          className="mx-4 rounded-2xl p-8 text-center flex flex-col items-center gap-3"
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            boxShadow: neonShadow,
          }}
        >
          <p className="text-sm font-medium" style={{ color: "#fff" }}>
            Нет событий за этот период
          </p>
          <p className="text-xs" style={{ color: "#94A3B8" }}>
            Проверьте другой период или синхронизируйтесь
          </p>
        </div>
      ) : (
        <div className="animate-in fade-in duration-300">
          {view === "month" ? (
            <CalendarMonthView
              year={currentDate.getFullYear()}
              month={currentDate.getMonth() + 1}
              days={days}
            />
          ) : (
            <CalendarWeekView currentDate={currentDate} days={days} />
          )}
        </div>
      )}
    </div>
  );
}
