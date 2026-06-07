import { useState, useEffect, useRef } from "react";
import { useDeadlines, FILTER_LABELS } from "../hooks/useDeadlines";
import DeadlineCard from "../components/DeadlineCard";
import { RefreshCw, CheckCircle2, CalendarDays, BookOpen, GraduationCap, List } from "lucide-react";
import type { DeadlineFilter } from "../types/deadline";

const SYNC_INTERVAL_MS = 30 * 60 * 1000; // 30 минут
const MIN_SYNC_INTERVAL_MS = 5 * 60 * 1000; // минимум 5 минут между синхронизациями

function getLastSyncTime(): number | null {
  const raw = localStorage.getItem("deadlines_last_sync");
  return raw ? parseInt(raw, 10) : null;
}

function setLastSyncTime(time: number) {
  localStorage.setItem("deadlines_last_sync", String(time));
}

function formatSyncTime(timestamp: number | null): string {
  if (!timestamp) return "Не синхронизировано";
  const diff = Date.now() - timestamp;
  if (diff < 60_000) return "Только что";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} мин назад`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} ч назад`;
  return new Date(timestamp).toLocaleString("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

const neonShadowLight = "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)";
const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

const FILTER_CONFIG: { key: DeadlineFilter; label: string; icon: React.ElementType; color: string }[] = [
  { key: "lessons", label: FILTER_LABELS.lessons, icon: BookOpen, color: "#3B82F6" },
  { key: "works", label: FILTER_LABELS.works, icon: CalendarDays, color: "#F59E0B" },
  { key: "control", label: FILTER_LABELS.control, icon: GraduationCap, color: "#EF4444" },
  { key: "all", label: FILTER_LABELS.all, icon: List, color: "#B794F6" },
];

export default function Deadlines() {
  const [filter, setFilter] = useState<DeadlineFilter>("lessons");
  const [program, setProgram] = useState<string>("");
  const { events, total, isLoading, isFetchingMore, isSyncing, hasMore, error, doSync, doSilentSync, loadMore } = useDeadlines(filter, 20, program || undefined);
  const [lastSync, setLastSync] = useState<number | null>(getLastSyncTime);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Уникальные программы из загруженных событий (для селекта)
  const programs = Array.from(new Set(events.map((e) => e.program_title).filter((p): p is string => !!p))).sort();

  // Авто-синхронизация при входе и каждые 30 мин (бесшовная — без спиннера)
  useEffect(() => {
    const runSilent = async () => {
      const last = getLastSyncTime();
      const now = Date.now();
      if (!last || now - last > MIN_SYNC_INTERVAL_MS) {
        await doSilentSync();
        setLastSync(now);
        setLastSyncTime(now);
      }
    };
    runSilent();

    intervalRef.current = setInterval(async () => {
      await doSilentSync();
      const t = Date.now();
      setLastSync(t);
      setLastSyncTime(t);
    }, SYNC_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [doSilentSync]);

  const handleManualSync = () => {
    doSync();
    const t = Date.now();
    setLastSync(t);
    setLastSyncTime(t);
  };

  return (
    <div
      className="pb-4 min-h-full"
      style={{
        background:
          "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
      }}
    >
      {/* Header */}
      <div className="px-5 pt-8 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1
              className="text-2xl font-bold"
              style={{ color: "#fff", textShadow: neonShadowLight }}
            >
              Ближайшие события
            </h1>
            <p className="text-xs mt-1" style={{ color: "rgba(255,255,255,0.5)" }}>
              Обновлено: {formatSyncTime(lastSync)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleManualSync}
              disabled={isSyncing}
              className="p-2 rounded-xl transition-all active:scale-90 disabled:opacity-50"
              style={{ background: "rgba(138, 43, 226, 0.15)" }}
              title="Синхронизировать с Netology"
            >
              <RefreshCw
                size={18}
                color="#B794F6"
                className={isSyncing ? "animate-spin" : ""}
              />
            </button>
          </div>
        </div>

        {error && (
          <p className="text-xs mt-2" style={{ color: "#EF4444" }}>
            {error}
          </p>
        )}
      </div>

      {/* Filter Buttons */}
      <div className="px-4 mb-4 flex gap-2 overflow-x-auto hide-scrollbar pb-1">
        {FILTER_CONFIG.map((btn) => {
          const isActive = filter === btn.key;
          const Icon = btn.icon;
          return (
            <button
              key={btn.key}
              onClick={() => setFilter(btn.key)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all active:scale-95"
              style={{
                background: isActive ? `${btn.color}25` : "rgba(15, 23, 42, 0.6)",
                color: isActive ? btn.color : "#94A3B8",
                border: isActive ? `1px solid ${btn.color}50` : "1px solid transparent",
                boxShadow: isActive ? `0 0 10px ${btn.color}30` : "none",
              }}
            >
              <Icon size={14} />
              {btn.label}
            </button>
          );
        })}
      </div>

      {/* Program Filter */}
      {programs.length > 0 && (
        <div className="px-4 mb-4">
          <select
            value={program}
            onChange={(e) => setProgram(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl text-sm bg-slate-900/60 text-white border border-purple-500/30 focus:border-purple-500 focus:outline-none appearance-none"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23B794F6' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 12px center",
              paddingRight: "36px",
            }}
          >
            <option value="">Все программы</option>
            {programs.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Events List */}
      <div className="px-4 flex flex-col gap-3">
        {isLoading ? (
          <div className="text-center py-8">
            <RefreshCw size={24} color="#B794F6" className="animate-spin mx-auto" />
            <p className="text-xs mt-2" style={{ color: "#94A3B8" }}>
              Загрузка...
            </p>
          </div>
        ) : events.length === 0 ? (
          <div
            className="rounded-2xl p-8 text-center flex flex-col items-center gap-3"
            style={{
              background: "rgba(15, 23, 42, 0.6)",
              boxShadow: neonShadow,
            }}
          >
            <CheckCircle2 size={40} color="#10B981" />
            <div>
              <p className="text-sm font-medium" style={{ color: "#fff" }}>
                Нет предстоящих событий
              </p>
              <p className="text-xs mt-1" style={{ color: "#94A3B8" }}>
                Все дедлайны и зачёты выполнены
              </p>
            </div>
          </div>
        ) : (
          <>
            <p className="text-xs" style={{ color: "rgba(255,255,255,0.4)" }}>
              Показано {events.length} из {total}
            </p>
            {events.map((event) => (
              <DeadlineCard key={event.id} event={event} />
            ))}
            {hasMore && (
              <button
                onClick={() => loadMore()}
                disabled={isFetchingMore}
                className="w-full py-3 rounded-2xl text-sm font-medium transition-all active:scale-95 disabled:opacity-50"
                style={{
                  background: "rgba(138, 43, 226, 0.15)",
                  color: "#B794F6",
                  border: "1px solid rgba(138, 43, 226, 0.3)",
                }}
              >
                {isFetchingMore ? (
                  <span className="flex items-center justify-center gap-2">
                    <RefreshCw size={14} className="animate-spin" />
                    Загрузка...
                  </span>
                ) : (
                  "Загрузить ещё"
                )}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
