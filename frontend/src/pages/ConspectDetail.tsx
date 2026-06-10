import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Loader2,
  Edit3,
  Save,
  X,
  Star,
  BookOpen,
  Tag,
} from "lucide-react";
import { getConspect, updateConspect, type Conspect } from "../api/summary";
import ReactMarkdown from "react-markdown";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

export default function ConspectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [conspect, setConspect] = useState<Conspect | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editSummary, setEditSummary] = useState("");
  const [editKeyPoints, setEditKeyPoints] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getConspect(id)
      .then((c) => {
        setConspect(c);
        setEditSummary(c.summary || "");
        setEditKeyPoints(c.key_points || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSave = async () => {
    if (!id || !conspect) return;
    setSaving(true);
    try {
      const updated = await updateConspect(id, {
        summary: editSummary,
        key_points: editKeyPoints.filter((kp) => kp.trim() !== ""),
      });
      setConspect(updated);
      setEditing(false);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div
        className="flex items-center justify-center"
        style={{
          background:
            "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
          minHeight: "100%",
        }}
      >
        <Loader2 size={24} color="#B794F6" className="animate-spin" />
      </div>
    );
  }

  if (error || !conspect) {
    return (
      <div
        className="px-5 pt-8 text-center"
        style={{
          background:
            "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
          minHeight: "100%",
        }}
      >
        <p className="text-sm font-medium" style={{ color: "#EF4444" }}>
          {error || "Конспект не найден"}
        </p>
        <button
          onClick={() => navigate("/conspects")}
          className="mt-4 text-sm"
          style={{ color: "#B794F6" }}
        >
          ← Назад к списку
        </button>
      </div>
    );
  }

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
        <button onClick={() => navigate("/conspects")} className="p-2 -ml-2">
          <ArrowLeft size={20} color="#94A3B8" />
        </button>
        <h1
          className="text-lg font-bold truncate px-2"
          style={{ color: "#fff", textShadow: neonShadow }}
        >
          {conspect.title}
        </h1>
        <button
          onClick={() => {
            if (editing) {
              setEditing(false);
              setEditSummary(conspect.summary || "");
              setEditKeyPoints(conspect.key_points || []);
            } else {
              setEditing(true);
            }
          }}
          className="p-2"
        >
          {editing ? <X size={20} color="#EF4444" /> : <Edit3 size={20} color="#B794F6" />}
        </button>
      </div>

      {/* Meta */}
      <div className="px-5 mb-4 flex flex-wrap gap-2">
        {conspect.topic && (
          <span
            className="text-xs px-2 py-1 rounded-full flex items-center gap-1"
            style={{ background: "rgba(138,43,226,0.15)", color: "#B794F6" }}
          >
            <Tag size={12} />
            {conspect.topic}
          </span>
        )}
        {conspect.difficulty !== null && (
          <span
            className="text-xs px-2 py-1 rounded-full flex items-center gap-1"
            style={{ background: "rgba(183,148,246,0.15)", color: "#B794F6" }}
          >
            <Star size={12} />
            Сложность: {conspect.difficulty}/10
          </span>
        )}
        {conspect.is_edited && (
          <span
            className="text-xs px-2 py-1 rounded-full"
            style={{ background: "rgba(16,185,129,0.15)", color: "#10B981" }}
          >
            Отредактирован
          </span>
        )}
      </div>

      {/* Summary */}
      <div className="px-4 mb-4">
        <div
          className="rounded-xl p-4"
          style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
        >
          <h2 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "#fff" }}>
            <BookOpen size={16} color="#B794F6" />
            Содержание
          </h2>

          {editing ? (
            <div className="flex flex-col gap-3">
              <textarea
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
                className="w-full rounded-lg p-3 text-sm outline-none resize-y"
                style={{
                  background: "rgba(15,23,42,0.8)",
                  color: "#fff",
                  border: "1px solid rgba(138,43,226,0.3)",
                  minHeight: "200px",
                }}
              />
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: "#64748B" }}>
                  Markdown поддерживается
                </span>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all active:scale-95 disabled:opacity-50"
                  style={{
                    background: "rgba(138, 43, 226, 0.2)",
                    color: "#B794F6",
                    border: "1px solid rgba(138, 43, 226, 0.3)",
                  }}
                >
                  {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                  Сохранить
                </button>
              </div>
            </div>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none">
              {conspect.summary ? (
                <ReactMarkdown>{conspect.summary}</ReactMarkdown>
              ) : (
                <p className="text-xs" style={{ color: "#64748B" }}>
                  Нет содержания
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Key Points */}
      {(!editing && conspect.key_points && conspect.key_points.length > 0) && (
        <div className="px-4 mb-4">
          <div
            className="rounded-xl p-4"
            style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
          >
            <h2 className="text-sm font-semibold mb-3" style={{ color: "#fff" }}>
              Ключевые моменты
            </h2>
            <ul className="flex flex-col gap-2">
              {conspect.key_points.map((kp, i) => (
                <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "#E2E8F0" }}>
                  <span className="shrink-0 mt-1 w-1.5 h-1.5 rounded-full" style={{ background: "#B794F6" }} />
                  {kp}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Definitions */}
      {conspect.definitions && conspect.definitions.length > 0 && (
        <div className="px-4 mb-4">
          <div
            className="rounded-xl p-4"
            style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
          >
            <h2 className="text-sm font-semibold mb-3" style={{ color: "#fff" }}>
              Термины
            </h2>
            <div className="flex flex-col gap-2">
              {conspect.definitions.map((d, i) => (
                <div key={i} className="rounded-lg p-3" style={{ background: "rgba(138,43,226,0.08)" }}>
                  <p className="text-sm font-medium" style={{ color: "#B794F6" }}>
                    {d.term}
                  </p>
                  <p className="text-xs mt-1" style={{ color: "#94A3B8" }}>
                    {d.definition}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Raw VTT info */}
      {conspect.raw_vtt_length && (
        <div className="px-5">
          <p className="text-xs" style={{ color: "#64748B" }}>
            Исходный VTT: {conspect.raw_vtt_length.toLocaleString("ru-RU")} символов
          </p>
        </div>
      )}
    </div>
  );
}
