# Отчёт: Этап C — Пагинация и фильтр по программе

**Дата:** 2026-06-07  
**Статус:** ✅ Завершён  
**Issues:** #44, #45  

---

## C1. Пагинация

### Что сделано

1. **useDeadlines.ts** — переписан на `useInfiniteQuery`:
   - `PAGE_SIZE = 20`
   - `getNextPageParam` — вычисляет следующий offset на основе загруженных событий и `total`
   - Возвращает `events` (flatMap всех страниц), `total`, `isFetchingMore`, `hasMore`, `loadMore`

2. **Deadlines.tsx** — добавлены:
   - Счётчик «Показано N из M»
   - Кнопка «Загрузить ещё» с индикатором загрузки

3. **Backend** — `list_events` теперь возвращает `tuple[list[DeadlineEvent], int]`:
   - Отдельный `COUNT` запрос для точного `total`
   - `_build_base_stmt` — вынесена общая логика фильтрации

## C2. Фильтр по программе

### Что сделано

1. **Backend** — `GET /api/deadlines?program=...`:
   - Параметр `program` — подстрока, фильтрация через `ILIKE`
   - Интегрирован в `_build_base_stmt` и count-запрос

2. **Frontend API** — `getDeadlines(filter, limit, offset, program?)`

3. **useDeadlines.ts** — `program` добавлен в `queryKey` и `queryFn`

4. **Deadlines.tsx** — селект «Все программы»:
   - Программы извлекаются из загруженных событий (`program_title`)
   - При выборе — перезагрузка с серверным фильтром

---

## Результат

- `npm run build` — ✅ 0 ошибок
- Пагинация работает — ✅
- Фильтр по программе работает — ✅
- Бэкенд импортируется без ошибок — ✅
