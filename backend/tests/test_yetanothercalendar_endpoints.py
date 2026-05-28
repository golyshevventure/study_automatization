"""Исследование endpoint'ов Netology из проекта YetAnotherCalendar.

Тестируемые endpoint'ы:
1. POST /backend/api/user/sign_in — авторизация
2. GET /backend/api/user/programs/calendar/filters — список курсов
3. GET /backend/api/user/professions/{calendar_id}/schedule — программы профессии
4. GET /backend/api/user/programs/{program_id}/schedule — события программы

Результаты сохраняются в /backend/api_tests_etc/test_endpoints/
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Загружаем .env
load_dotenv(Path(__file__).parent.parent.parent / ".env")

NETOLOGY_EMAIL = os.getenv("NETOLOGY_EMAIL")
NETOLOGY_PASSWORD = os.getenv("NETOLOGY_PASSWORD")
BASE_URL = "https://netology.ru"
OUTPUT_DIR = Path(__file__).parent.parent / "api_tests_etc" / "test_endpoints"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(name: str, data: dict | list) -> Path:
    """Сохранить JSON с timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{name}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Сохранено: {path.name} ({len(json.dumps(data))} bytes)")
    return path


def test_sign_in() -> httpx.Cookies | None:
    """Тест 1: Авторизация через POST /backend/api/user/sign_in"""
    print("\n" + "=" * 60)
    print("ТЕСТ 1: POST /backend/api/user/sign_in")
    print("=" * 60)

    url = f"{BASE_URL}/backend/api/user/sign_in"
    data = {
        "login": NETOLOGY_EMAIL,
        "password": NETOLOGY_PASSWORD,
        "remember": "1",
    }

    print(f"  URL: {url}")
    print(f"  Data: login={NETOLOGY_EMAIL}, remember=1")

    try:
        response = httpx.post(url, data=data, timeout=15, follow_redirects=True)
        print(f"  Status: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        print(f"  Cookies: {dict(response.cookies)}")

        result = {
            "endpoint": "POST /backend/api/user/sign_in",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies_raw": {k: v for k, v in response.cookies.items()},
            "body_preview": response.text[:2000] if response.text else None,
            "timestamp": datetime.now().isoformat(),
        }
        save_json("sign_in_response", result)

        if response.status_code == 200:
            print("  ✅ Успешная авторизация")
            if response.cookies:
                print(f"  🍪 Получены cookies: {list(response.cookies.keys())}")
                return response.cookies
            else:
                print("  ⚠️ Cookies не получены, но статус 200")
                # Проверим Set-Cookie в headers
                set_cookie = response.headers.get("set-cookie")
                if set_cookie:
                    print(f"  🍪 Set-Cookie в headers: {set_cookie[:200]}...")
        elif response.status_code == 401:
            print("  ❌ 401 Unauthorized — неверный логин/пароль")
        else:
            print(f"  ⚠️ Неожиданный статус: {response.status_code}")
            print(f"  Body: {response.text[:500]}")

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        result = {
            "endpoint": "POST /backend/api/user/sign_in",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        save_json("sign_in_error", result)

    return None


def test_get_courses(cookies: httpx.Cookies) -> list[dict] | None:
    """Тест 2: GET /backend/api/user/programs/calendar/filters — список курсов"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: GET /backend/api/user/programs/calendar/filters")
    print("=" * 60)

    url = f"{BASE_URL}/backend/api/user/programs/calendar/filters"
    print(f"  URL: {url}")

    try:
        client = httpx.Client(cookies=cookies, timeout=15)
        response = client.get(url)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Content-Length: {len(response.content)} bytes")

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_text": response.text[:2000]}

        result = {
            "endpoint": "GET /backend/api/user/programs/calendar/filters",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        save_json("calendar_filters", result)

        if response.status_code == 200:
            print("  ✅ Успешно")
            if isinstance(data, dict):
                programs = data.get("programs", [])
                print(f"  📚 Найдено программ: {len(programs)}")
                for p in programs[:5]:
                    print(f"    - {p.get('title', 'N/A')} (id={p.get('id', 'N/A')}, type={p.get('type', 'N/A')})")
                if len(programs) > 5:
                    print(f"    ... и ещё {len(programs) - 5}")
                return programs
        else:
            print(f"  ⚠️ Статус {response.status_code}")
            print(f"  Body: {response.text[:500]}")

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

    return None


def test_profession_schedule(cookies: httpx.Cookies, program_id: int) -> list[dict] | None:
    """Тест 3: GET /backend/api/user/professions/{calendar_id}/schedule"""
    print("\n" + "=" * 60)
    print(f"ТЕСТ 3: GET /backend/api/user/professions/{program_id}/schedule")
    print("=" * 60)

    url = f"{BASE_URL}/backend/api/user/professions/{program_id}/schedule"
    print(f"  URL: {url}")

    try:
        client = httpx.Client(cookies=cookies, timeout=15)
        response = client.get(url)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Length: {len(response.content)} bytes")

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_text": response.text[:2000]}

        result = {
            "endpoint": f"GET /backend/api/user/professions/{program_id}/schedule",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        save_json(f"profession_{program_id}_schedule", result)

        if response.status_code == 200 and isinstance(data, dict):
            print("  ✅ Успешно")
            modules = data.get("profession_modules", [])
            print(f"  📦 Найдено модулей: {len(modules)}")
            for m in modules[:3]:
                prog = m.get("program", {})
                print(f"    - {prog.get('name', 'N/A')} (id={prog.get('id', 'N/A')}, start={prog.get('start_date')}, finish={prog.get('finish_date')})")
            return modules
        else:
            print(f"  ⚠️ Статус {response.status_code}")
            print(f"  Body: {response.text[:500]}")

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

    return None


def test_program_schedule(cookies: httpx.Cookies, program_id: int) -> dict | None:
    """ТЕСТ 4: GET /backend/api/user/programs/{program_id}/schedule — события программы"""
    print("\n" + "=" * 60)
    print(f"ТЕСТ 4: GET /backend/api/user/programs/{program_id}/schedule")
    print("=" * 60)

    url = f"{BASE_URL}/backend/api/user/programs/{program_id}/schedule"
    print(f"  URL: {url}")

    try:
        client = httpx.Client(cookies=cookies, timeout=15)
        response = client.get(url)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Length: {len(response.content)} bytes")

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw_text": response.text[:2000]}

        result = {
            "endpoint": f"GET /backend/api/user/programs/{program_id}/schedule",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        save_json(f"program_{program_id}_schedule", result)

        if response.status_code == 200 and isinstance(data, dict):
            print("  ✅ Успешно")
            lessons = data.get("lessons", [])
            print(f"  📚 Найдено lessons: {len(lessons)}")
            if lessons:
                first = lessons[0]
                print(f"  📄 Первый lesson:")
                print(f"    title: {first.get('title', 'N/A')}")
                print(f"    block_title: {first.get('block_title', 'N/A')}")
                lesson_items = first.get("lesson_items", [])
                print(f"    lesson_items: {len(lesson_items)}")
                if lesson_items:
                    item = lesson_items[0]
                    print(f"    📄 Первый item:")
                    print(f"      type: {item.get('type', 'N/A')}")
                    print(f"      title: {item.get('title', 'N/A')[:80]}")
                    print(f"      keys: {list(item.keys())}")
            return data
        else:
            print(f"  ⚠️ Статус {response.status_code}")
            print(f"  Body: {response.text[:500]}")

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")

    return None


def main():
    print("🔬 Исследование endpoint'ов Netology (YetAnotherCalendar-style)")
    print(f"📧 Email: {NETOLOGY_EMAIL}")
    print(f"📁 Результаты: {OUTPUT_DIR}")

    if not NETOLOGY_EMAIL or not NETOLOGY_PASSWORD:
        print("❌ Не найдены NETOLOGY_EMAIL / NETOLOGY_PASSWORD в .env")
        sys.exit(1)

    # Тест 1: Авторизация
    cookies = test_sign_in()
    if not cookies:
        print("\n❌ Авторизация не удалась, дальнейшие тесты невозможны")
        sys.exit(1)

    # Тест 2: Список курсов
    programs = test_get_courses(cookies)

    if programs:
        # Тест 3: Profession schedule для первой программы
        first_program = programs[0]
        program_id = first_program.get("id")
        if program_id:
            test_profession_schedule(cookies, program_id)
            test_program_schedule(cookies, program_id)

        # Также протестируем бакалавриат (bhebfad-25) если есть
        for p in programs:
            if "bhebfad-25" in str(p.get("urlcode", "")) or "бакалавриат" in str(p.get("title", "")).lower():
                print(f"\n🎓 Найден бакалавриат: {p.get('title')} (id={p.get('id')})")
                test_profession_schedule(cookies, p.get("id"))
                test_program_schedule(cookies, p.get("id"))
                break
    else:
        # Попробуем с известным ID бакалавриата
        print("\n⚠️ Не удалось получить список курсов, пробуем с известным ID...")
        test_profession_schedule(cookies, 59690)  # bhebfad-25
        test_program_schedule(cookies, 59690)

    print("\n" + "=" * 60)
    print("✅ Исследование завершено")
    print(f"📁 Все результаты в: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
