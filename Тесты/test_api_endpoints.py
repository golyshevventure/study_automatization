"""
Тестирование найденных API endpoint'ов Нетологии.
Берёт cookies из data/netology_cookies.json и делает HTTP-запросы.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))
from logger_config import get_logger

logger = get_logger("test_api")

COOKIES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "netology_cookies.json"
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "Данные")

# Найденные endpoint'ы для тестирования
ENDPOINTS = [
    ("GET", "https://netology.ru/backend/api/user/programs/bhebfad-25"),
    ("GET", "https://netology.ru/backend/api/user/programs/bhebfad-25-memeo-2"),
    ("GET", "https://netology.ru/backend/api/user/programs/59690/menu"),
    ("GET", "https://netology.ru/backend/api/user/programs/59690/schedule"),
    ("GET", "https://netology.ru/backend/api/user/programs/59690/diploma"),
    ("GET", "https://netology.ru/backend/api/user/professions/59690/schedule"),
    ("GET", "https://netology.ru/backend/api/user/student_learning/actual"),
    ("GET", "https://netology.ru/backend/api/user/student_learning/calendar"),
    ("GET", "https://netology.ru/backend/api/user/last_opened_lesson_items_info"),
    ("GET", "https://netology.ru/backend/api/user/programs/progress"),
    ("GET", "https://netology.ru/backend/api/user/profile"),
    ("GET", "https://netology.ru/backend/api/user/favorite_programs"),
    ("GET", "https://netology.ru/backend/api/user/notifications/unread_messages"),
    ("GET", "https://netology.ru/backend/api/app_options"),
    ("GET", "https://netology.ru/backend/api/directions"),
]


def cookies_to_headers(cookies_file):
    """Преобразует Playwright cookies в HTTP заголовки."""
    with open(cookies_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    return {
        "Cookie": cookie_str,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://netology.ru/profile",
    }


async def test_endpoint(client, method, url, headers):
    """Тестирует один endpoint."""
    result = {
        "method": method,
        "url": url,
        "status": None,
        "content_type": None,
        "is_json": False,
        "size": 0,
        "error": None,
        "preview": None,
    }

    try:
        response = await client.request(method, url, headers=headers, timeout=30)
        result["status"] = response.status_code
        result["content_type"] = response.headers.get("content-type", "")
        result["size"] = len(response.content)

        ct = result["content_type"].lower()
        if "json" in ct:
            result["is_json"] = True
            try:
                data = response.json()
                # Сохраняем JSON для анализа
                filename = (
                    url.replace("https://", "").replace("/", "_").replace(".", "_")
                    + ".json"
                )
                filepath = os.path.join(OUTPUT_DIR, f"api_{filename}")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                result["preview"] = _preview_json(data)
            except Exception as e:
                result["error"] = f"JSON parse error: {e}"
        else:
            # Сохраняем первые 500 байт для анализа
            result["preview"] = response.text[:500]

    except Exception as e:
        result["error"] = str(e)

    return result


def _preview_json(data, max_depth=2):
    """Создаёт краткое описание JSON структуры."""
    if isinstance(data, dict):
        keys = list(data.keys())
        return f"dict: {len(keys)} keys — {keys[:10]}"
    elif isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            keys = list(data[0].keys())
            return f"list: {len(data)} items, first has keys: {keys[:10]}"
        return f"list: {len(data)} items"
    else:
        return f"value: {type(data).__name__}"


async def main():
    if not os.path.exists(COOKIES_FILE):
        print(f"❌ Cookies не найдены: {COOKIES_FILE}")
        return

    headers = cookies_to_headers(COOKIES_FILE)
    results = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for method, url in ENDPOINTS:
            print(f"\n🌐 {method} {url}")
            result = await test_endpoint(client, method, url, headers)
            results.append(result)

            status = result["status"]
            is_json = result["is_json"]
            size = result["size"]
            error = result["error"]
            preview = result["preview"]

            if error and status is None:
                print(f"   ❌ Ошибка: {error}")
            elif status == 200 and is_json:
                print(f"   ✅ {status} | JSON | {size} bytes | {preview}")
            elif status == 200:
                print(f"   ⚠️ {status} | Не JSON ({result['content_type']}) | {size} bytes")
            else:
                print(f"   ⚠️ {status} | {size} bytes | {error or preview}")

    # Сохраняем отчёт
    report = {
        "tested_at": datetime.now().isoformat(),
        "total_endpoints": len(ENDPOINTS),
        "successful_json": len([r for r in results if r["status"] == 200 and r["is_json"]]),
        "successful_other": len([r for r in results if r["status"] == 200 and not r["is_json"]]),
        "failed": len([r for r in results if r["status"] != 200 or r["error"]]),
        "results": results,
    }

    report_file = os.path.join(OUTPUT_DIR, "api_test_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 60)
    print(f"Всего endpoint'ов: {report['total_endpoints']}")
    print(f"✅ JSON (200): {report['successful_json']}")
    print(f"⚠️  Другой ответ (200): {report['successful_other']}")
    print(f"❌ Ошибки: {report['failed']}")
    print(f"\n💾 Отчёт сохранён: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
