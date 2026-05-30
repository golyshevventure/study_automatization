"""
Исследование endpoint'а GET /backend/api/user/lesson_items/{id}

Этап 2: полный обход profession → modules → programs → lessons → lesson_items,
запросы к lesson_items/{id} для всех найденных типов.

Результаты: backend/api_tests_etc/lesson_items/
"""

import json
import os
import sys
import time
from pathlib import Path

import httpx

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
    print(f"  💾 {path.name}")
    return path


def extract_lessons_from_schedule(schedule: dict) -> list:
    """Извлекает lessons из разных форматов schedule."""
    lessons = []
    if not isinstance(schedule, dict):
        return lessons
    lessons.extend(schedule.get("lessons", []))
    for block in schedule.get("blocks", []):
        lessons.extend(block.get("lessons", []))
    return lessons


def main():
    email = os.getenv("NETOLOGY_EMAIL")
    password = os.getenv("NETOLOGY_PASSWORD")
    if not email or not password:
        print("❌ NETOLOGY_EMAIL и NETOLOGY_PASSWORD в .env")
        sys.exit(1)

    print(f"🔐 Авторизация {email}...")
    service = NetologyAuthService(timeout=15.0)
    cookies = service.authenticate(email, password)
    print(f"✅ Cookies: {list(cookies.keys())}")

    client = httpx.Client(
        cookies=cookies,
        timeout=15.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        },
    )

    # ── 1. Получаем professions ──────────────────────────────────────────────
    print("\n📋 Получаем professions...")
    resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/calendar/filters")
    raw = resp.json() if resp.status_code == 200 else {}
    programs = raw.get("programs", []) if isinstance(raw, dict) else raw
    save_json("01_calendar_filters", {"status_code": resp.status_code, "data": raw})

    professions = [p for p in programs if p.get("type") == "profession" or p.get("is_profession")]
    print(f"   Всего программ: {len(programs)}, professions: {len(professions)}")

    # ── 2. Обходим profession → modules → program schedules ──────────────────
    print("\n📅 Обход profession → modules → programs...")
    all_lesson_items = []
    all_schedules = []

    for prof in professions[:3]:  # первые 3 profession
        prof_id = prof.get("id")
        prof_title = prof.get("title", prof.get("name", "unknown"))
        print(f"\n   🎓 Profession: {prof_title} (id={prof_id})")

        resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/professions/{prof_id}/schedule")
        if resp.status_code != 200:
            print(f"      ❌ {resp.status_code}")
            continue

        prof_schedule = resp.json()
        save_json(f"02_profession_{prof_id}_schedule", {"status_code": 200, "data": prof_schedule})

        modules = prof_schedule.get("profession_modules", [])
        print(f"      Modules: {len(modules)}")

        for mod in modules:
            mod_prog = mod.get("program", {})
            mod_prog_id = mod_prog.get("id")
            mod_prog_name = mod_prog.get("name", "unknown")
            if not mod_prog_id:
                continue

            resp2 = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/{mod_prog_id}/schedule")
            status2 = resp2.status_code
            sched2 = resp2.json() if status2 == 200 else None
            print(f"        📘 {mod_prog_name} (id={mod_prog_id}) → {status2}")

            if sched2:
                all_schedules.append({"profession_id": prof_id, "program_id": mod_prog_id, "schedule": sched2})
                lessons = extract_lessons_from_schedule(sched2)
                for lesson in lessons:
                    for li in lesson.get("lesson_items", []):
                        li["_source_profession_id"] = prof_id
                        li["_source_program_id"] = mod_prog_id
                        li["_source_lesson_id"] = lesson.get("id")
                        all_lesson_items.append(li)

    save_json("03_all_schedules_summary", [{"profession_id": s["profession_id"], "program_id": s["program_id"], "lessons_count": len(extract_lessons_from_schedule(s["schedule"]))} for s in all_schedules])
    save_json("04_all_lesson_items_summary", all_lesson_items)
    print(f"\n📦 Всего lesson_items: {len(all_lesson_items)}")

    # ── 3. Анализируем типы ──────────────────────────────────────────────────
    by_type = {}
    for li in all_lesson_items:
        t = li.get("type", "unknown")
        by_type.setdefault(t, []).append(li)

    print(f"\n🏷️  Типы lesson_items:")
    for t, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"   {t:12s}: {len(items):3d} шт.")

    # ── 4. Детальные запросы к lesson_items/{id} ─────────────────────────────
    print("\n🔍 Запрашиваем /lesson_items/{id}...")
    tested_ids = set()
    detailed = []

    # Берём до 5 штук каждого типа
    for t, items in by_type.items():
        for li in items[:5]:
            li_id = li.get("id")
            if not li_id or li_id in tested_ids:
                continue
            tested_ids.add(li_id)

            print(f"   lesson_items/{li_id} ({t}) ...", end=" ", flush=True)
            resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/lesson_items/{li_id}")
            print(f"{resp.status_code}")
            time.sleep(0.3)

            result = {
                "requested_id": li_id,
                "type_from_schedule": t,
                "status_code": resp.status_code,
                "data": resp.json() if resp.status_code == 200 else None,
                "text_preview": resp.text[:500] if resp.status_code != 200 else None,
            }
            detailed.append(result)
            save_json(f"05_lesson_item_{li_id}_{t}", result)

    save_json("06_all_detailed", detailed)

    # ── 5. Статистика по детальным ответам ───────────────────────────────────
    print("\n📊 Статистика по детальным ответам:")
    ok_data = [d for d in detailed if d["status_code"] == 200 and d["data"]]
    print(f"   Успешных: {len(ok_data)} / {len(detailed)}")

    for d in ok_data[:10]:
        data = d["data"]
        t = data.get("type", "unknown")
        has_video = bool(data.get("video_url"))
        has_files = bool(data.get("files"))
        has_content = bool(data.get("content"))
        print(f"   - {d['requested_id']} [{t}] video={has_video} files={has_files} content={has_content}")

    client.close()
    print(f"\n✅ Готово. Результаты: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
