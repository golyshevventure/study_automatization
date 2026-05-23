"""
Тестовый скрипт API-first подхода.
Цель: проверить формат ответов API Нетологии.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))

import httpx
from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv

load_dotenv()

COOKIES_FILE = "data/netology_cookies.json"
API_BASE = "https://netology.ru/backend/api/user"

# Тестовая программа: Мировая экономика
TEST_PROGRAM_ID = "bhebfad-25-memeo-2"
TEST_PROGRAM_NUMERIC_ID = 69757


def load_cookies_for_httpx(cookies_file):
    if not os.path.exists(cookies_file):
        return {}
    with open(cookies_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    # httpx ожидает dict name -> value
    return {c["name"]: c["value"] for c in cookies}


async def test_api_with_cookies():
    cookies = load_cookies_for_httpx(COOKIES_FILE)
    if not cookies:
        print("❌ Cookies не найдены")
        return False

    async with httpx.AsyncClient(cookies=cookies, follow_redirects=True) as client:
        # 1. Проверяем профиль (самый простой endpoint)
        print("=== 1. GET /user/profile ===")
        r = await client.get(f"{API_BASE}/profile")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Email: {data.get('email')}")
            print(f"   Name: {data.get('full_name')}")
        elif r.status_code == 401:
            print("   ❌ 401 Unauthorized — cookies протухли")
            return False
        else:
            print(f"   Body: {r.text[:200]}")

        # 2. Schedule программы (по slug)
        print(f"\n=== 2. GET /programs/{TEST_PROGRAM_ID}/schedule ===")
        r = await client.get(f"{API_BASE}/programs/{TEST_PROGRAM_ID}/schedule")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            lessons = data.get("lessons", [])
            print(f"   Lessons: {len(lessons)}")
            if lessons:
                first = lessons[0]
                print(f"   First lesson: {first.get('title')} (id={first.get('id')})")
                items = first.get("lesson_items", [])
                print(f"   Items in first lesson: {len(items)}")
                if items:
                    for i, it in enumerate(items[:3]):
                        print(f"      [{i}] {it.get('title')} | type={it.get('type')} | video_url={it.get('video_url') is not None}")
            # Сохраняем для анализа
            with open("Данные/api_test_schedule_live.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("   💾 Сохранено: Данные/api_test_schedule_live.json")
        else:
            print(f"   Body: {r.text[:300]}")
            return False

        # 3. Schedule по numeric ID
        print(f"\n=== 3. GET /programs/{TEST_PROGRAM_NUMERIC_ID}/schedule ===")
        r = await client.get(f"{API_BASE}/programs/{TEST_PROGRAM_NUMERIC_ID}/schedule")
        print(f"   Status: {r.status_code}")

        # 4. Lesson item content
        # Найдём первый text-item
        text_item_id = None
        video_item_id = None
        attachment_item_id = None
        for lesson in data.get("lessons", []):
            for item in lesson.get("lesson_items", []):
                if text_item_id is None and item.get("type") == "text":
                    text_item_id = item["id"]
                if video_item_id is None and item.get("type") == "webinar":
                    video_item_id = item["id"]
                if attachment_item_id is None and item.get("type") == "attachment":
                    attachment_item_id = item["id"]

        if text_item_id:
            print(f"\n=== 4a. GET /lesson_items/{text_item_id} (type=text) ===")
            r = await client.get(f"{API_BASE}/lesson_items/{text_item_id}")
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data_item = r.json()
                print(f"   Keys: {list(data_item.keys())}")
                print(f"   Title: {data_item.get('title')}")
                print(f"   Type: {data_item.get('type')}")
                print(f"   Content_type: {data_item.get('content_type')}")
                content = data_item.get("content", "")
                print(f"   Content length: {len(content)}")
                print(f"   Content preview: {content[:500]}")
                print(f"   Video_url: {data_item.get('video_url')}")
                print(f"   Webinar_url: {data_item.get('webinar_url')}")
                print(f"   Youtube_id: {data_item.get('youtube_video_id')}")
                with open(f"Данные/api_test_item_{text_item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(data_item, f, ensure_ascii=False, indent=2)
                print(f"   💾 Сохранено: Данные/api_test_item_{text_item_id}.json")

        if video_item_id:
            print(f"\n=== 4b. GET /lesson_items/{video_item_id} (type=webinar) ===")
            r = await client.get(f"{API_BASE}/lesson_items/{video_item_id}")
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data_item = r.json()
                print(f"   Keys: {list(data_item.keys())}")
                print(f"   Title: {data_item.get('title')}")
                print(f"   Type: {data_item.get('type')}")
                print(f"   Video_url: {data_item.get('video_url')}")
                print(f"   Content length: {len(data_item.get('content', ''))}")
                with open(f"Данные/api_test_item_{video_item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(data_item, f, ensure_ascii=False, indent=2)
                print(f"   💾 Сохранено: Данные/api_test_item_{video_item_id}.json")

        if attachment_item_id:
            print(f"\n=== 4c. GET /lesson_items/{attachment_item_id} (type=attachment) ===")
            r = await client.get(f"{API_BASE}/lesson_items/{attachment_item_id}")
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data_item = r.json()
                print(f"   Keys: {list(data_item.keys())}")
                print(f"   Title: {data_item.get('title')}")
                print(f"   Type: {data_item.get('type')}")
                print(f"   Content_type: {data_item.get('content_type')}")
                content = data_item.get("content", "")
                print(f"   Content length: {len(content)}")
                print(f"   Content preview: {content[:500]}")
                with open(f"Данные/api_test_item_{attachment_item_id}.json", "w", encoding="utf-8") as f:
                    json.dump(data_item, f, ensure_ascii=False, indent=2)
                print(f"   💾 Сохранено: Данные/api_test_item_{attachment_item_id}.json")

    return True


async def main():
    print("🔬 Тест API-first подхода\n")
    ok = await test_api_with_cookies()
    if not ok:
        print("\n❌ Cookies протухли. Запускаем авторизацию через Playwright...")
        scraper = NetologyScraper(headless=True)
        await scraper.start()
        login_ok = await ensure_netology_login(scraper.page, TEST_PROGRAM_ID)
        if login_ok:
            await scraper.save_cookies()
            print("✅ Cookies обновлены. Повторяем API-запрос...")
            await scraper.stop()
            ok = await test_api_with_cookies()
        else:
            print("❌ Авторизация не удалась")
            await scraper.stop()

    if ok:
        print("\n✅ Все API-запросы успешны. Данные сохранены в Данные/")
    else:
        print("\n❌ Не удалось выполнить API-запросы")


if __name__ == "__main__":
    asyncio.run(main())
