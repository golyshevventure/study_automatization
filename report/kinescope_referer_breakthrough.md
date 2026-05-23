# Отчёт: Прорыв с Kinescope — Referer даёт доступ к master.m3u8

> Дата: 2026-05-23
> Категория: reverse engineering / video extraction
> Статус: ✅ Решено

---

## Проблема

В API-first режиме аудио fallback (Whisper) для Kinescope-видео **не работал**:

- `audio_extractor.resolve_kinescope_video_url()` делал HTTP GET к short URL (`https://kinescope.io/XXXX`)
- Kinescope отвечал `403 Forbidden`
- FFmpeg не мог скачать поток
- Транскрибация видео через Whisper была невозможна без Playwright

---

## Решение

Добавить заголовок **`Referer: https://netology.ru`** в HTTP-запрос к Kinescope.

### Почему это работает

Kinescope — это white-label видеохостинг для Нетологии. Видео привязаны к домену Нетологии. Без Referer Kinescope считает запрос внешним и блокирует его. С Referer от netology.ru — запрос признаётся легитимным.

### Код

```python
headers = {
    "User-Agent": "Mozilla/5.0 ...",
    "Referer": "https://netology.ru",  # ← ключевой заголовок
}
r = requests.get(video_url, headers=headers, timeout=15)
# Теперь r.status_code == 200, а не 403
```

### Что получаем из HTML

С правильным Referer Kinescope отдаёт embed-страницу с `playerOptions`:

```javascript
var playerOptions = {
  "playlist": [{
    "sources": {
      "hls": {
        "src": "https://kinescope.io/{uuid}/master.m3u8?expires=...&sign=..."
      }
    },
    "tracks": []  // субтитры (если есть)
  }]
};
```

Из `playerOptions` извлекаем подписанный `master.m3u8` и отдаём его в ffmpeg.

---

## Результат теста

**Дисциплина:** Мировая экономика (bhebfad-25-memeo-2)
**Раздел:** Тема 1
**Режим:** API-first (`--api`)

| Видео | Транскрипция (символов) | Статус |
|-------|------------------------|--------|
| Часть 1 | 24 391 | ✅ |
| Часть 2 | 27 217 | ✅ |
| **Итого исходный текст** | **53 348** | — |
| **Конспект** | **12 367** | ✅ Сохранён |

**Длительность:** 9 мин 24 сек (включая загрузку Whisper на GPU)

---

## Сравнение до/после

| Параметр | Без Referer (было) | С Referer (стало) |
|----------|-------------------|-------------------|
| HTTP статус | 403 Forbidden | 200 OK |
| Доступ к `playerOptions` | ❌ Нет | ✅ Да |
| Извлечение `master.m3u8` | ❌ Невозможно | ✅ Работает |
| FFmpeg | ❌ Ошибка | ✅ Скачивает аудио |
| Whisper | ❌ Нет входных данных | ✅ 24K–27K символов транскрипции |
| API-first аудио fallback | ❌ Сломан | ✅ Полностью работает |

---

## Файлы, которые изменились

| Файл | Изменение |
|------|-----------|
| `Утилиты/audio_extractor.py` | Добавлен `Referer`, парсинг `playerOptions` JSON, очистка control characters |

---

## Инсайты для будущего

1. **Referer — это не единственная защита.** Kinescope также проверяет `User-Agent` и, возможно, cookies. Но для embed-страниц достаточно Referer + User-Agent.
2. **Подписанные URL.** `master.m3u8` содержит `expires` и `sign` — они валидны ограниченное время. Нельзя кэшировать надолго.
3. **Субтитры.** В `playerOptions` есть поле `tracks`, но в проверенных видео оно пустое. Возможно, VTT загружается динамически отдельным запросом. Это требует дополнительного исследования.

---

## Вывод

API-first режим StudyCore теперь **полностью функционален**:
- ✅ Текстовые материалы — через API
- ✅ PDF/DOCX/PPTX — через API (`files[]`)
- ✅ Видео/вебинары — аудио fallback через `master.m3u8` + Whisper
- ❌ VTT (субтитры) — требует дополнительного исследования

Playwright нужен только для **авторизации** (получения cookies). Весь остальной пайплайн работает через HTTP.

---

*Отчёт составлен после успешного прогона Темы 1 в API-first режиме.*
