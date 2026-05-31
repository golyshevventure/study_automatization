import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useCourse } from "../hooks/useCourse";
import ModuleCard from "../components/ModuleCard";
import ProgressBar from "../components/ProgressBar";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";
const neonShadowLight = "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)";

export default function CourseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { course, loading, error } = useCourse(id);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center"
        style={{
          background: "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
          minHeight: "100%",
        }}
      >
        <span
          className="inline-block w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"
          style={{ animationDuration: "0.8s" }}
        />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div
        className="px-5 pt-8 text-center"
        style={{
          background: "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
          minHeight: "100%",
        }}
      >
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-sm mb-6"
          style={{ color: "#B794F6" }}
        >
          <ArrowLeft size={16} /> Назад
        </button>
        <p className="text-sm font-medium" style={{ color: "#ef4444" }}>
          {error || "Курс не найден"}
        </p>
      </div>
    );
  }

  const isProfession = course.type === "Профессия";

  return (
    <div
      className="pb-4"
      style={{
        background: "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
        minHeight: "100%",
      }}
    >
      {/* Header */}
      <div className="px-5 pt-6 pb-4">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-sm mb-4 transition-opacity active:opacity-70"
          style={{ color: "#B794F6" }}
        >
          <ArrowLeft size={18} /> Назад
        </button>

        <div className="flex items-center gap-2 mb-2">
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full"
            style={{
              background: course.passed
                ? "rgba(16, 185, 129, 0.2)"
                : "rgba(138, 43, 226, 0.2)",
              color: course.passed ? "#10B981" : "#B794F6",
            }}
          >
            {course.passed ? "✅ Пройден" : course.type}
          </span>
        </div>

        <h1
          className="text-xl font-bold mb-3"
          style={{ color: "#fff", textShadow: neonShadowLight }}
        >
          {course.title}
        </h1>

        {/* Общий прогресс */}
        <div
          className="rounded-2xl p-4 flex flex-col gap-2"
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            boxShadow: neonShadow,
          }}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.7)" }}>
              Общий прогресс
            </span>
            <span className="text-sm font-bold" style={{ color: "#B794F6" }}>
              {course.progress}%
            </span>
          </div>
          <ProgressBar progress={course.progress} height={10} />
        </div>
      </div>

      {/* Modules */}
      <div className="px-4 mt-2">
        <h2
          className="text-lg font-semibold mb-3"
          style={{ color: "#fff", textShadow: neonShadowLight }}
        >
          {isProfession ? "Модули" : "Содержание"}
        </h2>

        <div className="flex flex-col gap-3">
          {course.modules.map((module, idx) => (
            <ModuleCard key={idx} module={module} index={idx} />
          ))}
        </div>
      </div>
    </div>
  );
}
