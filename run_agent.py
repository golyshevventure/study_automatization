import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Утилиты"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv
from generate_summary import generate_summary
from second_brain_cleanup import remove_old_structure, ensure_new_structure, ensure_subject_dirs
from material_classifier import (
    classify_material,
    category_folder,
    should_skip,
    classify_lesson_strategy,
    classify_item,
)
from subject_index import update_subject_index, reset_subject_index
from conspect_writer import write_material, write_large_file_stub, wiki_link
from audio_extractor import extract_audio_from_mp4
from local_whisper import transcribe_to_text

load_dotenv()

SECONDBRAIN = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain"
STUDY_DIR = os.path.join(SECONDBRAIN, "Учеба (Фин. Ун.)")


def safe_filename(name, max_len=80):
    name = re.sub(r'[\\/:"*?<>|]', '', name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(' ', 1)[0]
    return name


def _file_exists(subject_name, section_name, lesson_title):
    """Проверяет, существует ли уже файл для этого материала."""
    display_title = f"{section_name} — {lesson_title}" if lesson_title.lower() not in section_name.lower() else section_name
    category = classify_material(lesson_title, section_name)
    folder_name = category_folder(category)
    safe_title = re.sub(r'[\\/:"*?<>|]', '', display_title).strip()
    if len(safe_title) > 80:
        safe_title = safe_title[:80].rsplit(' ', 1)[0]
    safe_subject = re.sub(r'[\\/:"*?<>|]', '', subject_name).strip()
    if len(safe_subject) > 80:
        safe_subject = safe_subject[:80].rsplit(' ', 1)[0]
    filepath = os.path.join(STUDY_DIR, "Дисциплины", safe_subject, folder_name, f"{safe_title}.md")
    return os.path.exists(filepath)


def process_material(subject_name, section_name, lesson_title, lesson_text, lesson_href="", force=False, category_override=None):
    """
    Обрабатывает один материал: классифицирует, генерирует конспект или заглушку, сохраняет.
    category_override: если задан, использует эту категорию вместо авто-классификации.
    """
    display_title = f"{section_name} — {lesson_title}" if lesson_title.lower() not in section_name.lower() else section_name

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
    safe_title = re.sub(r'[\\/:"*?<>|]', '', display_title).strip()
    if len(safe_title) > 80:
        safe_title = safe_title[:80].rsplit(' ', 1)[0]
    safe_subject = re.sub(r'[\\/:"*?<>|]', '', subject_name).strip()
    if len(safe_subject) > 80:
        safe_subject = safe_subject[:80].rsplit(' ', 1)[0]
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


async def _get_item_content(scraper, item, subject_name):
    """
    Получает контент одного item.
    Возвращает dict с text, video_url, title, href.
    Если есть видео — извлекает и транскрибирует аудио.
    """
    text, video_url = await scraper.get_lesson_text_content(item["href"])

    # Audio fallback: если есть видео — ВСЕГДА транскрибируем
    if video_url:
        print(f"   🎬 Найдено видео ({item['title']}), извлекаем аудио...")
        try:
            audio_path = extract_audio_from_mp4(
                video_url, output_dir=f"data/audio/{safe_filename(subject_name)}"
            )
            print(f"   🎙️  Транскрибируем аудио...")
            transcript = transcribe_to_text(audio_path)
            if transcript and len(transcript) > 500:
                text = f"[Транскрипция вебинара]\n\n{transcript}"
                print(f"   ✅ Транскрипция: {len(transcript)} символов")
            else:
                print(f"   ⚠️ Транскрипция слишком короткая, используем HTML fallback")
        except Exception as e:
            print(f"   ⚠️ Ошибка аудио: {e}")

    return {
        "title": item["title"],
        "href": item["href"],
        "text": text,
        "video_url": video_url,
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
        print("  python run_agent.py <program_id> --subject 'Название'  — только разделы с этим словом")
        sys.exit(1)

    program_id = sys.argv[1]
    target_subject = None
    force = "--force" in sys.argv
    if "--subject" in sys.argv:
        idx = sys.argv.index("--subject")
        target_subject = sys.argv[idx + 1]

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
        print("=" * 60)
        print("🔍 Сбор структуры...")
        print("=" * 60)

        program_title, disciplines = await scraper.get_program_disciplines(program_id)

        # Определяем subject_name
        if target_subject and disciplines:
            filtered = [d for d in disciplines if target_subject.lower() in d.get("title", "").lower()]
            if filtered:
                subject_name = filtered[0]["title"]
            else:
                subject_name = program_title or target_subject
        else:
            subject_name = program_title or (disciplines[0]["title"] if disciplines else "Предмет")

        print(f"\n📚 Предмет: {subject_name}")
        print(f"   Разделов: {len(disciplines)}")

        if target_subject:
            print(f"   🔍 Фильтр: только разделы содержащие '{target_subject}'")

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

            if target_subject and target_subject.lower() not in disc_title.lower():
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
                        scraper, subject_name, section_name, items,
                        conspect_links, material_links, info_links,
                        seen_hrefs, force
                    )
            else:
                # Legacy структура: disc = lesson, items внутри
                section_name = disc_title
                items = await _collect_lesson_items(
                    scraper, program_id, disc["lesson_id"], disc.get("links", []), section_name
                )
                await _process_items(
                    scraper, subject_name, section_name, items,
                    conspect_links, material_links, info_links,
                    seen_hrefs, force
                )

            print(f"   ✅ Раздел завершён")
            await asyncio.sleep(1)

        # Обновляем файл предмета
        update_subject_index(subject_name, conspect_links, material_links, info_links)

        await scraper.save_cookies()
        print("\n" + "=" * 60)
        print("🏁 Всё готово!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n🛑 Остановлено пользователем")
    finally:
        try:
            await scraper.save_cookies()
        except Exception:
            pass
        await scraper.stop()


async def _process_items(
    scraper, subject_name, section_name, items,
    conspect_links, material_links, info_links,
    seen_hrefs, force
):
    """
    Обрабатывает items одного lesson.
    Определяет стратегию (merge/split), выполняет audio fallback, сохраняет.
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

    # Определяем стратегию
    strategy = classify_lesson_strategy(section_name, item_contents)
    print(f"   🧠 Стратегия: {strategy}")

    if strategy == "skip":
        print(f"   ⏭️  Пропускаем (домашнее задание / контрольная / эссе)")
        return

    if strategy == "merge_conspect":
        # Объединяем ВСЕ тексты в один
        parts = []
        for ic in item_contents:
            if ic["text"] and len(ic["text"]) > 50:
                parts.append(f"## {ic['title']}\n\n{ic['text']}")
        combined_text = "\n\n---\n\n".join(parts)

        folder, link = process_material(
            subject_name, section_name, section_name,
            combined_text,
            lesson_href=unique_items[0]["href"] if unique_items else "",
            force=force,
            category_override="конспект"
        )
        if link:
            conspect_links.add(link)
        return

    if strategy == "split_program":
        # "Рабочая программа": каждый item по своей категории
        for ic in item_contents:
            cat = classify_item(ic["title"], section_name)
            folder, link = process_material(
                subject_name, section_name, ic["title"],
                ic["text"],
                lesson_href=ic["href"],
                force=force,
                category_override=cat
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
        folder, link = process_material(
            subject_name, section_name, ic["title"],
            ic["text"],
            lesson_href=ic["href"],
            force=force
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
