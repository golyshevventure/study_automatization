import { useState } from "react";
import { useDeadlines } from "../hooks/useDeadlines";
import DeadlineCard from "../components/DeadlineCard";
import { Clock, CheckCircle2, RefreshCw } from "lucide-react";
import type { DeadlineFilter } from "../types/deadline";

const neonShadowLight = "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)";
const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

const FILTER_BUTTONS: { key: DeadlineFilter; label: string; color: string }[] = [
  { key: "all", label: "Все", color: "#B794F6" },
  { key: "normal", label: "Обычное", color: "#B794F6" },
  { key: "urgent", label: "Срочно", color: "#F59E0B" },
  { key: "overdue", label: "Просрочено", color: "#EF4444" },
];

export default function Deadlines() {
  const [filter, setFilter] = useState<DeadlineFilter>("all");
  const { deadlines, isLoading, refetch, lastUpdated, counts } = useDeadlines("all", filter);

  // Группировка по программе
  const groups = new Map<string, typeof deadlines>();
  for (const d of deadlines) {
    const key = d.programName;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(d);
  }

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
          <h1
            className="text-2xl font-bold"
            style={{ color: "#fff", textShadow: neonShadowLight }}
          >
            Дедлайны
          </h1>
          <button
            onClick={refetch}
            disabled={isLoading}
            className="p-2 rounded-xl transition-all active:scale-90 disabled:opacity-50"
            style={{ background: "rgba(138, 43, 226, 0.15)" }}
          >
            <RefreshCw
              size={18}
              color="#B794F6"
              className={isLoading ? "animate-spin" : ""}
            />
          </button>
        </div>
        <p className="text-sm mt-1" style={{ color: "#94A3B8" }}>
          {counts.all} активных задач
          {counts.overdue > 0 && (
            <span style={{ color: "#EF4444" }}>
              {" "}
              · {counts.overdue} просрочено
            </span>
          )}
          {counts.urgent > 0 && (
            <span style={{ color: "#F59E0B" }}>
              {" "}
              · {counts.urgent} срочных
            </span>
          )}
        </p>
        {lastUpdated && (
          <p className="text-xs mt-1" style={{ color: "#64748B" }}>
            Обновлено: {lastUpdated.toLocaleTimeString("ru-RU", { timeZone: "Europe/Moscow" })} МСК
          </p>
        )}
      </div>

      {/* Filter Buttons */}
      <div className="px-4 mb-4 flex gap-2 overflow-x-auto hide-scrollbar pb-1">
        {FILTER_BUTTONS.map((btn) => {
          const isActive = filter === btn.key;
          const count = counts[btn.key];
          return (
            <button
              key={btn.key}
              onClick={() => setFilter(btn.key)}
              className="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all active:scale-95"
              style={{
                background: isActive ? `${btn.color}25` : "rgba(15, 23, 42, 0.6)",
                color: isActive ? btn.color : "#94A3B8",
                border: isActive ? `1px solid ${btn.color}50` : "1px solid transparent",
                boxShadow: isActive ? `0 0 10px ${btn.color}30` : "none",
              }}
            >
              {btn.label}
              {count > 0 && (
                <span
                  className="ml-1.5 text-xs"
                  style={{ color: isActive ? btn.color : "#64748B" }}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Deadline Cards */}
      <div className="px-4 flex flex-col gap-3">
        {deadlines.length === 0 ? (
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
                {filter === "all"
                  ? "Все дедлайны выполнены!"
                  : filter === "overdue"
                  ? "Нет просроченных дедлайнов"
                  : filter === "urgent"
                  ? "Нет срочных дедлайнов"
                  : "Нет обычных дедлайнов"}
              </p>
              <p className="text-xs mt-1" style={{ color: "#94A3B8" }}>
                {filter === "all"
                  ? "Нет активных заданий требующих внимания"
                  : "Попробуйте другой фильтр"}
              </p>
            </div>
          </div>
        ) : (
          Array.from(groups.entries()).map(([programName, items]) => (
            <div key={programName}>
              <p
                className="text-xs font-medium uppercase tracking-wider mb-2 mt-1 px-1"
                style={{ color: "rgba(255,255,255,0.5)" }}
              >
                {programName}
              </p>
              <div className="flex flex-col gap-3">
                {items.map((d) => (
                  <DeadlineCard key={d.id} deadline={d} showProgram={false} />
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Auto-refresh hint */}
      <div className="px-4 mt-4 text-center">
        <p className="text-xs" style={{ color: "#64748B" }}>
          <Clock size={12} className="inline mr-1" />
          Автообновление каждый час
        </p>
      </div>
    </div>
  );
}
