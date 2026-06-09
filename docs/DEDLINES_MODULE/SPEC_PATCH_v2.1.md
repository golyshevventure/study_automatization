# SPEC: Calendar Module Patch v2.1

**Author:** Kimi Agent
**Date:** 2026-05-23
**Status:** In Progress
**Base:** SPEC_CALENDAR_v2.0.md (phases A–E completed)
**Milestone:** [Calendar v2.1 Patch](https://github.com/golyshevventure/study_automatization/milestone/5)

---

## 1. Context

Calendar v2.0 функционально работает, но после UAT выявлены критические UX-проблемы и баги:
- Сдвиг дат из-за UTC→local timezone бага
- Сетка 7×6 создаёт пустую строку для большинства месяцев
- Фильтры были удалены без согласования
- Клик на ячейку сразу открывает детали первого события — неудобно, если событий несколько
- Оформление выглядит "плоским", нет глубины и нативного календарного UX

## 2. Goals

- Исправить сдвиг дат (timezone bug)
- Сделать сетку месяца адаптивной (4 или 5 недель)
- Вернуть фильтры по типу событий
- Реализовать DaySheet (список событий дня при клике на ячейку)
- Улучшить визуальное оформление (тени, hover, типографика)
- Сохранить фирменный neon-стиль StudyCore

## 3. Non-Goals

- Backend API изменения не требуются
- Создание пользовательских событий (backend) — только UI-заглушка
- Push-уведомления
- Drag-and-drop событий

## 4. Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-001 | Даты отображаются корректно без сдвига UTC→local | Must | Pending |
| REQ-002 | Сетка месяца = ровно столько недель, сколько нужно (4 или 5) | Must | Pending |
| REQ-003 | Фильтры (Все/Занятия/Работы/Контроль) доступны в календаре | Must | Pending |
| REQ-004 | Клик на ячейку даты открывает DaySheet со списком событий дня | Must | Pending |
| REQ-005 | В DaySheet клик на событие открывает детали (EventDetailModal) | Must | Pending |
| REQ-006 | В DaySheet есть кнопка "Добавить событие" (UI-заглушка) | Should | Pending |
| REQ-007 | Ячейки имеют hover/active состояния и визуальную глубину | Should | Pending |
| REQ-008 | Текущий день выделен заметнее (свечение + цвет) | Should | Pending |
| REQ-009 | Mobile-first: читаемость на 375px экране | Should | Pending |

## 5. Architecture

### 5.1 Components

```
Calendar.tsx
├── CalendarHeader
├── CalendarFilterBar         ← восстановить
├── CalendarLegend            ← легенда цветов (оставить)
├── CalendarMonthView
│   ├── CalendarDayCell       ← hover/active, правильные даты
│   └── DaySheet              ← НОВЫЙ: bottom sheet списка событий дня
│       ├── DaySheetHeader    ← дата + кнопка закрыть + "+"
│       ├── DaySheetEventItem ← строка события
│       └── EventDetailModal  ← переиспользовать
├── CalendarWeekView
│   └── EventDetailModal
└── MonthSkeleton / WeekSkeleton
```

### 5.2 Date Formatting Rule (critical)

**ЗАПРЕЩЕНО:** `date.toISOString().split("T")[0]` — сдвигает дату в UTC.

**ОБЯЗАТЕЛЬНО:**
```ts
function formatDateKey(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}
```

Применить во ВСЕХ компонентах: `CalendarMonthView`, `CalendarWeekView`, `MiniCalendar`, `CalendarService` (backend уже правильный).

## 6. Implementation Plan

### Phase 1: Bug Fixes (критично)
- [ ] Исправить форматирование дат (UTC→local) во всех компонентах
- [ ] Сделать сетку месяца 7×4 или 7×5 (динамически)
- [ ] Вернуть фильтры: восстановить CalendarFilterBar, обновить useCalendar

### Phase 2: DaySheet UX
- [ ] Создать DaySheet компонент (bottom sheet)
- [ ] CalendarDayCell: клик → DaySheet (не EventDetailModal напрямую)
- [ ] DaySheet: список событий дня с сортировкой по времени
- [ ] DaySheet: клик на событие → EventDetailModal
- [ ] DaySheet: кнопка "+ Добавить событие" (alert/mock)
- [ ] MiniCalendar: клик на день с событиями → DaySheet

### Phase 3: Polish
- [ ] Hover/active состояния ячеек
- [ ] Улучшить выделение текущего дня (свечение)
- [ ] Типографика: увеличить контраст
- [ ] Проверить mobile-first на 375px
- [ ] Build → 0 ошибок

### Phase 4: Closure
- [ ] Git commit + push
- [ ] Обновить SPEC_CALENDAR_v2.0.md
- [ ] Закрыть GitHub issues

## 7. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| RISK-001 | Дата-форматирование останется где-то неисправленным | Medium | High | Глобальный grep `toISOString` + тест на всех компонентах |
| RISK-002 | DaySheet перегружает mobile UX | Low | Medium | Максимум 70% высоты экрана, swipe-to-close |

## 8. Acceptance Criteria

- [ ] Событие 5 июня в 14:20 отображается в ячейке "5", не "6"
- [ ] Месяц апрель 2026 = 5 недель, февраль 2026 = 4 недели
- [ ] Фильтры переключаются, меняют отображаемые события
- [ ] Клик на ячейку с 3 событиями → DaySheet со списком из 3
- [ ] Клик на событие в DaySheet → детали
- [ ] Build проходит, 0 TypeScript ошибок
