import { useState } from "react";
import { FileText, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { notes } from "../data";
import { useDeadlines } from "../hooks/useDeadlines";
import { useAuth } from "../contexts/AuthContext";
import DeadlineCard from "../components/DeadlineCard";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";
const neonShadowLight = "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)";

// Демо-данные из API /backend/api/user/programs/progress
const myCourses = [
  {
    id: 5382,
    title: "Big Data: основы работы с большими массивами данных",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 27457,
    title: "Основы Python: создаём телеграм-бота",
    type: "Курс",
    progress: 30,
    passed: true,
  },
  {
    id: 27904,
    title: "Введение в SQL и работу с базой данных",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 28974,
    title: "Data Scientist: с нуля до middle",
    type: "Профессия",
    progress: 0,
    passed: false,
    modules: [
      { title: "Вводная информация для студентов курса", progress: 0 },
      { title: "Бонусный курс. Английский язык для аналитиков", progress: 0 },
      { title: "Основы аналитики и аналитическое мышление", progress: 0 },
      { title: "Основы визуализации данных", progress: 0 },
      { title: "Основы статистики", progress: 0 },
      { title: "Основы Python", progress: 0 },
      { title: "Библиотеки Python для анализа данных", progress: 0 },
      { title: "Статистика в Python", progress: 0 },
      { title: "Итоговый модуль по курсу «Python для анализа данных»", progress: 0 },
      { title: "SQL и получение данных", progress: 0 },
      { title: "Soft Skills", progress: 0 },
      { title: "Математика для Data Science", progress: 0 },
      { title: "Аналитика больших данных", progress: 0 },
      { title: "Работа с признаками и построение моделей", progress: 0 },
      { title: "Основы нейронных сетей", progress: 0 },
      { title: "Рекомендательные системы", progress: 0 },
      { title: "Временные ряды", progress: 0 },
      { title: "Компьютерное зрение", progress: 0 },
      { title: "Обработка естественного языка", progress: 0 },
      { title: "Менеджмент дата-проектов", progress: 0 },
      { title: "Deep Learning", progress: 0 },
      { title: "Итоговый модуль профессии «Data Scientist: с нуля до middle»", progress: 0 },
      { title: "Школа практики", progress: 0 },
    ],
  },
  {
    id: 38064,
    title: "Системный аналитик: первые шаги к профессии",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 38184,
    title: "IT-профессии: как выбрать направление и реализовать себя",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 38396,
    title: "Демокурс бакалавриата «Финансы и анализ данных»",
    type: "Курс",
    progress: 20,
    passed: false,
  },
  {
    id: 38397,
    title: "Вводный курс бакалавриата ТюмГУ «Разработка IT-продуктов и информационных систем»",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 39808,
    title: "DevOps-инженер с нуля",
    type: "Профессия",
    progress: 0,
    passed: false,
    modules: [
      { title: "Вводная информация для студентов «DevOps-инженер с нуля»", progress: 0 },
      { title: "IT-системы и операционная система Linux", progress: 0 },
      { title: "Операционная система Linux	", progress: 0 },
      { title: "Администрирование операционной системы Linux", progress: 0 },
      { title: "Программирование на Bash", progress: 0 },
      { title: "Сеть, сетевые протоколы", progress: 0 },
      { title: "Виртуализация", progress: 0 },
      { title: "Автоматизация и CI/СD", progress: 0 },
      { title: "Мониторинг", progress: 0 },
      { title: "Отказоустойчивость", progress: 0 },
      { title: "Системы хранения и передачи данных", progress: 0 },
      { title: "Реляционные базы данных и администрирование баз данных", progress: 0 },
      { title: "Информационная безопасность", progress: 0 },
      { title: "Курсовой проект по блоку \"Системное администрирование\"", progress: 0 },
      { title: "Системы управления версиями", progress: 0 },
      { title: "Виртуализация и контейнеризация", progress: 0 },
      { title: "Облачная инфраструктура. Terraform", progress: 0 },
      { title: "Система управления конфигурациями", progress: 0 },
      { title: "Непрерывная разработка и интеграция", progress: 0 },
      { title: "Мониторинг и логи", progress: 0 },
      { title: "Микросервисы", progress: 0 },
      { title: "Kubernetes: основы, применение и администрирование", progress: 0 },
      { title: "Организация проекта при помощи облачных провайдеров", progress: 0 },
      { title: "Итоговый модуль профессии DevOps-инженер с нуля", progress: 0 },
      { title: "Митапы для DevOps-разработчиков и системных администраторов", progress: 0 },
    ],
  },
  {
    id: 41550,
    title: "Симулятор «Рабочая неделя веб-разработчика на Python»",
    type: "Курс",
    progress: 6,
    passed: false,
  },
  {
    id: 42827,
    title: "Как начать работать на фрилансе",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 44412,
    title: "Специалист по информационной безопасности: старт карьеры",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 48767,
    title: "Основы анализа данных в SQL, Python, Power BI, DataLens",
    type: "Профессия",
    progress: 1,
    passed: false,
    modules: [
      { title: "Вводная информация для студентов", progress: 10 },
      { title: "Введение в SQL и работу с базой данных", progress: 0 },
      { title: "Основы работы с Python для аналитиков", progress: 0 },
      { title: "Основы визуализации данных", progress: 0 },
      { title: "Подводим итоги обучения и определяем дальнейшие шаги", progress: 0 },
    ],
  },
  {
    id: 50002,
    title: "В поиске своего призвания",
    type: "Курс",
    progress: 0,
    passed: false,
  },
  {
    id: 51838,
    title: "Вводный курс  бакалавриата «Финансы и анализ данных»",
    type: "Курс",
    progress: 59,
    passed: false,
  },
  {
    id: 59690,
    title: "Бакалавриат «Финансы и анализ данных» c Финансовым университетом",
    type: "Профессия",
    progress: 62,
    passed: false,
    modules: [
      { title: "Адаптационный модуль для бакалавриата «Финансы и анализ данных»", progress: 96 },
      { title: "Опрос про обучение в бакалавриате", progress: 0 },
      { title: "1 курс, 2 семестр: Введение в специальность", progress: 82 },
      { title: "1 курс, 2 семестр: Теория вероятностей и математическая статистика в профессиональной деятельности", progress: 75 },
      { title: "1 курс, 2 семестр: Безопасность жизнедеятельности", progress: 92 },
      { title: "1 курс, 2 семестр: Иностранный язык", progress: 69 },
      { title: "1 курс, 2 семестр: Философия", progress: 31 },
      { title: "1 курс, 2 семестр: Логика. Теория аргументации", progress: 42 },
      { title: "1 курс, 2 семестр: Основы российской государственности", progress: 65 },
      { title: "1 курс, 2 семестр: Экономическая теория", progress: 45 },
      { title: "1 курс, 2 семестр: История экономических учений", progress: 17 },
      { title: "1 курс, 2 семестр: Мировая экономика и международные экономические отношения", progress: 58 },
      { title: "1 курс, 2 семестр: Учебно-научный семинар", progress: 30 },
      { title: "1 курс, 2 семестр: Политология", progress: 62 },
      { title: "1 курс, 1 семестр: Элементы высшей математики", progress: 68 },
      { title: "1 курс, 1 семестр: Структуры данных и алгоритмы", progress: 68 },
      { title: "1 курс, 1 семестр: IT-системы в экономике", progress: 84 },
      { title: "1 курс, 1 семестр: Экономическая теория", progress: 85 },
      { title: "1 курс, 1 семестр: Финансовый университет: история и современность", progress: 100 },
      { title: "1 курс, 1 семестр: Иностранный язык", progress: 91 },
      { title: "1 курс, 1 семестр: Физическая культура и спорт", progress: 88 },
      { title: "1 курс, 1 семестр: Основы права", progress: 33 },
      { title: "1 курс, 1 семестр: История России", progress: 22 },
    ],
  },
];


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

function CourseCard({ course }: { course: (typeof myCourses)[0] }) {
  const isProfession = course.type === "Профессия";
  const MAX_VISIBLE_MODULES = 5;

  return (
    <div
      className="rounded-2xl p-4 flex flex-col gap-2"
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

  const active = myCourses
    .filter((c) => !c.passed && c.progress > 0)
    .sort((a, b) => {
      if (a.type === "Профессия" && b.type !== "Профессия") return -1;
      if (a.type !== "Профессия" && b.type === "Профессия") return 1;
      return b.progress - a.progress;
    });
  
  const notStarted = myCourses.filter((c) => !c.passed && c.progress === 0);
  const passed = myCourses.filter((c) => c.passed);

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
            {showAll ? "Скрыть" : `Показать все (${myCourses.length})`}
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
