import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Plus, Loader2, Search, Trash2, ChevronRight } from "lucide-react";
import {
  getConspects,
  getJobStatus,
  deleteConspect,
  type Conspect,
  type ConspectJob,
} from "../api/summary";
import GenerateConspectModal from "../components/summary/GenerateConspectModal";
import KnowledgeGraph from "../components/summary/KnowledgeGraph";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

function JobToast({ jobId, onDone }: { jobId: string; onDone: () => void }) {
  const [job, setJob] = useState<ConspectJob | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const j = await getJobStatus(jobId);
        setJob(j);
        if (j.status === "ready" || j.status === "failed") {
          clearInterval(interval);
          if (j.status === "ready") {
            setTimeout(onDone, 3000);
          }
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId, onDone]);

  if (!job) return null;

  const statusMap: Record<string, { text: string; color: string; bg: string }> = {
    queued: { text: "В очереди", color: "#B794F6", bg: "rgba(138,43,226,0.15)" },
    extracting: { text: "Извлечение VTT", color: "#B794F6", bg: "rgba(138,43,226,0.15)" },
    generating: { text: "Генерация", color: "#B794F6", bg: "rgba(138,43,226,0.15)" },
    ready: { text: "Готово!", color: "#10B981", bg: "rgba(16,185,129,0.15)" },
    failed: { text: "Ошибка", color: "#EF4444", bg: "rgba(239,68,68,0.15)" },
  };
  const s = statusMap[job.status] || { text: job.status, color: "#94A3B8", bg: "rgba(148,163,184,0.15)" };

  return (
    <div
      className="fixed top-4 left-1/2 -translate-x-1/2 z-50 rounded-xl px-4 py-3 flex items-center gap-3"
      style={{ background: s.bg, border: `1px solid ${s.color}40` }}
    >
      {job.status !== "ready" && job.status !== "failed" && (
        <Loader2 size={16} color={s.color} className="animate-spin" />
      )}
      <span className="text-sm font-medium" style={{ color: s.color }}>
        {s.text}
      </span>
      {job.status === "failed" && job.error_message && (
        <span className="text-xs" style={{ color: "#EF4444" }}>
          {job.error_message}
        </span>
      )}
    </div>
  );
}

export default function Conspects() {
  const navigate = useNavigate();
  const [conspects, setConspects] = useState<Conspect[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getConspects(search || undefined, undefined, undefined, 20, 0);
      setConspects(res.items);
      setTotal(res.total);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search, refreshKey]);

  useEffect(() => {
    load();
  }, [load]);

  const handleJobCreated = (jobId: string) => {
    setActiveJobId(jobId);
  };

  const handleJobDone = () => {
    setActiveJobId(null);
    setRefreshKey((k) => k + 1);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Удалить конспект?")) return;
    try {
      await deleteConspect(id);
      setRefreshKey((k) => k + 1);
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div
      className="pb-4"
      style={{
        background:
          "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
        minHeight: "100%",
      }}
    >
      {/* Header */}
      <div className="px-5 pt-8 pb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold" style={{ color: "#fff", textShadow: neonShadow }}>
          Конспекты
        </h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all active:scale-95"
          style={{
            background: "rgba(138, 43, 226, 0.2)",
            color: "#B794F6",
            border: "1px solid rgba(138, 43, 226, 0.3)",
            boxShadow: "0 0 10px rgba(138, 43, 226, 0.2)",
          }}
        >
          <Plus size={16} />
          Создать
        </button>
      </div>

      {/* Search */}
      <div className="px-4 mb-4">
        <div
          className="flex items-center gap-2 rounded-xl px-4 py-3"
          style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
        >
          <Search size={16} color="#64748B" />
          <input
            type="text"
            placeholder="Поиск по конспектам..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            className="bg-transparent text-sm outline-none w-full"
            style={{ color: "#fff" }}
          />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 mb-4">
          <div className="rounded-xl p-3 text-sm" style={{ background: "rgba(239,68,68,0.15)", color: "#EF4444" }}>
            {error}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} color="#B794F6" className="animate-spin" />
        </div>
      )}

      {/* Empty */}
      {!loading && conspects.length === 0 && (
        <div className="px-4 text-center py-12">
          <FileText size={40} color="#334155" className="mx-auto mb-3" />
          <p className="text-sm font-medium" style={{ color: "#94A3B8" }}>
            {search ? "Ничего не найдено" : "Нет конспектов"}
          </p>
          {!search && (
            <button
              onClick={() => setShowModal(true)}
              className="mt-3 text-sm"
              style={{ color: "#B794F6" }}
            >
              Создать первый конспект
            </button>
          )}
        </div>
      )}

      {/* List */}
      <div className="px-4 flex flex-col gap-3">
        {conspects.map((c) => (
          <div
            key={c.id}
            className="rounded-xl p-4 flex items-start gap-3"
            style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: "rgba(138,43,226,0.15)" }}
            >
              <FileText size={18} color="#B794F6" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium" style={{ color: "#fff" }}>
                {c.title}
              </p>
              {c.topic && (
                <p className="text-xs mt-0.5" style={{ color: "#94A3B8" }}>
                  {c.topic}
                </p>
              )}
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-xs" style={{ color: "#64748B" }}>
                  {new Date(c.created_at).toLocaleDateString("ru-RU")}
                </span>
                {c.is_edited && (
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-full"
                    style={{ background: "rgba(183,148,246,0.15)", color: "#B794F6" }}
                  >
                    отредактирован
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate(`/conspects/${c.id}`)}
                className="p-2"
              >
                <ChevronRight size={16} color="#64748B" />
              </button>
              <button onClick={() => handleDelete(c.id)} className="p-2">
                <Trash2 size={16} color="#EF4444" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {showModal && (
        <GenerateConspectModal onClose={() => setShowModal(false)} onJobCreated={handleJobCreated} />
      )}

      {/* Job Toast */}
      {activeJobId && <JobToast jobId={activeJobId} onDone={handleJobDone} />}
    </div>
  );
}
