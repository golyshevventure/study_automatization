export const subjects = [
  { id: 1, name: "Матанализ", count: 12, color: "#F59E0B", icon: "Calculator", progress: 75 },
  { id: 2, name: "Программирование", count: 8, color: "#10B981", icon: "Code", progress: 60 },
  { id: 3, name: "Маркетинг", count: 5, color: "#EC4899", icon: "TrendingUp", progress: 40 },
  { id: 4, name: "Психология", count: 3, color: "#8B5CF6", icon: "Brain", progress: 30 },
];

export const notes = [
  { id: 1, title: "Пределы функций — определения", subject: "Матанализ", subjectColor: "#F59E0B", date: "22 мая", status: "done" as const },
  { id: 2, title: "Непрерывность и точки разрыва", subject: "Матанализ", subjectColor: "#F59E0B", date: "21 мая", status: "done" as const },
  { id: 3, title: "Производная функции", subject: "Матанализ", subjectColor: "#F59E0B", date: "20 мая", status: "in_progress" as const },
  { id: 4, title: "ООП в Python: классы и объекты", subject: "Программирование", subjectColor: "#10B981", date: "19 мая", status: "done" as const },
  { id: 5, title: "Декораторы и генераторы", subject: "Программирование", subjectColor: "#10B981", date: "18 мая", status: "in_progress" as const },
  { id: 6, title: "4P маркетинг-микс", subject: "Маркетинг", subjectColor: "#EC4899", date: "17 мая", status: "done" as const },
  { id: 7, title: "STP-модель сегментации", subject: "Маркетинг", subjectColor: "#EC4899", date: "16 мая", status: "pending" as const },
  { id: 8, title: "Когнитивные искажения", subject: "Психология", subjectColor: "#8B5CF6", date: "15 мая", status: "done" as const },
];

export const deadlines = [
  { id: 1, title: "ДЗ по матанализу №7", subject: "Матанализ", date: "24 мая", urgent: true },
  { id: 2, title: "Курсовая: прототип", subject: "Программирование", date: "26 мая", urgent: true },
  { id: 3, title: "Тест: Маркетинг-микс", subject: "Маркетинг", date: "28 мая", urgent: false },
  { id: 4, title: "Эссе по когнитивистике", subject: "Психология", date: "30 мая", urgent: false },
];

export const notifications = [
  { id: 1, title: "Новое сообщение в ЛК Нетологии", text: "Преподаватель ответил на ваш вопрос", time: "10 мин назад", type: "important" as const, read: false },
  { id: 2, title: "Дедлайн приближается", text: "ДЗ по матанализу — через 3 дня", time: "1 ч назад", type: "warning" as const, read: false },
  { id: 3, title: "Сводка за неделю готова", text: "Вы изучили 5 конспектов, осталось 2 дедлайна", time: "3 ч назад", type: "info" as const, read: true },
  { id: 4, title: "Новый материал", text: "Доступна лекция 'Производная сложной функции'", time: "Вчера", type: "info" as const, read: true },
  { id: 5, title: "Экзамен назначен", text: "Матанализ — 15 июня, 10:00", time: "Вчера", type: "warning" as const, read: false },
];

export const noteContent = {
  title: "Пределы функций — определения и свойства",
  subject: "Матанализ",
  subjectColor: "#F59E0B",
  date: "22 мая 2025",
  tags: ["Пределы", "Основы"],
  sections: [
    { heading: "Определение предела по Коши", text: "Число A называется пределом функции f(x) в точке a, если для любого ε > 0 существует δ > 0 такое, что для всех x, удовлетворяющих 0 < |x - a| < δ, выполняется |f(x) - A| < ε." },
    { heading: "Определение предела по Гейне", text: "Число A есть предел функции f(x) при x → a, если для любой последовательности xn → a (xn ≠ a), последовательность f(xn) сходится к A." },
    { heading: "Свойства пределов", items: ["lim(f + g) = lim f + lim g", "lim(f · g) = lim f · lim g", "lim(f / g) = lim f / lim g (при lim g ≠ 0)"] },
    { heading: "Примеры решения", text: "lim(x→2) (x² - 4)/(x - 2) = lim(x→2) (x + 2) = 4" },
  ],
};

export const userStats = { notes: 12, subjects: 4, streak: 7 };
