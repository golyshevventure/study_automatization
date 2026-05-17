#!/usr/bin/env python3
"""
Исследовательский скрипт: собирает полную структуру программы Нетологии.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv

load_dotenv()


async def explore_program(scraper, program_id, depth=0, max_lessons_per_module=5, max_items_per_lesson=20):
    """
    Рекурсивно обходит программу/модуль.
    Возвращает структуру: {title, program_id, lessons: [...]}
    """
    indent = "  " * depth
    print(f"{indent}🔍 Программа/модуль: {program_id}")

    # Собираем дисциплины/модули
    program_title, disciplines = await scraper.get_program_disciplines(program_id)
    if not disciplines:
        print(f"{indent}  ⚠️ Нет дисциплин")
        return {"program_id": program_id, "title": program_title, "modules": []}

    modules = []
    for disc in disciplines[:20]:  # ограничим для скорости
        disc_title = disc["title"]
        print(f"{indent}  📂 {disc_title}")

        if disc.get("locked"):
            modules.append({
                "title": disc_title,
                "locked": True,
                "lessons": []
            })
            continue

        # Новая структура: module program_id
        if "program_id" in disc and disc["program_id"]:
            module_lessons = await scraper.get_module_lessons(disc["program_id"])
            lessons = []
            for ml in module_lessons[:max_lessons_per_module]:
                if ml.get("locked"):
                    lessons.append({"title": ml.get("title"), "locked": True, "items": []})
                    continue
                items = await scraper.get_discipline_lessons(disc["program_id"], ml["lesson_id"], [])
                # Для каждого item определяем тип
                items_enriched = []
                for item in items[:max_items_per_lesson]:
                    item_info = {
                        "title": item["title"],
                        "href": item["href"],
                        "locked": item.get("locked", False),
                    }
                    # Проверяем VTT, видео, файлы
                    text, _ = await scraper.get_lesson_text_content(item["href"])
                    item_info["text_length"] = len(text) if text else 0

                    video_url = await scraper.extract_video_url(item["href"])
                    item_info["has_video"] = bool(video_url)
                    item_info["video_url_preview"] = video_url[:60] + "..." if video_url else None

                    items_enriched.append(item_info)

                lessons.append({
                    "title": ml.get("title"),
                    "lesson_id": ml["lesson_id"],
                    "locked": False,
                    "items": items_enriched
                })

            modules.append({
                "title": disc_title,
                "program_id": disc.get("program_id"),
                "locked": False,
                "lessons": lessons
            })
        else:
            # Legacy структура
            items = await scraper.get_discipline_lessons(program_id, disc["lesson_id"], disc.get("links", []))
            items_enriched = []
            for item in items[:max_items_per_lesson]:
                item_info = {
                    "title": item["title"],
                    "href": item["href"],
                    "locked": item.get("locked", False),
                }
                text, _ = await scraper.get_lesson_text_content(item["href"])
                item_info["text_length"] = len(text) if text else 0
                video_url = await scraper.extract_video_url(item["href"])
                item_info["has_video"] = bool(video_url)
                item_info["video_url_preview"] = video_url[:60] + "..." if video_url else None
                items_enriched.append(item_info)

            modules.append({
                "title": disc_title,
                "lesson_id": disc.get("lesson_id"),
                "locked": False,
                "lessons": [{"title": disc_title, "items": items_enriched}]
            })

    return {
        "program_id": program_id,
        "title": program_title,
        "modules": modules
    }


async def explore_profile(scraper):
    """Собирает все программы со страницы профиля."""
    url = "https://netology.ru/profile"
    print(f"🌐 {url}")
    ok = await scraper._safe_goto(url, wait_until="domcontentloaded", timeout=60000)
    if not ok:
        print("⚠️ Профиль не загрузился")
        return []

    await asyncio.sleep(3)

    programs = await scraper.page.evaluate("""
    () => {
        const results = [];
        const seen = new Set();
        // Карточки программ
        document.querySelectorAll('a[href*="/profile/program/"]').forEach(a => {
            const href = a.getAttribute('href');
            const m = href.match(/program\/([^\\/?#]+)/);
            if (!m) return;
            const pid = m[1];
            if (seen.has(pid)) return;
            seen.add(pid);
            let title = '';
            const h = a.querySelector('h3, h2, h1, [class*="title"], [class*="name"]');
            if (h) title = h.textContent.trim();
            if (!title) title = a.textContent.trim().split('\\n')[0].trim();
            results.push({title, program_id: pid, href});
        });
        return results;
    }
    """)

    print(f"📚 Найдено программ: {len(programs)}")
    for p in programs:
        print(f"  {p['title']} ({p['program_id']})")
    return programs


async def main():
    program_id = sys.argv[1] if len(sys.argv) > 1 else "bhebfad-25-memeo-2"

    scraper = NetologyScraper(headless=True)
    await scraper.start()

    login_ok = await ensure_netology_login(scraper.page, program_id)
    if not login_ok:
        print("❌ Авторизация не удалась")
        await scraper.stop()
        sys.exit(1)

    # 1. Собираем программы профиля
    print("\n" + "=" * 60)
    print("🔍 Исследование профиля")
    print("=" * 60)
    programs = await explore_profile(scraper)

    # 2. Глубокое исследование выбранной программы
    print("\n" + "=" * 60)
    print(f"🔍 Глубокое исследование: {program_id}")
    print("=" * 60)
    structure = await explore_program(scraper, program_id, depth=0, max_lessons_per_module=10, max_items_per_lesson=20)

    # 3. Сохраняем
    output_path = f"Данные/program_structure_{program_id}.json"
    os.makedirs("Данные", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Структура сохранена: {output_path}")

    # 4. Анализ
    print("\n" + "=" * 60)
    print("📊 Анализ структуры")
    print("=" * 60)

    total_modules = len(structure["modules"])
    total_lessons = sum(len(m["lessons"]) for m in structure["modules"])
    total_items = sum(
        len(item)
        for m in structure["modules"]
        for l in m["lessons"]
        for item in [l["items"]]
    )
    video_items = sum(
        1
        for m in structure["modules"]
        for l in m["lessons"]
        for item in l["items"]
        if item.get("has_video")
    )
    short_text_items = sum(
        1
        for m in structure["modules"]
        for l in m["lessons"]
        for item in l["items"]
        if item.get("text_length", 0) < 1000 and item.get("text_length", 0) > 0
    )

    print(f"  Модулей: {total_modules}")
    print(f"  Занятий: {total_lessons}")
    print(f"  Материалов: {total_items}")
    print(f"  С видео: {video_items}")
    print(f"  С коротким текстом (<1000): {short_text_items}")

    # Примеры разделов с видео
    print("\n  📹 Разделы с видео:")
    for m in structure["modules"]:
        for l in m["lessons"]:
            video_count = sum(1 for item in l["items"] if item.get("has_video"))
            if video_count > 0:
                print(f"    {m['title']} / {l['title']}: {video_count} видео из {len(l['items'])}")
                for item in l["items"]:
                    flag = "🎬" if item.get("has_video") else "📄"
                    print(f"      {flag} {item['title']} (text: {item['text_length']})")

    await scraper.save_cookies()
    await scraper.stop()
    print("\n✅ Исследование завершено")


if __name__ == "__main__":
    asyncio.run(main())
