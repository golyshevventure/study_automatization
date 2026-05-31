import { ExternalLink } from "lucide-react";
import ProgressBar from "./ProgressBar";
import type { CourseModule } from "../hooks/usePrograms";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

interface ModuleCardProps {
  module: CourseModule;
  index: number;
}

export default function ModuleCard({ module, index }: ModuleCardProps) {
  const isPassed = module.progress === 100;
  const isInProgress = module.progress > 0 && !isPassed;

  const statusColor = isPassed
    ? "#10B981"
    : isInProgress
    ? "#B794F6"
    : "#94A3B8";

  const statusText = isPassed
    ? "✅ Пройден"
    : isInProgress
    ? `${module.progress}%`
    : "Не начат";

  const cardContent = (
    <div
      className="rounded-2xl p-4 flex flex-col gap-3"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        boxShadow: neonShadow,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <span
            className="text-xs font-bold shrink-0 mt-0.5"
            style={{ color: "#64748B", minWidth: "1.5rem" }}
          >
            {index + 1}.
          </span>
          <p className="text-sm font-medium leading-snug" style={{ color: "#fff" }}>
            {module.title}
          </p>
        </div>
        <span
          className="text-xs font-bold shrink-0"
          style={{ color: statusColor }}
        >
          {statusText}
        </span>
      </div>

      <ProgressBar progress={module.progress} height={6} />

      {module.link && (
        <div className="flex items-center gap-1.5" style={{ color: "#B794F6" }}>
          <ExternalLink size={12} />
          <span className="text-xs">Открыть в Netology</span>
        </div>
      )}
    </div>
  );

  if (module.link) {
    return (
      <a
        href={module.link}
        target="_blank"
        rel="noopener noreferrer"
        className="block cursor-pointer transition-transform active:scale-[0.98]"
      >
        {cardContent}
      </a>
    );
  }

  return cardContent;
}
