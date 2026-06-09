import { BookOpen, CalendarDays, GraduationCap, List } from "lucide-react";
import type { CalendarFilter } from "../../types/calendar";

const FILTER_CONFIG: { key: CalendarFilter; label: string; icon: React.ElementType; color: string }[] = [
  { key: "lessons", label: "Занятия", icon: BookOpen, color: "#3B82F6" },
  { key: "works", label: "Работы", icon: CalendarDays, color: "#F59E0B" },
  { key: "control", label: "Контроль", icon: GraduationCap, color: "#EF4444" },
  { key: "all", label: "Все", icon: List, color: "#B794F6" },
];

interface Props {
  filter: CalendarFilter;
  onChange: (f: CalendarFilter) => void;
}

export default function CalendarFilterBar({ filter, onChange }: Props) {
  return (
    <div className="px-4 mb-3 flex gap-2 overflow-x-auto hide-scrollbar pb-1">
      {FILTER_CONFIG.map((btn) => {
        const isActive = filter === btn.key;
        const Icon = btn.icon;
        return (
          <button
            key={btn.key}
            onClick={() => onChange(btn.key)}
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
  );
}
