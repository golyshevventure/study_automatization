import { Clock, AlertCircle } from "lucide-react";
import type { EnrichedDeadlineItem } from "../types/deadline";

interface DeadlineCardProps {
  deadline: EnrichedDeadlineItem;
  showProgram?: boolean;
}

/**
 * Цветовая схема индикаторов статуса:
 *   - overdue (просрочен) → красный #EF4444
 *   - urgent (срочный, < 3 дней) → оранжевый #F59E0B
 *   - normal (обычный) → фиолетовый/синий #B794F6
 */
const STATUS_COLORS = {
  overdue: {
    strip: "#EF4444",
    glow: "0 0 8px rgba(239, 68, 68, 0.4)",
    dateText: "#EF4444",
    badgeBg: "rgba(239, 68, 68, 0.15)",
    badgeText: "#EF4444",
  },
  urgent: {
    strip: "#F59E0B",
    glow: "0 0 8px rgba(245, 158, 11, 0.4)",
    dateText: "#F59E0B",
    badgeBg: "rgba(245, 158, 11, 0.15)",
    badgeText: "#F59E0B",
  },
  normal: {
    strip: "#B794F6",
    glow: "0 0 8px rgba(183, 148, 246, 0.3)",
    dateText: "#94A3B8",
    badgeBg: "rgba(183, 148, 246, 0.15)",
    badgeText: "#B794F6",
  },
};

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

export default function DeadlineCard({ deadline, showProgram = false }: DeadlineCardProps) {
  const colors = STATUS_COLORS[deadline.displayStatus];

  return (
    <div
      className="rounded-2xl p-4 flex items-start gap-3 transition-transform active:scale-[0.98]"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        boxShadow: neonShadow,
      }}
    >
      {/* Левая цветная полоска — индикатор статуса */}
      <div
        className="w-1.5 self-stretch rounded-full shrink-0"
        style={{
          background: colors.strip,
          boxShadow: colors.glow,
        }}
      />

      <div className="flex-1 min-w-0">
        {/* Название программы (опционально) */}
        {showProgram && (
          <p
            className="text-xs font-medium uppercase tracking-wider mb-1"
            style={{ color: "#64748B" }}
          >
            {deadline.programName}
          </p>
        )}

        {/* Верхняя строка: дисциплина */}
        <p
          className="text-xs font-medium uppercase tracking-wider mb-1"
          style={{ color: "#B794F6" }}
        >
          {deadline.disciplineName}
        </p>

        {/* Название задания */}
        <p className="text-sm font-medium leading-snug" style={{ color: "#fff" }}>
          {deadline.title}
        </p>

        {/* Тип задания + статусный бейдж */}
        <div className="flex items-center gap-2 mt-1.5">
          <span className="text-xs" style={{ color: "#64748B" }}>
            {deadline.typeLabel}
          </span>
          {deadline.status === "in_progress" && (
            <span
              className="text-xs font-medium px-1.5 py-0.5 rounded-full"
              style={{
                background: "rgba(138, 43, 226, 0.2)",
                color: "#B794F6",
              }}
            >
              В процессе
            </span>
          )}
        </div>

        {/* Дата и время дедлайна */}
        <div className="flex items-center gap-1.5 mt-2.5">
          {deadline.isOverdue ? (
            <AlertCircle size={14} color={colors.dateText} />
          ) : (
            <Clock size={14} color={colors.dateText} />
          )}
          <span className="text-xs font-medium" style={{ color: colors.dateText }}>
            {deadline.formattedDate}
          </span>
          {deadline.isOverdue && (
            <span
              className="text-xs font-medium px-1.5 py-0.5 rounded-full ml-1"
              style={{
                background: colors.badgeBg,
                color: colors.badgeText,
              }}
            >
              Просрочено
            </span>
          )}
          {deadline.isUrgent && (
            <span
              className="text-xs font-medium px-1.5 py-0.5 rounded-full ml-1"
              style={{
                background: colors.badgeBg,
                color: colors.badgeText,
              }}
            >
              Срочно
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
