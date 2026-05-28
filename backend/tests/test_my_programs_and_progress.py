"""
Скрипт для получения доступных программ (курсов) и прогресса по ним.
Эндпоинты:
  - GET /backend/api/user/programs/progress  — прогресс по всем программам
  - GET /backend/api/user/profile            — профиль пользователя (имя, аватар)
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary", "summary_programs"))

import httpx
from dotenv import load_dotenv

load_dotenv()

COOKIES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "netology_cookies", "netology_cookies.json")
API_BASE = "https://netology.ru/backend/api/user"


def load_cookies_for_httpx(cookies_file):
    if not os.path.exists(cookies_file):
        return {}
    with open(cookies_file, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    return {c["name"]: c["value"] for c in cookies}


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


async def fetch_profile(client):
    r = await client.get(f"{API_BASE}/profile")
    if r.status_code != 200:
        print(f"❌ Ошибка профиля: {r.status_code}")
        return None
    return r.json()


async def fetch_progress(client):
    r = await client.get(f"{API_BASE}/programs/progress")
    if r.status_code != 200:
        print(f"❌ Ошибка прогресса: {r.status_code}")
        return None
    return r.json()


async def main():
    cookies = load_cookies_for_httpx(COOKIES_FILE)
    if not cookies:
        print(f"❌ Cookies не найдены: {COOKIES_FILE}")
        print("   Сначала выполните авторизацию через netology_auth.py")
        return

    async with httpx.AsyncClient(cookies=cookies, follow_redirects=True) as client:
        # 1. Профиль
        print_header("ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ")
        profile = await fetch_profile(client)
        if profile:
            print(f"   Имя:  {profile.get('full_name', '—')}")
            print(f"   Email: {profile.get('email', '—')}")
            avatar = profile.get('avatar_url') or profile.get('avatar', {}).get('url')
            print(f"   Аватар: {avatar or '—'}")

        # 2. Прогресс / программы
        print_header("ДОСТУПНЫЕ ПРОГРАММЫ (КУРСЫ)")
        progress = await fetch_progress(client)
        if not progress:
            return

        programs = progress.get("programs", [])
        print(f"   Всего программ: {len(programs)}\n")

        for p in programs:
            p_type = "Профессия" if p.get("is_profession") else "Курс"
            print(f"   📚 {p_type}: {p['title']} (ID: {p['id']})")

            modules = p.get("modules", [])
            for m in modules:
                passed = m.get("lesson_items_passed", 0)
                total = m.get("lesson_items_count", 0)
                lessons_passed = m.get("lessons_passed", 0)
                lessons_total = m.get("lessons_count", 0)
                is_passed = m.get("is_passed", False)
                available = m.get("is_available", False)

                pct = (passed / total * 100) if total else 0
                status_icon = "✅" if is_passed else "📖"
                lock_icon = "🔓" if available else "🔒"

                print(f"      {status_icon} {lock_icon} {m['title']}")
                print(f"         Материалов: {passed}/{total} ({pct:.0f}%)")
                print(f"         Занятий:    {lessons_passed}/{lessons_total}")
            print()

        # 3. Сохраняем JSON
        out_dir = os.path.join(os.path.dirname(__file__), "..", "Данные")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "my_programs_progress.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        print(f"💾 Сохранено: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
