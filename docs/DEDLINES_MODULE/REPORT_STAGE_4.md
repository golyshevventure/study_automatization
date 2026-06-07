# Отчёт: Этап 4 — Frontend

**Дата:** 2026-06-05  
**Статус:** ✅ Завершён  

---

## Что сделано

### 4.1 API-клиент

**Файл:** `frontend/src/api/deadlines.ts`

| Функция | Endpoint | Описание |
|---------|----------|----------|
| `syncDeadlines()` | POST `/deadlines/sync` | Синхронизация с Netology |
| `getDeadlines(filter, limit, offset)` | GET `/deadlines?filter=...` | Список событий |
| `getDeadlineDetail(id)` | GET `/deadlines/{id}` | Детали события |

### 4.2 Типы

**Файл:** `frontend/src/types/deadline.ts`

- `DeadlineEvent` — единый тип для всех событий (task/test/webinar)
- `DeadlineFilter` — "lessons" | "works" | "control" | "all"
- `DeadlineListResponse` / `DeadlineSyncResponse` — ответы API

### 4.3 Хук `useDeadlines`

**Файл:** `frontend/src/hooks/useDeadlines.ts`

- Использует `@tanstack/react-query` для кеширования
- Поддерживает `useDeadlines(filter, limit)`
- `doSync()` — мутация синхронизации с инвалидацией кеша
- `staleTime: 5 минут`

### 4.4 Страница `Deadlines.tsx`

**Файл:** `frontend/src/pages/Deadlines.tsx`

- **Заголовок:** «Ближайшие события»
- **Фильтры:** Занятия / Работы / Контроль / Все (с иконками)
- **Кнопка синхронизации** с анимацией spinner'а
- **Состояния:** загрузка, пустой список, список событий
- **Убрано:** фильтры "Срочно"/"Просрочено" (по требованию — только будущее)

### 4.5 Компонент `DeadlineCard.tsx`

**Файл:** `frontend/src/components/DeadlineCard.tsx`

- Цветная полоска-индикатор по типу события:
  - 🟠 task/test — оранжевая
  - 🔴 exam/credit — красная
  - 🔵 lesson/consultation — синяя
  - 🟢 passed/approved — зелёная
- Иконка по типу события
- Подпись типа: «ДЗ / Работа», «Тест», «Экзамен», «Зачёт», «Занятие»
- Бейдж «Выполнено» для passed-событий
- Бейдж «N вариантов» для сгруппированных
- Дата с припиской «МСК»

### 4.6 Обновление `Home.tsx`

- Использует новый `useDeadlines("all", 3)` для топ-3 событий на главной
- Передаёт `event` в `DeadlineCard`

### 4.7 Удалены демоданные

- `frontend/src/data/realDeadlines.ts`
- `frontend/src/utils/deadlineUtils.ts`

---

## Проверка сборки

```
npm run build
```

Ошибки TypeScript в наших файлах: **0**

Оставшиеся ошибки — отсутствующие npm-пакеты проекта (radix-ui, clsx, tailwind-merge) и неиспользуемые переменные в других файлах. Не связаны с модулем дедлайнов.

---

## Следующий этап

**Этап 6:** Тесты — E2E + группировка + фильтры
