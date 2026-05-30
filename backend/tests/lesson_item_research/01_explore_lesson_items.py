"""
Исследование endpoint'а GET /backend/api/user/lesson_items/{id}

Этап 1: авторизация, получение программ, schedule, извлечение lesson_item IDs,
запросы к lesson_items/{id}, сохранение сырых ответов.

Результаты сохраняются в backend/api_tests_etc/lesson_items/
"""

import json
import os
import sys
from pathlib import Path

import httpx

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.auth_service.netology_auth import NetologyAuthService, NetologyAuthError

NETOLOGY_BASE = "https://netology.ru"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "api_tests_etc" / "lesson_items"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(name: str, data: dict | list) -> Path:
    path = OUTPUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Сохранено: {path.name}")
    return path


def main():
    email = os.getenv("NETOLOGY_EMAIL")
    password = os.getenv("NETOLOGY_PASSWORD")

    if not email or not password:
        print("❌ Укажите NETOLOGY_EMAIL и NETOLOGY_PASSWORD в .env")
        sys.exit(1)

    print(f"🔐 Авторизация как {email}...")
    service = NetologyAuthService(timeout=15.0)
    try:
        cookies = service.authenticate(email, password)
    except NetologyAuthError as exc:
        print(f"❌ Ошибка авторизации: {exc}")
        sys.exit(1)

    print(f"✅ Авторизация успешна. Cookies: {list(cookies.keys())}")

    client = httpx.Client(
        cookies=cookies,
        timeout=15.0,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        },
        follow_redirects=True,
    )

    # ── 1. Получаем список программ ──────────────────────────────────────────
    print("\n📋 Получаем список программ (calendar/filters)...")
    resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/calendar/filters")
    print(f"   Status: {resp.status_code}")
    programs_data = resp.json() if resp.status_code == 200 else {}
    save_json("01_programs_filters", {"status_code": resp.status_code, "data": programs_data})

    programs = programs_data if isinstance(programs_data, list) else programs_data.get("programs", [])
    if not programs:
        print("⚠️ Программы не найдены, пробуем /backend/api/user/student_learning/calendar")
        resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/student_learning/calendar")
        print(f"   Status: {resp.status_code}")
        programs_data = resp.json() if resp.status_code == 200 else {}
        save_json("01b_student_learning_calendar", {"status_code": resp.status_code, "data": programs_data})
        programs = programs_data if isinstance(programs_data, list) else programs_data.get("programs", [])

    print(f"   Найдено программ: {len(programs)}")
    if not programs:
        print("❌ Нет программ для исследования")
        return

    # ── 2. Получаем schedule для каждой программы ────────────────────────────
    print("\n📅 Получаем schedule для программ...")
    all_lesson_items = []  # список dict'ов с id, type, title, program_id
    for prog in programs[:5]:  # ограничимся первыми 5 программами
        prog_id = prog.get("id")
        prog_title = prog.get("title", prog.get("name", "unknown"))
        if not prog_id:
            continue

        print(f"\n   📚 Программа: {prog_title} (id={prog_id})")

        # Пробуем programs/{id}/schedule
        resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/{prog_id}/schedule")
        print(f"      programs/{prog_id}/schedule → {resp.status_code}")
        if resp.status_code == 200:
            save_json(f"02_program_{prog_id}_schedule", {"status_code": resp.status_code, "data": resp.json()})
            schedule = resp.json()
        else:
            # Пробуем professions/{id}/schedule
            resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/professions/{prog_id}/schedule")
            print(f"      professions/{prog_id}/schedule → {resp.status_code}")
            save_json(f"02_profession_{prog_id}_schedule", {"status_code": resp.status_code, "data": resp.json() if resp.status_code == 200 else None})
            schedule = resp.json() if resp.status_code == 200 else {}

        # Извлекаем lesson_items из schedule
        # Структура может быть разной: lessons напрямую или profession_modules → lessons
        lessons = []
        if isinstance(schedule, dict):
            lessons = schedule.get("lessons", [])
            if not lessons and "profession_modules" in schedule:
                for mod in schedule.get("profession_modules", []):
                    mod_lessons = mod.get("lessons", [])
                    if not mod_lessons and "program" in mod:
                        mod_lessons = mod.get("program", {}).get("lessons", [])
                    lessons.extend(mod_lessons)
            if not lessons and "blocks" in schedule:
                for block in schedule.get("blocks", []):
                    lessons.extend(block.get("lessons", []))

        print(f"      Извлечено lessons: {len(lessons)}")
        for lesson in lessons:
            for li in lesson.get("lesson_items", []):
                li["_source_program_id"] = prog_id
                li["_source_program_title"] = prog_title
                li["_source_lesson_id"] = lesson.get("id")
                all_lesson_items.append(li)

    print(f"\n📦 Всего lesson_items извлечено: {len(all_lesson_items)}")

    # Сохраняем все lesson_items для анализа
    save_json("03_all_lesson_items_summary", all_lesson_items)

    # ── 3. Исследуем уникальные типы lesson_items ────────────────────────────
    types = {}
    for li in all_lesson_items:
        t = li.get("type", "unknown")
        types.setdefault(t, []).append(li)

    print(f"\n🏷️  Типы lesson_items: {list(types.keys())}")
    for t, items in types.items():
        print(f"   {t}: {len(items)} шт.")

    # ── 4. Делаем запросы к lesson_items/{id} ────────────────────────────────
    print("\n🔍 Запрашиваем детали lesson_items...")
    # Берём до 3 штук каждого типа
    tested_ids = set()
    detailed_items = []
    for t, items in types.items():
        for li in items[:3]:
            li_id = li.get("id")
            if not li_id or li_id in tested_ids:
                continue
            tested_ids.add(li_id)

            print(f"   lesson_items/{li_id} (type={t})...", end=" ")
            resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/lesson_items/{li_id}")
            print(f"→ {resp.status_code}")

            result = {
                "requested_id": li_id,
                "type_from_schedule": t,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "data": resp.json() if resp.status_code == 200 else None,
                "text_preview": resp.text[:500] if resp.status_code != 200 else None,
            }
            detailed_items.append(result)
            save_json(f"04_lesson_item_{li_id}_{t}", result)

    save_json("05_all_detailed_lesson_items", detailed_items)

    # ── 5. Ищем lesson_items с video_url (Kinescope) ─────────────────────────
    print("\n🎬 Ищем video_url (Kinescope)...")
    video_items = [li for li in all_lesson_items if li.get("video_url")]
    print(f"   Найдено с video_url: {len(video_items)}")
    for vi in video_items[:5]:
        print(f"   - {vi['id']} {vi.get('type')} → {vi.get('video_url')}")

    # ── 6. Ищем lesson_items с files ─────────────────────────────────────────
    print("\n📎 Ищем файлы...")
    file_items = [li for li in all_lesson_items if li.get("files")]
    print(f"   Найдено с files: {len(file_items)}")
    for fi in file_items[:5]:
        files = fi.get("files", [])
        print(f"   - {fi['id']} {fi.get('type')} → {len(files)} файл(ов)")
        for f in files:
            print(f"      {f.get('name')} ({f.get('extension')}) → {f.get('link', '')[:80]}")

    client.close()
    print(f"\n✅ Исследование завершено. Результаты в: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
