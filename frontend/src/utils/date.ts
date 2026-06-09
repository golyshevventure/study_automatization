/**
 * Утилиты для работы с датами в локальной таймзоне.
 *
 * ВАЖНО: Не использовать toISOString() для получения даты-строки,
 * т.к. toISOString() конвертирует в UTC и сдвигает дату
 * для положительных таймзон (например, МСК +3 → дата назад на 1 день).
 */

/** Форматирует Date в YYYY-MM-DD в локальной таймзоне. */
export function formatDateKey(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Парсит YYYY-MM-DD в Date (полночь локальной таймзоны). */
export function parseDateKey(key: string): Date {
  const [y, m, d] = key.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Проверяет, что две даты — один и тот же день (локальная таймзона). */
export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/** Форматирует дату в человекочитаемый вид, например "5 июня". */
export function formatDayMonth(date: Date): string {
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}

/** Форматирует дату в день недели + дату, например "Пятница, 5 июня". */
export function formatFullDate(date: Date): string {
  return date.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
