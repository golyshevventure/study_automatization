import { useEffect } from "react";
import { useCalendar } from "../hooks/useCalendar";
import CalendarHeader from "../components/calendar/CalendarHeader";
import CalendarFilterBar from "../components/calendar/CalendarFilterBar";
import CalendarMonthView from "../components/calendar/CalendarMonthView";
import CalendarWeekView from "../components/calendar/CalendarWeekView";
import { RefreshCw } from "lucide-react";

const SYNC_INTERVAL_MS = 30 * 60 * 1000;
const MIN_SYNC_INTERVAL_MS = 5 * 60 * 1000;

function getLastSyncTime(): number | null {
  const raw = localStorage.getItem("calendar_last_sync");
  return raw ? parseInt(raw, 10) : null;
}

function setLastSyncTime(time: number) {
  localStorage.setItem("calendar_last_sync", String(time));
}

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

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
    doSilentSync,
  } = useCalendar();

  // Авто-синхронизация
  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const scheduleNext = (delay: number) => {
      timeoutId = setTimeout(async () => {
        if (cancelled) return;
        await doSilentSync();
        if (!cancelled) setLastSyncTime(Date.now());
        scheduleNext(SYNC_INTERVAL_MS);
      }, delay);
    };

    const runSilent = async () => {
      const last = getLastSyncTime();
      const now = Date.now();
      if (!last || now - last > MIN_SYNC_INTERVAL_MS) {
        await doSilentSync();
        if (!cancelled) setLastSyncTime(now);
      }
      scheduleNext(SYNC_INTERVAL_MS);
    };
    runSilent();

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [doSilentSync]);

  const handleManualSync = () => {
    doSync();
    setLastSyncTime(Date.now());
  };

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
        onSync={handleManualSync}
      />

      <CalendarFilterBar filter={filter} onChange={setFilter} />

      {error && (
        <p className="px-4 text-xs mb-2" style={{ color: "#EF4444" }}>
          {error}
        </p>
      )}

      {isLoading ? (
        <div className="text-center py-12">
          <RefreshCw size={24} color="#B794F6" className="animate-spin mx-auto" />
          <p className="text-xs mt-2" style={{ color: "#94A3B8" }}>
            Загрузка календаря...
          </p>
        </div>
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
            Попробуйте другой фильтр или период
          </p>
        </div>
      ) : (
        <>
          {view === "month" ? (
            <CalendarMonthView
              year={currentDate.getFullYear()}
              month={currentDate.getMonth() + 1}
              days={days}
            />
          ) : (
            <CalendarWeekView currentDate={currentDate} days={days} />
          )}
        </>
      )}
    </div>
  );
}
