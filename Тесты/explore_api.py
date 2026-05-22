"""
Исследование API Нетологии.
Перехватывает все сетевые запросы при навигации по ЛК.
Сохраняет результат в Данные/api_explore.json для анализа.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login

OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "Данные", "api_explore.json"
)

# Список URL для исследования
URLS_TO_EXPLORE = [
    "https://netology.ru/profile",
    "https://netology.ru/profile/program/bhebfad-25/schedule",
    "https://netology.ru/profile/program/bhebfad-25-memeo-2/schedule",
    "https://netology.ru/profile/program/bhebfad-25-memeo-2/lessons/617943",
]


def classify_content_type(headers, url):
    """Классифицирует тип контента по заголовкам и URL."""
    ct = headers.get("content-type", "").lower()
    if "json" in ct:
        return "json"
    if "html" in ct:
        return "html"
    if "javascript" in ct or "js" in ct:
        return "js"
    if "css" in ct:
        return "css"
    if "image" in ct:
        return "image"
    if "vtt" in url.lower():
        return "vtt"
    if "mp4" in url.lower() or "m3u8" in url.lower():
        return "video"
    if "pdf" in url.lower():
        return "pdf"
    return "other"


async def main():
    scraper = NetologyScraper(headless=True)
    await scraper.start()

    # Хранилище перехваченных запросов
    captured = []
    api_candidates = []

    async def handle_route(route, request):
        url = request.url
        method = request.method
        headers = request.headers
        resource_type = request.resource_type

        # Пропускаем статику
        parsed = urlparse(url)
        path = parsed.path
        host = parsed.netloc

        is_static = any(
            ext in path.lower()
            for ext in [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf"]
        )

        if not is_static:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "url": url,
                "host": host,
                "path": path,
                "resource_type": resource_type,
                "headers": dict(headers),
            }
            captured.append(entry)

            # Определяем API-кандидатов
            if resource_type in ["xhr", "fetch"]:
                api_candidates.append(entry)
            elif "json" in (headers.get("content-type", "")).lower():
                api_candidates.append(entry)
            elif "/api/" in path.lower():
                api_candidates.append(entry)

        await route.continue_()

    # Включаем перехват всех запросов
    await scraper.page.route("**/*", handle_route)

    # Авторизация
    login_ok = await ensure_netology_login(scraper.page, "bhebfad-25")
    if not login_ok:
        print("❌ Не удалось авторизоваться")
        await scraper.stop()
        return

    print("✅ Авторизация пройдена. Начинаем исследование...")

    # Переходим по URL и собираем запросы
    for url in URLS_TO_EXPLORE:
        print(f"\n🌐 Переходим: {url}")
        before_count = len(captured)

        try:
            await scraper.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"   ⚠️ Ошибка перехода: {e}")

        after_count = len(captured)
        new_requests = after_count - before_count
        print(f"   📡 Новых запросов: {new_requests}")

    # Анализируем результаты
    print("\n" + "=" * 60)
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    # Группируем по хосту
    hosts = {}
    for req in captured:
        host = req["host"]
        hosts.setdefault(host, []).append(req)

    print(f"\nВсего перехвачено запросов: {len(captured)}")
    print(f"API-кандидатов (XHR/Fetch/JSON/API): {len(api_candidates)}")
    print(f"\nУникальных хостов: {len(hosts)}")

    for host, reqs in sorted(hosts.items(), key=lambda x: -len(x[1])):
        print(f"\n  📍 {host}: {len(reqs)} запросов")

        # Показываем пути
        paths = {}
        for r in reqs:
            p = r["path"]
            paths[p] = paths.get(p, 0) + 1

        for path, count in sorted(paths.items(), key=lambda x: -x[1])[:10]:
            marker = " 🎯" if "/api/" in path.lower() else ""
            print(f"     {path} ({count}x){marker}")

    # Сохраняем результаты
    result = {
        "explored_at": datetime.now().isoformat(),
        "urls_explored": URLS_TO_EXPLORE,
        "total_requests": len(captured),
        "api_candidates_count": len(api_candidates),
        "hosts": {host: len(reqs) for host, reqs in hosts.items()},
        "api_candidates": api_candidates,
        "all_requests": captured,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Результаты сохранены: {OUTPUT_FILE}")
    print(f"   Всего запросов: {len(captured)}")
    print(f"   API-кандидатов: {len(api_candidates)}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
