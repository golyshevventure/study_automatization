import asyncio
import logging
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Утилиты"))

from netology_scraper import NetologyScraper
from netology_api_client import NetologyAPIClient
from netology_auth import ensure_netology_login
from dotenv import load_dotenv
from generate_summary import generate_summary, classify_lesson_via_llm
from second_brain_cleanup import remove_old_structure, ensure_new_structure, ensure_subject_dirs
from material_classifier import (
    classify_material,
    category_folder,
    should_skip,
    classify_lesson_strategy,
    classify_lesson_strategy_with_confidence,
    classify_item,
    is_structure_page,
)
from subject_index import update_subject_index, reset_subject_index
from conspect_writer import write_material, write_large_file_stub, wiki_link
from audio_extractor import extract_audio_from_mp4, extract_vtt_text
from local_whisper import transcribe_to_text
from logger_config import setup_logging, get_logger

load_dotenv()

logger = get_logger("run_agent")
setup_logging()

SECONDBRAIN = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain"
STUDY_DIR = os.path.join(SECONDBRAIN, "Учеба (Фин. Ун.)")


def safe_filename(name, max_len=80):
    name = re.sub(r'[\\/:"*?<>|]', "", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0]
    return name


def _file_exists(subject_name, section_name, lesson_title):
    """Проверяет, существует ли уже файл для этого материала."""
    display_title = (
        f"{section_name} — {lesson_title}"
        if lesson_title.lower() not in section_name.lower()
        else section_name
    )
    category = classify_material(lesson_title, section_name)
    folder_name = category_folder(category)
    safe_title = re.sub(r'[\\/:"*?<>|]', "", display_title).strip()
    if len(safe_title) > 80:
        safe_title = safe_title[:80].rsplit(" ", 1)[0]
    safe_subject = re.sub(r'[\\/:"*?<>|]', "", subject_name).strip()
    if len(safe_subject) > 80:
        safe_subject = safe_subject[:80].rsplit(" ", 1)[0]
    filepath = os.path.join(STUDY_DIR, "Дисциплины", safe_subject, folder_name, f"{safe_title}.md")
    return os.path.exists(filepath)


def process_material(
    subject_name,
    section_name,
    lesson_title,
    lesson_text,
    lesson_href="",
    force=False,
    category_override=None,
):
    """
    Обрабатывает один материал: классифицирует, генерирует конспект или заглушку, сохраняет.
    category_override: если задан, использует эту категорию вместо авто-классификации.
    """
    display_title = (
        f"{section_name} — {lesson_title}"
        if lesson_title.lower() not in section_name.lower()
        else section_name
    )

    print(f"\n{'='*60}")
    print(f"🎓 {display_title}")
    print(f"{'='*60}")

    # Пропускаем домашки, контрольные, эссе
    if should_skip(lesson_title, section_name):
        print(f"   ⏭️  Пропускаем (домашнее задание / контрольная / эссе)")
        return None, None

    # Классифицируем материал
    if category_override:
        category = category_override
    else:
        category = classify_material(lesson_title, section_name)
    folder_name = category_folder(category)
    print(f"   📁 Категория: {folder_name}")

    # Deduplication
    safe_title = re.sub(r'[\\/:"*?<>|]', "", display_title).strip()
    if len(safe_title) > 80:
        safe_title = safe_title[:80].rsplit(" ", 1)[0]
    safe_subject = re.sub(r'[\\/:"*?<>|]', "", subject_name).strip()
    if len(safe_subject) > 80:
        safe_subject = safe_subject[:80].rsplit(" ", 1)[0]
    filepath = os.path.join(STUDY_DIR, "Дисциплины", safe_subject, folder_name, f"{safe_title}.md")
    if os.path.exists(filepath) and not force:
        print(f"   ⏭️  Уже существует, пропускаем (используй --force для перезаписи)")
        return folder_name, wiki_link(subject_name, folder_name, display_title)

    # Большой файл (>150K)
    if lesson_text is None:
        print(f"   ⚠️ Файл слишком большой, создаём заглушку")
        write_large_file_stub(subject_name, folder_name, display_title, lesson_href)
        return folder_name, wiki_link(subject_name, folder_name, display_title)

    print(f"   Символов: {len(lesson_text)}")

    # Слишком мало текста
    if not lesson_text or len(lesson_text) < 300:
        print(f"   ⚠️ Слишком мало текста ({len(lesson_text)} симв.), пропускаем")
        return None, None

    # Генерация конспекта
    print("   ⏳ Генерация конспекта...")
    raw_summary = generate_summary(lesson_text, subject_name, display_title)
    if raw_summary.startswith("Ошибка"):
        print(f"   ❌ {raw_summary}")
        return None, None

    # Сохраняем
    write_material(subject_name, folder_name, display_title, raw_summary, lesson_href)
    link = wiki_link(subject_name, folder_name, display_title)
    print("   ✅ Готово")
    return folder_name, link


async def _get_item_content_api(api_client, item, subject_name):
    """
    API-версия получения контента item'а.
    Возвращает dict с text, video_url, title, href, is_structure.
    """
    ic = await api_client.fetch_item_content(item, subject_name)

    # Audio fallback (тот же guard, что и в Playwright-версии)
    text = ic.get("text", "")
    video_url = ic.get("video_url", "")
    is_structure = ic.get("is_structure", False)

    if is_structure:
        print(f"   ⚠️ Обнаружена страница с описанием программы курса (structure page)")
        if video_url:
            print(f"   🎬 Попробуем аудио fallback несмотря на длинный текст...")
            text = None

    # Пробуем извлечь VTT-субтитры (быстрее и точнее Whisper)
    vtt_text = ""
    if video_url and (not text or len(text) < 1000):
        print(f"   📝 Проверяем субтитры (VTT)...")
        try:
            vtt_text = extract_vtt_text(video_url)
            if vtt_text and len(vtt_text) > 500:
                print(f"   ✅ VTT: {len(vtt_text)} символов")
                text = f"[Субтитры вебинара]\n\n{vtt_text}"
                is_structure = False
            else:
                print(f"   ⚠️ Субтитры не найдены или слишком короткие")
        except Exception as e:
            print(f"   ⚠️ Ошибка VTT: {e}")

    # Audio fallback: если нет VTT и текст короткий
    if video_url and (not text or len(text) < 1000):
        if is_structure:
            print(f"   🎬 Извлекаем аудио из-за structure page...")
        else:
            print(
                f"   🎬 Найдено видео ({ic['title']}), текст короткий ({len(text) if text else 0} симв.), извлекаем аудио..."
            )
        try:
            audio_path = extract_audio_from_mp4(
                video_url, output_dir=f"data/audio/{safe_filename(subject_name)}"
            )
            print(f"   🎙️  Транскрибируем аудио...")
            transcript = transcribe_to_text(audio_path)
            if transcript and len(transcript) > 500:
                text = f"[Транскрипция вебинара]\n\n{transcript}"
                print(f"   ✅ Транскрипция: {len(transcript)} символов")
                is_structure = False
            else:
                print(f"   ⚠️ Транскрипция слишком короткая, используем HTML fallback")
        except Exception as e:
            print(f"   ⚠️ Ошибка аудио: {e}")
    elif video_url and not is_structure:
        print(
            f"   🎬 Найдено видео, но текст уже достаточно длинный ({len(text)} симв.), аудио не требуется"
        )

    return {
        "title": ic["title"],
        "href": ic["href"],
        "text": text,
        "video_url": video_url,
        "is_structure": is_structure,
    }


async def _get_item_content(scraper, item, subject_name):
    """
    Получает контент одного item (Playwright-версия).
    Возвращает dict с text, video_url, title, href.
    Audio fallback: если видео есть, но текст короткий (<1000 симв.) — транскрибируем.
    Если текст уже достаточно длинный (VTT, PDF, хороший HTML) — используем его.
    Structure page detection: если HTML — это описание программы курса, помечаем.
    """
    text, video_url = await scraper.get_lesson_text_content(item["href"])

    # Detect structure page (course syllabus instead of real content)
    is_structure = False
    if text and is_structure_page(text):
        print(f"   ⚠️ Обнаружена страница с описанием программы курса (structure page)")
        is_structure = True
        # If video exists, try audio fallback even if text > 1000
        if video_url:
            print(f"   🎬 Попробуем аудио fallback несмотря на длинный текст...")
            text = None  # Force audio fallback

    # Audio fallback: если есть видео И текст короткий/пустой
    if video_url and (not text or len(text) < 1000):
        if is_structure:
            print(f"   🎬 Извлекаем аудио из-за structure page...")
        else:
            print(
                f"   🎬 Найдено видео ({item['title']}), текст короткий ({len(text) if text else 0} симв.), извлекаем аудио..."
            )
        try:
            audio_path = extract_audio_from_mp4(
                video_url, output_dir=f"data/audio/{safe_filename(subject_name)}"
            )
            print(f"   🎙️  Транскрибируем аудио...")
            transcript = transcribe_to_text(audio_path)
            if transcript and len(transcript) > 500:
                text = f"[Транскрипция вебинара]\n\n{transcript}"
                print(f"   ✅ Транскрипция: {len(transcript)} символов")
                is_structure = False  # Audio replaced structure text
            else:
                print(f"   ⚠️ Транскрипция слишком короткая, используем HTML fallback")
        except Exception as e:
            print(f"   ⚠️ Ошибка аудио: {e}")
    elif video_url and not is_structure:
        print(
            f"   🎬 Найдено видео, но текст уже достаточно длинный ({len(text)} симв.), аудио не требуется"
        )

    return {
        "title": item["title"],
        "href": item["href"],
        "text": text,
        "video_url": video_url,
        "is_structure": is_structure,
    }


async def _collect_lesson_items(scraper, program_id, lesson_id, fallback_links, section_name):
    """Собирает items для одного lesson."""
    items = await scraper.get_discipline_lessons(program_id, lesson_id, fallback_links)
    if not items and fallback_links:
        print(f"   🔄 Под-занятия не найдены, берём ссылки раздела напрямую")
        items = [
            {"title": link.get("text", section_name), "href": link["href"], "locked": False}
            for link in fallback_links
            if link.get("href")
        ]
    return items


async def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python run_agent.py <program_id>  — собрать всю программу")
        print(
            "  python run_agent.py <program_id> --subject 'Название'  — только разделы с этим словом"
        )
        print(
            "  python run_agent.py <program_id> --name 'Имя предмета'  — задать имя папки вручную"
        )
        print("  python run_agent.py <program_id> --force  — перезаписать существующие файлы")
        print("  python run_agent.py <program_id> --api  — использовать API-first (быстрее)")
        sys.exit(1)

    program_id = sys.argv[1]
    target_subjects = []
    subject_name_override = None
    force = "--force" in sys.argv
    use_api = "--api" in sys.argv
    for i, arg in enumerate(sys.argv):
        if arg == "--subject" and i + 1 < len(sys.argv):
            target_subjects.append(sys.argv[i + 1])
        if arg == "--name" and i + 1 < len(sys.argv):
            subject_name_override = sys.argv[i + 1]

    # Очистка старой структуры
    print("🧹 Очистка старой структуры Second Brain...")
    remove_old_structure()
    ensure_new_structure()

    # Авторизация
    scraper = NetologyScraper(headless=True)
    await scraper.start()
    login_ok = await ensure_netology_login(scraper.page, program_id)

    if not login_ok:
        print("🔓 Cookies протухли, переключаюсь на видимый браузер для ручного входа...")
        await scraper.stop()
        scraper = NetologyScraper(headless=False)
        await scraper.start()
        login_ok = await ensure_netology_login(scraper.page, program_id)
        if not login_ok:
            print("❌ Не удалось авторизоваться в Нетологии")
            await scraper.stop()
            sys.exit(1)

    try:
        if use_api:
            await _run_api_mode(scraper, program_id, subject_name_override, target_subjects, force)
        else:
            await _run_playwright_mode(
                scraper, program_id, subject_name_override, target_subjects, force
            )
    except KeyboardInterrupt:
        print("\n\n🛑 Остановлено пользователем")
    finally:
        try:
            await scraper.save_cookies()
        except Exception:
            pass
        await scraper.stop()


async def _run_playwright_mode(
    scraper, program_id, subject_name_override, target_subjects, force
):
    """Оригинальный Playwright-режим."""
    print("=" * 60)
    print("🔍 Сбор структуры...")
    print("=" * 60)

    program_title, disciplines = await scraper.get_program_disciplines(program_id)

    # Определяем subject_name
    if subject_name_override:
        subject_name = subject_name_override
    elif program_title and program_title.strip():
        subject_name = program_title
    elif disciplines:
        # Ищем первую "содержательную" дисциплину (не служебную)
        meaningful = [
            d
            for d in disciplines
            if not any(
                kw in d.get("title", "").lower()
                for kw in [
                    "рабочая программа",
                    "домашнее задание",
                    "контрольная",
                    "экзамен",
                    "опрос",
                    "консультация",
                    "вебинар",
                    "творческое",
                ]
            )
        ]
        subject_name = meaningful[0]["title"] if meaningful else disciplines[0]["title"]
    else:
        subject_name = "Предмет"

    print(f"\n📚 Предмет: {subject_name}")
    print(f"   Разделов: {len(disciplines)}")

    if target_subjects:
        print(f"   🔍 Фильтр: только разделы содержащие {target_subjects}")
    if subject_name_override:
        print(f"   📝 Имя предмета задано вручную: {subject_name_override}")

    # Создаём папки дисциплины
    ensure_subject_dirs(subject_name)
    reset_subject_index(subject_name)

    # Собираем ссылки по категориям
    conspect_links = set()
    material_links = set()
    info_links = set()

    seen_hrefs = set()

    for disc in disciplines:
        disc_title = disc["title"]

        def _matches_filter(title, filters):
            t_lower = title.lower()
            for f in filters:
                f_lower = f.lower()
                if f_lower not in t_lower:
                    continue
                # Строгая проверка: после подстроки должна быть граница слова
                idx = t_lower.index(f_lower)
                end = idx + len(f_lower)
                if end == len(t_lower) or t_lower[end] in " \n«»().,;:!?-–—":
                    return True
            return False

        if target_subjects and not _matches_filter(disc_title, target_subjects):
            continue

        if disc.get("locked"):
            print(f"\n   🔒 {disc_title} — заблокировано, пропускаем")
            continue

        print(f"\n📂 {disc_title}")

        # === Legacy vs New structure ===
        if "program_id" in disc and disc["program_id"]:
            # Новая структура: модуль → занятия → items
            module_lessons = await scraper.get_module_lessons(disc["program_id"])
            for ml in module_lessons:
                if ml.get("locked"):
                    print(f"   🔒 {ml.get('title', 'Без названия')}")
                    continue
                section_name = ml.get("title", disc_title)
                items = await _collect_lesson_items(
                    scraper, disc["program_id"], ml["lesson_id"], [], section_name
                )
                await _process_items(
                    scraper,
                    subject_name,
                    section_name,
                    items,
                    conspect_links,
                    material_links,
                    info_links,
                    seen_hrefs,
                    force,
                )
        else:
            # Legacy структура: disc = lesson, items внутри
            section_name = disc_title
            items = await _collect_lesson_items(
                scraper, program_id, disc["lesson_id"], disc.get("links", []), section_name
            )
            await _process_items(
                scraper,
                subject_name,
                section_name,
                items,
                conspect_links,
                material_links,
                info_links,
                seen_hrefs,
                force,
            )

        print(f"   ✅ Раздел завершён")
        await asyncio.sleep(1)

    # Обновляем файл предмета
    update_subject_index(subject_name, conspect_links, material_links, info_links)

    await scraper.save_cookies()
    print("\n" + "=" * 60)
    print("🏁 Всё готово!")
    print("=" * 60)


async def _run_api_mode(scraper, program_id, subject_name_override, target_subjects, force):
    """API-first режим: HTTP-запросы вместо Playwright для структуры и контента."""
    print("=" * 60)
    print("⚡ API-first режим")
    print("=" * 60)

    api = NetologyAPIClient()

    # Проверяем авторизацию
    try:
        profile = await api.get_program_info(program_id)
    except Exception:
        print("🔓 Cookies протухли, обновляем через Playwright...")
        await scraper.save_cookies()
        api = NetologyAPIClient()
        profile = await api.get_program_info(program_id)

    program_title = profile.get("common", {}).get("name", "")
    lessons = await api.get_program_schedule(program_id)

    # Определяем subject_name
    if subject_name_override:
        subject_name = subject_name_override
    elif program_title and program_title.strip():
        subject_name = program_title
    elif lessons:
        meaningful = [
            l
            for l in lessons
            if not any(
                kw in l.get("title", "").lower()
                for kw in [
                    "рабочая программа",
                    "домашнее задание",
                    "контрольная",
                    "экзамен",
                    "опрос",
                    "консультация",
                    "вебинар",
                    "творческое",
                ]
            )
        ]
        subject_name = meaningful[0]["title"] if meaningful else lessons[0]["title"]
    else:
        subject_name = "Предмет"

    print(f"\n📚 Предмет: {subject_name}")
    print(f"   Разделов: {len(lessons)}")

    if target_subjects:
        print(f"   🔍 Фильтр: только разделы содержащие {target_subjects}")
    if subject_name_override:
        print(f"   📝 Имя предмета задано вручную: {subject_name_override}")

    # Создаём папки дисциплины
    ensure_subject_dirs(subject_name)
    reset_subject_index(subject_name)

    # Собираем ссылки по категориям
    conspect_links = set()
    material_links = set()
    info_links = set()
    seen_hrefs = set()

    for lesson in lessons:
        lesson_title = lesson.get("title", "")

        def _matches_filter(title, filters):
            t_lower = title.lower()
            for f in filters:
                f_lower = f.lower()
                if f_lower not in t_lower:
                    continue
                idx = t_lower.index(f_lower)
                end = idx + len(f_lower)
                if end == len(t_lower) or t_lower[end] in " \n«»().,;:!?-–—":
                    return True
            return False

        if target_subjects and not _matches_filter(lesson_title, target_subjects):
            continue

        if lesson.get("locked"):
            print(f"\n   🔒 {lesson_title} — заблокировано, пропускаем")
            continue

        print(f"\n📂 {lesson_title}")

        section_name = lesson_title
        raw_items = lesson.get("lesson_items", [])

        # Формируем items в формате, совместимом с _process_items
        items = []
        for it in raw_items:
            if it.get("locked"):
                continue
            path = it.get("path", "")
            href = f"https://netology.ru{path}" if path else ""
            items.append({
                "title": it.get("title", ""),
                "href": href,
                "locked": False,
                "id": it.get("id"),
                "type": it.get("type"),
            })

        await _process_items_api(
            api,
            subject_name,
            section_name,
            items,
            conspect_links,
            material_links,
            info_links,
            seen_hrefs,
            force,
        )

        print(f"   ✅ Раздел завершён")

    # Обновляем файл предмета
    update_subject_index(subject_name, conspect_links, material_links, info_links)

    await api.close()
    print("\n" + "=" * 60)
    print("🏁 API-first прогон завершён!")
    print("=" * 60)


async def _process_items(
    scraper,
    subject_name,
    section_name,
    items,
    conspect_links,
    material_links,
    info_links,
    seen_hrefs,
    force,
):
    """
    Обрабатывает items одного lesson.
    Определяет стратегию (merge/split), выполняет audio fallback, сохраняет.
    Hybrid classification: keyword first, LLM fallback if uncertain.
    """
    # Deduplication href'ов
    unique_items = []
    for item in items:
        if item["href"] in seen_hrefs:
            continue
        seen_hrefs.add(item["href"])
        if not item.get("locked"):
            unique_items.append(item)

    if not unique_items:
        return

    # Собираем контент всех items (последовательно — Playwright page не потокобезопасна)
    print(f"   📄 {len(unique_items)} материалов, собираем контент...")
    item_contents = []
    for item in unique_items:
        ic = await _get_item_content(scraper, item, subject_name)
        item_contents.append(ic)

    # Check if ALL items are structure pages → skip entirely
    all_structure = all(ic.get("is_structure") for ic in item_contents)
    if all_structure and len(item_contents) > 0:
        print(f"   ⏭️  Пропускаем (все материалы — описание программы курса, нет контента)")
        return

    # Determine strategy with hybrid classification
    strategy, confidence = classify_lesson_strategy_with_confidence(section_name, item_contents)
    print(f"   🧠 Keyword стратегия: {strategy} (уверенность: {confidence}%)")

    # LLM fallback for uncertain cases
    if confidence < 70:
        item_titles = [ic["title"] for ic in item_contents]
        llm_strategy = classify_lesson_via_llm(section_name, item_titles, subject_name)
        if llm_strategy != strategy:
            print(f"   🧠 LLM переопределил стратегию: {strategy} → {llm_strategy}")
            strategy = llm_strategy
        else:
            print(f"   🧠 LLM подтвердил стратегию: {strategy}")

    if strategy == "skip":
        print(f"   ⏭️  Пропускаем (домашнее задание / контрольная / эссе / тест)")
        return

    if strategy == "merge_conspect":
        # Объединяем ВСЕ тексты в один, skipping structure pages
        parts = []
        for ic in item_contents:
            if ic.get("is_structure"):
                continue
            if ic["text"] and len(ic["text"]) > 50:
                parts.append(f"## {ic['title']}\n\n{ic['text']}")
        combined_text = "\n\n---\n\n".join(parts)

        if not combined_text or len(combined_text) < 300:
            print(f"   ⏭️  Пропускаем (нет полезного контента после фильтрации structure pages)")
            return

        folder, link = process_material(
            subject_name,
            section_name,
            section_name,
            combined_text,
            lesson_href=unique_items[0]["href"] if unique_items else "",
            force=force,
            category_override="конспект",
        )
        if link:
            conspect_links.add(link)
        return

    if strategy == "split_program":
        # "Рабочая программа": каждый item по своей категории
        for ic in item_contents:
            if ic.get("is_structure"):
                continue
            cat = classify_item(ic["title"], section_name)
            folder, link = process_material(
                subject_name,
                section_name,
                ic["title"],
                ic["text"],
                lesson_href=ic["href"],
                force=force,
                category_override=cat,
            )
            if link:
                if folder == "Конспекты":
                    conspect_links.add(link)
                elif folder == "Учебные материалы":
                    material_links.add(link)
                elif folder == "Информация по дисциплине":
                    info_links.add(link)
        return

    # strategy == "split" — каждый item отдельно по обычной классификации
    for ic in item_contents:
        if ic.get("is_structure"):
            print(f"   ⏭️  Пропускаем structure page: {ic['title']}")
            continue
        folder, link = process_material(
            subject_name, section_name, ic["title"], ic["text"], lesson_href=ic["href"], force=force
        )
        if link:
            if folder == "Конспекты":
                conspect_links.add(link)
            elif folder == "Учебные материалы":
                material_links.add(link)
            elif folder == "Информация по дисциплине":
                info_links.add(link)


async def _process_items_api(
    api_client,
    subject_name,
    section_name,
    items,
    conspect_links,
    material_links,
    info_links,
    seen_hrefs,
    force,
):
    """
    API-версия _process_items.
    Использует _get_item_content_api вместо _get_item_content.
    """
    # Deduplication href'ов
    unique_items = []
    for item in items:
        if item["href"] in seen_hrefs:
            continue
        seen_hrefs.add(item["href"])
        if not item.get("locked"):
            unique_items.append(item)

    if not unique_items:
        return

    # Собираем контент всех items
    print(f"   📄 {len(unique_items)} материалов, собираем контент...")
    item_contents = []
    for item in unique_items:
        ic = await _get_item_content_api(api_client, item, subject_name)
        item_contents.append(ic)

    # Check if ALL items are structure pages → skip entirely
    all_structure = all(ic.get("is_structure") for ic in item_contents)
    if all_structure and len(item_contents) > 0:
        print(f"   ⏭️  Пропускаем (все материалы — описание программы курса, нет контента)")
        return

    # Determine strategy with hybrid classification
    strategy, confidence = classify_lesson_strategy_with_confidence(section_name, item_contents)
    print(f"   🧠 Keyword стратегия: {strategy} (уверенность: {confidence}%)")

    # LLM fallback for uncertain cases
    if confidence < 70:
        item_titles = [ic["title"] for ic in item_contents]
        llm_strategy = classify_lesson_via_llm(section_name, item_titles, subject_name)
        if llm_strategy != strategy:
            print(f"   🧠 LLM переопределил стратегию: {strategy} → {llm_strategy}")
            strategy = llm_strategy
        else:
            print(f"   🧠 LLM подтвердил стратегию: {strategy}")

    if strategy == "skip":
        print(f"   ⏭️  Пропускаем (домашнее задание / контрольная / эссе / тест)")
        return

    if strategy == "merge_conspect":
        parts = []
        for ic in item_contents:
            if ic.get("is_structure"):
                continue
            if ic["text"] and len(ic["text"]) > 50:
                parts.append(f"## {ic['title']}\n\n{ic['text']}")
        combined_text = "\n\n---\n\n".join(parts)

        if not combined_text or len(combined_text) < 300:
            print(f"   ⏭️  Пропускаем (нет полезного контента после фильтрации structure pages)")
            return

        folder, link = process_material(
            subject_name,
            section_name,
            section_name,
            combined_text,
            lesson_href=unique_items[0]["href"] if unique_items else "",
            force=force,
            category_override="конспект",
        )
        if link:
            conspect_links.add(link)
        return

    if strategy == "split_program":
        for ic in item_contents:
            if ic.get("is_structure"):
                continue
            cat = classify_item(ic["title"], section_name)
            folder, link = process_material(
                subject_name,
                section_name,
                ic["title"],
                ic["text"],
                lesson_href=ic["href"],
                force=force,
                category_override=cat,
            )
            if link:
                if folder == "Конспекты":
                    conspect_links.add(link)
                elif folder == "Учебные материалы":
                    material_links.add(link)
                elif folder == "Информация по дисциплине":
                    info_links.add(link)
        return

    # strategy == "split"
    for ic in item_contents:
        if ic.get("is_structure"):
            print(f"   ⏭️  Пропускаем structure page: {ic['title']}")
            continue
        folder, link = process_material(
            subject_name, section_name, ic["title"], ic["text"], lesson_href=ic["href"], force=force
        )
        if link:
            if folder == "Конспекты":
                conspect_links.add(link)
            elif folder == "Учебные материалы":
                material_links.add(link)
            elif folder == "Информация по дисциплине":
                info_links.add(link)


if __name__ == "__main__":
    asyncio.run(main())
