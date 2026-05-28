#!/usr/bin/env python3
"""
Быстрый исследовательский скрипт: собирает структуру без slow video extraction.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary", "summary_programs"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv

load_dotenv()


async def main():
    program_id = sys.argv[1] if len(sys.argv) > 1 else "bhebfad-25-memeo-2"

    scraper = NetologyScraper(headless=True)
    await scraper.start()

    login_ok = await ensure_netology_login(scraper.page, program_id)
    if not login_ok:
        print("❌ Авторизация не удалась")
        await scraper.stop()
        sys.exit(1)

    # Собираем дисциплины
    print("=" * 60)
    print(f"🔍 Программа: {program_id}")
    print("=" * 60)
    program_title, disciplines = await scraper.get_program_disciplines(program_id)
    print(f"📚 Всего разделов: {len(disciplines)}")

    # Исследуем КАЖДЫЙ раздел (несколько первых items)
    results = []
    for disc in disciplines:
        disc_title = disc["title"]
        if disc.get("locked"):
            results.append({"title": disc_title, "locked": True})
            continue

        lessons = await scraper.get_discipline_lessons(
            program_id, disc["lesson_id"], disc.get("links", [])
        )
        items_info = []
        for item in lessons[:5]:  # max 5 items per lesson
            # Только get_lesson_text_content — без extract_video_url
            text, _ = await scraper.get_lesson_text_content(item["href"])
            items_info.append(
                {
                    "title": item["title"],
                    "href": item["href"],
                    "text_length": len(text) if text else 0,
                    "text_preview": (text[:200] + "...") if text and len(text) > 200 else text,
                }
            )

        results.append(
            {
                "title": disc_title,
                "lesson_id": disc.get("lesson_id"),
                "item_count": len(lessons),
                "items": items_info,
            }
        )

    # Сохраняем
    output_path = f"Данные/program_structure_fast_{program_id}.json"
    os.makedirs("Данные", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"program_id": program_id, "disciplines": results}, f, ensure_ascii=False, indent=2
        )
    print(f"\n💾 Сохранено: {output_path}")

    # Вывод анализа
    print("\n" + "=" * 60)
    print("📊 Анализ")
    print("=" * 60)
    for r in results:
        if r.get("locked"):
            print(f"🔒 {r['title']}")
            continue
        videos = sum(1 for it in r["items"] if it["text_length"] < 1000 and it["text_length"] > 0)
        files = sum(1 for it in r["items"] if it["text_length"] > 1000)
        print(f"\n📂 {r['title']} ({r['item_count']} items)")
        for it in r["items"]:
            t = it["text_length"]
            icon = "📄" if t > 1000 else ("🎬?" if t > 0 else "❓")
            print(f"  {icon} {it['title']} — {t} симв.")
            if t > 0 and t < 2000:
                print(f"      Preview: {it['text_preview'][:120]}")

    await scraper.save_cookies()
    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
