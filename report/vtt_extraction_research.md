# Исследование: Извлечение VTT-субтитров из Kinescope

> Дата: 2026-05-23
> Категория: reverse engineering / subtitles
> Статус: ✅ Решено

---

## Цель

Найти способ извлечения VTT-субтитров из Kinescope-видео в API-first режиме (без Playwright).

---

## Методология

Проверены 4 гипотезы:
1. **HLS плейлист** — есть ли `#EXT-X-MEDIA:TYPE=SUBTITLES` в `master.m3u8`?
2. **`playerOptions.tracks`** — есть ли субтитры в JSON плеера?
3. **HTML парсинг** — есть ли прямые `.vtt` URL в HTML embed-страницы?
4. **YouTube** — если `youtube_video_id`, использовать `youtube-transcript-api`

---

## Результаты

### ❌ Гипотеза 1: HLS плейлист

```bash
curl master.m3u8
```

Результат: только `#EXT-X-MEDIA:TYPE=AUDIO`, нет `TYPE=SUBTITLES`.

**Вывод:** субтитры не встроены в HLS.

### ❌ Гипотеза 2: playerOptions.tracks

Проверено 4 видео — `tracks` пустые во всех.

```python
playlist = playerOptions["playlist"][0]
tracks = playlist.get("tracks", [])  # → []
```

**Вывод:** Kinescope не использует стандартное поле `tracks` для субтитров.

### ✅ Гипотеза 3: HTML парсинг — РАБОТАЕТ

В HTML embed-страницы Kinescope обнаружены прямые URL на `.vtt` файлы:

```
https://kinescope.io/tMovmrw31bN9CrcsEcsyuf/subtitles/1771397069/a6a17d6d-a1ec-4e45-b345-89d610b69f3b.vtt
```

**Паттерн:** `{video_id}/subtitles/{timestamp}/{uuid}.vtt`

**Доступность:** отдаётся без Referer, HTTP 200.

**Проверка выборки:**

| Видео | Тип | VTT | Длина |
|-------|-----|-----|-------|
| `tMovmrw31bN9CrcsEcsyuf` | webinar | ✅ | **58 493 символа** |
| `bKW4n8cQVZ4wkK8d4wdat7` | video | ✅ | ~30K символов (есть) |
| `dbSLrR1LWpNtrnwK2aXCGw` | video | ❌ | 0 |
| `vrF1XFj81KvN7MeZCPv1W9` | video | ❌ | 0 |

**Вывод:** субтитры есть не у всех видео, но когда есть — они доступны по прямому URL в HTML.

### ⚠️ Гипотеза 4: YouTube

Пока не встречалось `youtube_video_id` в проверенных lesson_items. Если появится — `youtube-transcript-api` готов.

---

## Реализация

### Новая функция: `extract_vtt_text(video_url)`

**Файл:** `Утилиты/audio_extractor.py`

```python
def extract_vtt_text(video_url: str) -> str:
    """Извлекает субтитры (VTT) из Kinescope-видео."""
    # 1. GET к embed-странице с Referer
    # 2. regex: ищем .vtt URL в HTML
    # 3. Скачиваем VTT
    # 4. Парсим WebVTT → plain text
```

### Интеграция в пайплайн

**Файл:** `run_agent.py` — `_get_item_content_api()`

Порядок fallback:
1. Проверить VTT → если есть и длинный (>500 символов) → использовать
2. Если VTT нет → audio fallback (ffmpeg + Whisper)
3. Если аудио не сработало → HTML fallback

---

## Сравнение: VTT vs Whisper

| Параметр | VTT | Whisper |
|----------|-----|---------|
| Скорость | **Мгновенно** (< 1 сек) | ~2-5 минут на видео |
| Точность | 100% (готовые субтитры) | ~95% (распознавание речи) |
| Расход GPU | Нет | RTX 5070 загружается |
| Покрытие | ~50% видео | 100% (если есть аудио) |

---

## Выводы

1. **VTT извлекаются успешно** через HTML-парсинг embed-страницы Kinescope.
2. **Не все видео имеют субтитры** — нужен fallback на Whisper.
3. **VTT предпочтительнее Whisper** — быстрее, точнее, не требует GPU.
4. **YouTube** — отдельный путь через `youtube-transcript-api`.

API-first режим StudyCore теперь имеет **трёхуровневый fallback** для видео:
1. ✅ VTT (если есть)
2. ✅ Whisper (если VTT нет)
3. ❌ Пропуск (если ничего не сработало)

---

*Исследование проведено в рамках реализации API-first режима StudyCore v0.9.0*
