/**
 * Типы заданий в системе дедлайнов
 */
export type DeadlineTaskType =
  | "homework"
  | "exam"
  | "coursework"
  | "creative"
  | "test"
  | "control_work";

/**
 * Статус выполнения домашнего задания из API Нетологии
 */
export type HomeworkStatus =
  | null
  | "in_progress"
  | "accepted"
  | "waiting_review";

/**
 * Элемент дедлайна — единичное задание/работа/экзамен
 */
export interface DeadlineItem {
  id: number;
  /** Название программы (например, "Бакалавриат «Финансы и анализ данных»") */
  programName: string;
  /** Название дисциплины/предмета (например, "Философия") */
  disciplineName: string;
  /** Семестр (например, "1 курс, 2 семестр") */
  semester: string;
  /** Название конкретного задания */
  title: string;
  /** Тип задания */
  type: DeadlineTaskType;
  /** Дедлайн в ISO-формате с timezone (+03:00 = МСК) */
  deadline: string;
  /** Статус выполнения из API */
  status: HomeworkStatus;
}

/**
 * Отображаемый статус после фильтрации и обработки
 */
export type DisplayStatus = "overdue" | "urgent" | "normal";

/**
 * Обогащенный элемент дедлайна с вычисляемыми полями для UI
 */
export interface EnrichedDeadlineItem extends DeadlineItem {
  isOverdue: boolean;
  isUrgent: boolean;
  displayStatus: DisplayStatus;
  formattedDate: string;
  typeLabel: string;
}

/**
 * Группировка дедлайнов по программе/дисциплине
 */
export interface ProgramGroup {
  programName: string;
  disciplineName: string;
  semester: string;
  deadlines: EnrichedDeadlineItem[];
}

/**
 * Фильтр для страницы «Все дедлайны»
 */
export type DeadlineFilter = "all" | "normal" | "urgent" | "overdue";
