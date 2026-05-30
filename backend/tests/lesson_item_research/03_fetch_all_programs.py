"""
Исследование lesson_items: обход ВСЕХ программ (paid, free, profession).

Для каждой программы пробуем:
  - /backend/api/user/programs/{id}/schedule
  - /backend/api/user/professions/{id}/schedule

Собираем lesson_items и делаем запросы к /lesson_items/{id}.
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


def save_json(name: str, data):
    path = OUTPUT_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 {path.name}")


def extract_lessons(schedule):
    if not isinstance(schedule, dict):
        return []
    lessons = list(schedule.get("lessons", []))
    for block in schedule.get("blocks", []):
        lessons.extend(block.get("lessons", []))
    # Если lessons пустые, возможно profession_modules → program → lessons
    if not lessons and "profession_modules" in schedule:
        for mod in schedule.get("profession_modules", []):
            prog = mod.get("program", {})
            lessons.extend(prog.get("lessons", []))
    return lessons


def main():
    email = os.getenv("NETOLOGY_EMAIL")
    password = os.getenv("NETOLOGY_PASSWORD")
    if not email or not password:
        print("❌ NETOLOGY_EMAIL и NETOLOGY_PASSWORD в .env")
        sys.exit(1)

    print(f"🔐 Авторизация {email}...")
    cookies = NetologyAuthService(timeout=15.0).authenticate(email, password)
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

    # ── 1. Calendar filters ──────────────────────────────────────────────────
    resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/calendar/filters")
    raw = resp.json() if resp.status_code == 200 else {}
    programs = raw.get("programs", []) if isinstance(raw, dict) else raw
    print(f"📋 Программ найдено: {len(programs)}")
    save_json("01_calendar_filters", {"status_code": resp.status_code, "data": raw})

    # ── 2. Обходим все программы ─────────────────────────────────────────────
    all_lesson_items = []
    for prog in programs:
        prog_id = prog.get("id")
        prog_title = prog.get("title", "unknown")
        if not prog_id:
            continue

        print(f"\n   📚 {prog_title} (id={prog_id})")

        # Пробуем programs/{id}/schedule
        r1 = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/{prog_id}/schedule")
        print(f"      programs/{prog_id}/schedule → {r1.status_code}")
        sched = None
        if r1.status_code == 200:
            sched = r1.json()
            save_json(f"02_program_{prog_id}_schedule", {"status_code": 200, "data": sched})

        lessons = extract_lessons(sched) if sched else []

        # Если lessons пустые, пробуем professions/{id}/schedule
        if not lessons:
            r2 = client.get(f"{NETOLOGY_BASE}/backend/api/user/professions/{prog_id}/schedule")
            print(f"      professions/{prog_id}/schedule → {r2.status_code}")
            if r2.status_code == 200:
                sched = r2.json()
                save_json(f"02_profession_{prog_id}_schedule", {"status_code": 200, "data": sched})
                # Для profession обходим модули и делаем запросы к programs/{module_program_id}/schedule
                for mod in sched.get("profession_modules", []):
                    mod_prog = mod.get("program", {})
                    mod_prog_id = mod_prog.get("id")
                    mod_name = mod_prog.get("name", "unknown")
                    if not mod_prog_id:
                        continue
                    r3 = client.get(f"{NETOLOGY_BASE}/backend/api/user/programs/{mod_prog_id}/schedule")
                    print(f"        📘 {mod_name} (id={mod_prog_id}) → {r3.status_code}")
                    if r3.status_code == 200:
                        mod_sched = r3.json()
                        mod_lessons = extract_lessons(mod_sched)
                        print(f"           Lessons: {len(mod_lessons)}")
                        for lesson in mod_lessons:
                            for li in lesson.get("lesson_items", []):
                                li["_source_profession_id"] = prog_id
                                li["_source_program_id"] = mod_prog_id
                                li["_source_lesson_id"] = lesson.get("id")
                                all_lesson_items.append(li)
                continue  # already processed lessons above

        print(f"      Lessons: {len(lessons)}")
        for lesson in lessons:
            for li in lesson.get("lesson_items", []):
                li["_source_program_id"] = prog_id
                li["_source_lesson_id"] = lesson.get("id")
                all_lesson_items.append(li)

    print(f"\n📦 Всего lesson_items: {len(all_lesson_items)}")
    save_json("03_all_lesson_items_summary", all_lesson_items)

    # ── 3. Типы ──────────────────────────────────────────────────────────────
    by_type = {}
    for li in all_lesson_items:
        by_type.setdefault(li.get("type", "unknown"), []).append(li)

    print("\n🏷️  Типы:")
    for t, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"   {t:12s}: {len(items):3d}")

    # ── 4. Детальные запросы ─────────────────────────────────────────────────
    print("\n🔍 /lesson_items/{id} ...")
    tested = set()
    detailed = []
    for t, items in by_type.items():
        for li in items[:5]:
            li_id = li.get("id")
            if not li_id or li_id in tested:
                continue
            tested.add(li_id)
            print(f"   {li_id} ({t}) ...", end=" ", flush=True)
            resp = client.get(f"{NETOLOGY_BASE}/backend/api/user/lesson_items/{li_id}")
            print(f"{resp.status_code}")
            time.sleep(0.3)
            detailed.append({
                "id": li_id,
                "type": t,
                "status_code": resp.status_code,
                "data": resp.json() if resp.status_code == 200 else None,
                "preview": resp.text[:300] if resp.status_code != 200 else None,
            })
            save_json(f"04_lesson_item_{li_id}_{t}", detailed[-1])

    save_json("05_all_detailed", detailed)

    # ── 5. Сводка ────────────────────────────────────────────────────────────
    print("\n📊 Сводка:")
    ok = [d for d in detailed if d["status_code"] == 200 and d["data"]]
    print(f"   Успешно: {len(ok)} / {len(detailed)}")
    for d in ok:
        dd = d["data"]
        print(f"   {d['id']} [{dd.get('type')}] video={bool(dd.get('video_url'))} files={bool(dd.get('files'))} content={bool(dd.get('content'))}")

    client.close()
    print(f"\n✅ Готово: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
