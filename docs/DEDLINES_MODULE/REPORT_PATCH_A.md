# Отчёт: Этап A — Фронтенд: TS-ошибки и сборка

**Дата:** 2026-06-06  
**Статус:** ✅ Завершён  
**Issues:** #40, #41, #42  

---

## Что сделано

### 1. Установлены недостающие npm-пакеты

```bash
npm install clsx tailwind-merge sonner next-themes
npm install @radix-ui/react-slider @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toggle @radix-ui/react-toggle-group @radix-ui/react-tooltip
npm install class-variance-authority input-otp react-resizable-panels
npm install @radix-ui/react-label @radix-ui/react-menubar @radix-ui/react-navigation-menu @radix-ui/react-popover @radix-ui/react-progress @radix-ui/react-radio-group @radix-ui/react-scroll-area @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-dialog
npm install react-day-picker embla-carousel-react recharts cmdk vaul react-hook-form
```

**Итого:** +97 пакетов, 0 vulnerabilities.

### 2. Исправлены path aliases

- `tsconfig.app.json` — добавлены `baseUrl` + `paths` (`@/*` → `./src/*`)
- `vite.config.ts` — добавлен `resolve.alias { '@': path.resolve(__dirname, './src') }`
- Добавлен `ignoreDeprecations: "6.0"` для `baseUrl`

### 3. Исправлены TS-ошибки неиспользуемых переменных

| Файл | Переменная | Действие |
|------|-----------|----------|
| `DeadlineCard.tsx` | `AlertCircle` | Удалён из импорта |
| `Welcome.tsx` | `navigate` | Удалён импорт `useNavigate` и переменная |

### 4. Исправлены CSS-ошибки сборки

- `toggle-group.tsx` — `gap-[--spacing(var(--gap))]` → `gap-[var(--gap)]`
- `calendar.tsx` — удалён (не использовался, содержал невалидный CSS для lightningcss)

### 5. Home.tsx — проверено

- Уже использует обновлённый `useDeadlines` с новым API
- Типы `DeadlineEvent` совместимы
- Группировка по `program_title` работает

### 6. useDeadlines.ts — не удалён

- Файл уже обновлён до нового API и активно используется в `Home.tsx` и `Deadlines.tsx`
- Содержит актуальную реализацию на React Query

---

## Результат

```
npm run build
✓ built in 15.50s
```

- **0 TS-ошибок**
- **0 CSS-ошибок**
- Сборка успешна: `dist/index.html`, `dist/assets/index-*.css` (56 kB), `dist/assets/index-*.js` (315 kB)
