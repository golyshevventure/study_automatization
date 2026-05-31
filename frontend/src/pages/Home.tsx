import { useState } from "react";
import { FileText, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { notes } from "../data";
import { useDeadlines } from "../hooks/useDeadlines";
import { useAuth } from "../contexts/AuthContext";
import { usePrograms, type Course } from "../hooks/usePrograms";
import DeadlineCard from "../components/DeadlineCard";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";
const neonShadowLight = "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)";



function HomeHeader() {
  const { user } = useAuth();

  const displayName = user?.full_name || user?.email || "Пользователь";
  const avatarSrc =
    user?.avatar_url ||
    `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=8a2be2&color=fff&size=96`;

  return (
    <div className="px-5 pt-8 pb-6 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium mb-1" style={{ color: "rgba(255,255,255,0.7)" }}>
          Студент Нетологии
        </p>
        <h1 className="text-2xl font-bold" style={{ color: "#fff", textShadow: neonShadowLight }}>
          {displayName}
        </h1>
      </div>
      <img
        src={avatarSrc}
        alt={displayName}
        className="w-12 h-12 rounded-full"
        style={{ boxShadow: "0 0 10px rgba(138, 43, 226, 0.5)" }}
      />
    </div>
  );
}

function CourseCard({ course }: { course: Course }) {
  const navigate = useNavigate();
  const isProfession = course.type === "Профессия";
  const MAX_VISIBLE_MODULES = 5;

  return (
    <div
      onClick={() => navigate(`/course/${course.id}`, { state: { course } })}
      className="rounded-2xl p-4 flex flex-col gap-2 cursor-pointer transition-transform active:scale-[0.98]"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        boxShadow: neonShadow,
      }}
    >
      <div className="flex items-center justify-between">
        <span
          className="text-xs font-medium px-2 py-0.5 rounded-full"
          style={{
            background: course.passed
              ? "rgba(16, 185, 129, 0.2)"
              : course.progress > 0
              ? "rgba(138, 43, 226, 0.2)"
              : "rgba(148, 163, 184, 0.2)",
            color: course.passed ? "#10B981" : course.progress > 0 ? "#B794F6" : "#94A3B8",
          }}
        >
          {course.passed ? "✅ Пройден" : course.type}
        </span>
        {!isProfession && (
          <span className="text-xs font-bold" style={{ color: "#B794F6" }}>
            {course.progress}%
          </span>
        )}
      </div>

      <p className="text-sm font-medium" style={{ color: "#fff" }}>
        {course.title}
      </p>

      {!isProfession && (
        <div className="w-full h-2 rounded-full" style={{ background: "#334155" }}>
          <div
            className="h-2 rounded-full transition-all"
            style={{
              width: `${course.progress}%`,
              background: "#8a2be2",
              boxShadow: course.progress > 0 ? "0 0 6px rgba(138, 43, 226, 0.5)" : "none",
            }}
          />
        </div>
      )}

      {isProfession && course.modules && (
        <div className="flex items-center gap-1.5 mt-1">
          {course.modules.slice(0, MAX_VISIBLE_MODULES).map((mod, idx) => (
            <div key={idx} className="flex-1 h-1.5 rounded-full" style={{ background: "#334155" }}>
              <div
                className="h-1.5 rounded-full transition-all"
                style={{
                  width: `${mod.progress}%`,
                  background: "#8a2be2",
                  boxShadow: mod.progress > 0 ? "0 0 4px rgba(138, 43, 226, 0.5)" : "none",
                }}
              />
            </div>
          ))}
          {course.modules.length > MAX_VISIBLE_MODULES && (
            <span className="text-xs" style={{ color: "#64748B" }}>
              +{course.modules.length - MAX_VISIBLE_MODULES}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);
  const { deadlines } = useDeadlines("top3");
  const { courses, loading, error } = usePrograms();

  if (loading) {
    return (
      <div
        className="pb-4 flex items-center justify-center"
        style={{
          background:
            "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
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

  if (error) {
    return (
      <div
        className="pb-4 px-5 pt-8 text-center"
        style={{
          background:
            "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
          minHeight: "100%",
        }}
      >
        <HomeHeader />
        <p className="text-sm font-medium mt-4" style={{ color: "#ef4444" }}>
          Ошибка загрузки курсов
        </p>
        <p className="text-xs mt-1" style={{ color: "rgba(255,255,255,0.5)" }}>
          {error}
        </p>
      </div>
    );
  }

  const active = courses
    .filter((c) => !c.passed && c.progress > 0)
    .sort((a, b) => {
      if (a.type === "Профессия" && b.type !== "Профессия") return -1;
      if (a.type !== "Профессия" && b.type === "Профессия") return 1;
      return b.progress - a.progress;
    });

  const notStarted = courses.filter((c) => !c.passed && c.progress === 0);
  const passed = courses.filter((c) => c.passed);

  const allGroups = [
    { title: "Активные", items: active },
    { title: "Не начато", items: notStarted },
    { title: "Пройдено", items: passed },
  ];

  const visibleGroups = showAll
    ? allGroups
    : allGroups.map((g) => ({
        ...g,
        items: g.items.slice(0, g.title === "Активные" ? 3 : 0),
      }));

  const totalCourses = courses.length;
  const hasHidden = active.length > 3 || notStarted.length > 0 || passed.length > 0;

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
      <HomeHeader />

      {/* My Courses */}
      <div className="mt-2 px-4">
        <h2 className="text-lg font-semibold mb-3" style={{ color: "#fff", textShadow: neonShadowLight }}>
          Мои курсы
        </h2>

        <div className="flex flex-col gap-4">
          {visibleGroups.map(
            (group) =>
              group.items.length > 0 && (
                <div key={group.title}>
                  <h3 className="text-xs font-medium uppercase tracking-wider mb-2" style={{ color: "rgba(255,255,255,0.5)" }}>
                    {group.title}
                  </h3>
                  <div className="flex flex-col gap-3">
                    {group.items.map((course) => (
                      <CourseCard key={course.id} course={course} />
                    ))}
                  </div>
                </div>
              )
          )}
        </div>

        {hasHidden && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="w-full mt-4 py-3 rounded-2xl text-sm font-medium transition-all active:scale-95"
            style={{
              background: "rgba(138, 43, 226, 0.15)",
              color: "#B794F6",
              border: "1px solid rgba(138, 43, 226, 0.3)",
              boxShadow: "0 0 10px rgba(138, 43, 226, 0.2)",
            }}
          >
            {showAll ? "Скрыть" : `Показать все (${totalCourses})`}
          </button>
        )}
      </div>

      {/* Upcoming Deadlines */}
      <div className="mt-6 px-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold" style={{ color: "#fff", textShadow: neonShadowLight }}>
            Ближайшие дедлайны
          </h2>
          <button
            onClick={() => navigate("/deadlines")}
            className="flex items-center gap-1 text-sm"
            style={{ color: "#B794F6" }}
          >
            Все <ChevronRight size={16} />
          </button>
        </div>
        <div className="flex flex-col gap-3">
          {deadlines.length === 0 ? (
            <div
              className="rounded-2xl p-6 text-center"
              style={{
                background: "rgba(15, 23, 42, 0.6)",
                boxShadow: neonShadow,
              }}
            >
              <p className="text-sm font-medium" style={{ color: "#fff" }}>
                Нет активных дедлайнов
              </p>
              <p className="text-xs mt-1" style={{ color: "#94A3B8" }}>
                Все задания выполнены или на проверке
              </p>
            </div>
          ) : (
            (() => {
              // Группировка по программе для отображения
              const groups = new Map<string, typeof deadlines>();
              for (const d of deadlines) {
                const key = d.programName;
                if (!groups.has(key)) groups.set(key, []);
                groups.get(key)!.push(d);
              }
              return Array.from(groups.entries()).map(([programName, items]) => (
                <div key={programName}>
                  <p
                    className="text-xs font-medium uppercase tracking-wider mb-2 mt-1"
                    style={{ color: "rgba(255,255,255,0.5)" }}
                  >
                    {programName}
                  </p>
                  <div className="flex flex-col gap-3">
                    {items.map((d) => (
                      <DeadlineCard key={d.id} deadline={d} />
                    ))}
                  </div>
                </div>
              ));
            })()
          )}
        </div>
      </div>

      {/* Recent Notes */}
      <div className="mt-6 px-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold" style={{ color: "#fff", textShadow: neonShadowLight }}>
            Недавние конспекты
          </h2>
          <button
            onClick={() => navigate("/notes")}
            className="flex items-center gap-1 text-sm"
            style={{ color: "#B794F6" }}
          >
            Все <ChevronRight size={16} />
          </button>
        </div>
        <div className="flex flex-col gap-3">
          {notes.slice(0, 3).map((note) => {
            const statusMap: Record<string, { text: string; bg: string; color: string }> = {
              done: { text: "Готово", bg: "rgba(16, 185, 129, 0.15)", color: "#10B981" },
              in_progress: { text: "В процессе", bg: "rgba(138, 43, 226, 0.15)", color: "#B794F6" },
              pending: { text: "Ожидает", bg: "rgba(148, 163, 184, 0.15)", color: "#94A3B8" },
            };
            const status = statusMap[note.status];
            return (
              <button
                key={note.id}
                onClick={() => navigate("/notes/1")}
                className="rounded-2xl p-4 flex items-start gap-3 text-left w-full"
                style={{ background: "rgba(15, 23, 42, 0.6)", boxShadow: neonShadow }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: `${note.subjectColor}20` }}
                >
                  <FileText size={18} color={note.subjectColor} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium" style={{ color: "#fff" }}>
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
        </div>
      </div>
    </div>
  );
}
