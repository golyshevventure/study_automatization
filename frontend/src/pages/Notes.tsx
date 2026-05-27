import { useState } from "react";
import { Search, FileText, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { notes, subjects } from "../data";

const statusLabels = {
  done: { text: "Готово", bg: "rgba(16, 185, 129, 0.15)", color: "#10B981" },
  in_progress: { text: "В процессе", bg: "rgba(245, 158, 11, 0.15)", color: "#F59E0B" },
  pending: { text: "Ожидает", bg: "rgba(148, 163, 184, 0.15)", color: "#94A3B8" },
};

export default function Notes() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<string | null>(null);

  const filteredNotes = notes.filter((note) => {
    const matchesSearch = note.title.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = filter ? note.subject === filter : true;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="pb-4 relative min-h-full">
      {/* Header */}
      <div className="px-5 pt-8 pb-4">
        <h1 className="text-2xl font-bold" style={{ color: "#F1F5F9" }}>
          Конспекты
        </h1>
        <p className="text-sm mt-1" style={{ color: "#94A3B8" }}>
          {notes.length} конспектов по {subjects.length} предметам
        </p>
      </div>

      {/* Search */}
      <div className="px-4 mb-4">
        <div
          className="flex items-center gap-3 rounded-2xl px-4 py-3"
          style={{ background: "#1E293B" }}
        >
          <Search size={18} color="#94A3B8" />
          <input
            type="text"
            placeholder="Поиск конспектов..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent outline-none text-sm flex-1"
            style={{ color: "#F1F5F9" }}
          />
        </div>
      </div>

      {/* Subject Filters */}
      <div className="px-4 mb-4">
        <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-1">
          <button
            onClick={() => setFilter(null)}
            className="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors"
            style={{
              background: filter === null ? "#F59E0B" : "#1E293B",
              color: filter === null ? "#1E293B" : "#94A3B8",
            }}
          >
            Все
          </button>
          {subjects.map((s) => (
            <button
              key={s.id}
              onClick={() => setFilter(s.name)}
              className="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors"
              style={{
                background: filter === s.name ? s.color : "#1E293B",
                color: filter === s.name ? "#fff" : "#94A3B8",
              }}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Notes List */}
      <div className="px-4 flex flex-col gap-3">
        {filteredNotes.map((note) => {
          const status = statusLabels[note.status];
          return (
            <button
              key={note.id}
              onClick={() => navigate("/notes/1")}
              className="rounded-2xl p-4 flex items-start gap-3 text-left w-full"
              style={{ background: "#1E293B" }}
            >
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: `${note.subjectColor}20` }}
              >
                <FileText size={18} color={note.subjectColor} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium" style={{ color: "#F1F5F9" }}>
                  {note.title}
                </p>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-xs" style={{ color: "#94A3B8" }}>
                    {note.subject}
                  </span>
                  <span className="text-xs" style={{ color: "#64748B" }}>
                    {note.date}
                  </span>
                </div>
              </div>
              <span
                className="text-xs font-medium px-2 py-1 rounded-full shrink-0"
                style={{ background: status.bg, color: status.color }}
              >
                {status.text}
              </span>
            </button>
          );
        })}
        {filteredNotes.length === 0 && (
          <div className="text-center py-12">
            <p style={{ color: "#94A3B8" }}>Конспекты не найдены</p>
          </div>
        )}
      </div>

      {/* FAB */}
      <button
        className="absolute bottom-4 right-4 w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-transform active:scale-90 z-10"
        style={{ background: "#F59E0B" }}
        onClick={() => {}}
      >
        <Plus size={24} color="#1E293B" />
      </button>
    </div>
  );
}
