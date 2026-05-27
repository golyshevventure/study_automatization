import type { DeadlineItem, EnrichedDeadlineItem, HomeworkStatus, ProgramGroup, DeadlineFilter } from "../types/deadline";

/**
 * Порог «срочности» — за сколько дней до дедлайна считать задание срочным
 */
const URGENCY_THRESHOLD_DAYS = 3;

/**
 * Статусы, которые НЕ должны отображаться в списке дедлайнов
 */
const HIDDEN_STATUSES: HomeworkStatus[] = ["accepted", "waiting_review"];

/**
 * Маппинг типов заданий на читаемые русские названия
 */
const TYPE_LABELS: Record<DeadlineItem["type"], string> = {
  homework: "Домашнее задание",
  exam: "Экзамен",
  coursework: "Курсовая работа",
  creative: "Творческое задание",
  test: "Тестирование",
  control_work: "Контрольная работа",
};

/**
 * Названия месяцев в родительном падеже
 */
const MONTH_NAMES = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

/**
 * Возвращает текущее время в часовом поясе МСК (+03:00).
 */
export function getNowMsk(): Date {
  const now = new Date();
  const mskString = now.toLocaleString("en-US", { timeZone: "Europe/Moscow" });
  return new Date(mskString);
}

/**
 * Парсит ISO-строку с дедлайном в объект Date.
 */
export function parseDeadline(isoDate: string): Date {
  return new Date(isoDate);
}

/**
 * Проверяет, что дедлайн уже прошёл.
 */
export function isOverdue(deadline: Date, now: Date = getNowMsk()): boolean {
  return deadline.getTime() < now.getTime();
}

/**
 * Проверяет, что дедлайн считается «срочным» — осталось <= URGENCY_THRESHOLD_DAYS.
 */
export function isUrgent(deadline: Date, now: Date = getNowMsk()): boolean {
  if (isOverdue(deadline, now)) return false;
  const diffMs = deadline.getTime() - now.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays <= URGENCY_THRESHOLD_DAYS;
}

/**
 * Проверяет, что просроченный дедлайн находится в пределах последнего месяца.
 * Используется только для главной страницы (Home).
 */
export function isOverdueWithinMonth(deadline: Date, now: Date = getNowMsk()): boolean {
  if (!isOverdue(deadline, now)) return true; // Будущие — всегда проходят
  const diffMs = now.getTime() - deadline.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays <= 30;
}

/**
 * Форматирует дедлайн в человекочитаемую строку.
 *
 * Примеры:
 *   - «Сегодня, 23:59 МСК»
 *   - «Завтра, 10:00 МСК»
 *   - «25 мая, 23:59 МСК»
 */
export function formatDeadline(deadline: Date, now: Date = getNowMsk()): string {
  const day = deadline.getDate();
  const month = MONTH_NAMES[deadline.getMonth()];
  const hours = String(deadline.getHours()).padStart(2, "0");
  const minutes = String(deadline.getMinutes()).padStart(2, "0");
  const timeStr = `${hours}:${minutes} МСК`;

  const deadlineDateOnly = new Date(deadline.getFullYear(), deadline.getMonth(), deadline.getDate());
  const nowDateOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const diffMs = deadlineDateOnly.getTime() - nowDateOnly.getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return `Сегодня, ${timeStr}`;
  }
  if (diffDays === 1) {
    return `Завтра, ${timeStr}`;
  }
  if (diffDays === -1) {
    return `Вчера, ${timeStr}`;
  }

  return `${day} ${month}, ${timeStr}`;
}

/**
 * Возвращает читаемое название типа задания.
 */
export function getTypeLabel(type: DeadlineItem["type"]): string {
  return TYPE_LABELS[type] ?? type;
}

/**
 * Фильтрует дедлайны: убирает выполненные (accepted) и на проверке (waiting_review).
 */
export function filterVisibleDeadlines(items: DeadlineItem[]): DeadlineItem[] {
  return items.filter((item) => !HIDDEN_STATUSES.includes(item.status));
}

/**
 * Фильтрует дедлайны для главной страницы:
 *   - Убирает accepted/waiting_review
 *   - Убирает просроченные старше 1 месяца
 */
export function filterForHome(items: DeadlineItem[], now: Date = getNowMsk()): DeadlineItem[] {
  const visible = filterVisibleDeadlines(items);
  return visible.filter((item) => {
    const d = parseDeadline(item.deadline);
    return isOverdueWithinMonth(d, now);
  });
}

/**
 * Сортирует дедлайны по правилам:
 *   1. Сначала просроченные, отсортированные от ближайшего к now к более старому
 *   2. Затем предстоящие, отсортированные от ближайшего к now к более дальнему
 */
export function sortDeadlines(items: DeadlineItem[], now: Date = getNowMsk()): DeadlineItem[] {
  return items.sort((a, b) => {
    const dateA = parseDeadline(a.deadline);
    const dateB = parseDeadline(b.deadline);
    const overdueA = isOverdue(dateA, now);
    const overdueB = isOverdue(dateB, now);

    if (overdueA && overdueB) {
      return dateB.getTime() - dateA.getTime();
    }
    if (!overdueA && !overdueB) {
      return dateA.getTime() - dateB.getTime();
    }
    return overdueA ? -1 : 1;
  });
}

/**
 * Обогащает DeadlineItem вычисляемыми полями для UI.
 */
export function enrichDeadline(item: DeadlineItem, now: Date = getNowMsk()): EnrichedDeadlineItem {
  const deadlineDate = parseDeadline(item.deadline);
  const overdue = isOverdue(deadlineDate, now);
  const urgent = !overdue && isUrgent(deadlineDate, now);

  let displayStatus: EnrichedDeadlineItem["displayStatus"];
  if (overdue) {
    displayStatus = "overdue";
  } else if (urgent) {
    displayStatus = "urgent";
  } else {
    displayStatus = "normal";
  }

  return {
    ...item,
    isOverdue: overdue,
    isUrgent: urgent,
    displayStatus,
    formattedDate: formatDeadline(deadlineDate, now),
    typeLabel: getTypeLabel(item.type),
  };
}

/**
 * Группирует дедлайны по программе + дисциплине.
 */
export function groupByProgram(items: EnrichedDeadlineItem[]): ProgramGroup[] {
  const map = new Map<string, ProgramGroup>();

  for (const item of items) {
    const key = `${item.programName}::${item.disciplineName}`;
    if (!map.has(key)) {
      map.set(key, {
        programName: item.programName,
        disciplineName: item.disciplineName,
        semester: item.semester,
        deadlines: [],
      });
    }
    map.get(key)!.deadlines.push(item);
  }

  return Array.from(map.values());
}

/**
 * Возвращает топ-N обогащенных дедлайнов, готовых к отображению на главной.
 */
export function getTopDeadlines(
  items: DeadlineItem[],
  limit: number,
  now: Date = getNowMsk()
): EnrichedDeadlineItem[] {
  const filtered = filterForHome(items, now);
  const sorted = sortDeadlines(filtered, now);
  return sorted.slice(0, limit).map((item) => enrichDeadline(item, now));
}

/**
 * Возвращает ВСЕ обогащенные дедлайны для страницы «Все дедлайны».
 * С опциональным фильтром по статусу.
 */
export function getAllDeadlines(
  items: DeadlineItem[],
  filter: DeadlineFilter = "all",
  now: Date = getNowMsk()
): EnrichedDeadlineItem[] {
  const visible = filterVisibleDeadlines(items);
  let enriched = visible.map((item) => enrichDeadline(item, now));

  if (filter !== "all") {
    enriched = enriched.filter((item) => item.displayStatus === filter);
  }

  return sortDeadlines(enriched, now);
}

/**
 * Возвращает количество срочных (urgent) дедлайнов.
 */
export function countUrgentDeadlines(items: DeadlineItem[], now: Date = getNowMsk()): number {
  const visible = filterVisibleDeadlines(items);
  return visible.filter((item) => {
    const d = parseDeadline(item.deadline);
    return !isOverdue(d, now) && isUrgent(d, now);
  }).length;
}

/**
 * Возвращает количество просроченных дедлайнов.
 */
export function countOverdueDeadlines(items: DeadlineItem[], now: Date = getNowMsk()): number {
  const visible = filterVisibleDeadlines(items);
  return visible.filter((item) => isOverdue(parseDeadline(item.deadline), now)).length;
}

/**
 * Возвращает количество дедлайнов по каждому фильтру.
 */
export function getDeadlineCounts(items: DeadlineItem[], now: Date = getNowMsk()) {
  const visible = filterVisibleDeadlines(items);
  const enriched = visible.map((item) => enrichDeadline(item, now));

  return {
    all: enriched.length,
    normal: enriched.filter((d) => d.displayStatus === "normal").length,
    urgent: enriched.filter((d) => d.displayStatus === "urgent").length,
    overdue: enriched.filter((d) => d.displayStatus === "overdue").length,
  };
}
