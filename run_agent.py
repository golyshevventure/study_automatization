import asyncio
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Утилиты"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv
from generate_summary import generate_summary
from second_brain_cleanup import remove_old_structure, ensure_new_structure, ensure_subject_dirs
from material_classifier import classify_material, category_folder
from subject_index import update_subject_index, reset_subject_index
from conspect_writer import write_material, write_large_file_stub, wiki_link

load_dotenv()

SECONDBRAIN = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain"
STUDY_DIR = os.path.join(SECONDBRAIN, "Учеба (Фин. Ун.)")


def safe_filename(name, max_len=80):
    name = re.sub(r'[\\/:"*?<>|]', '', name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(' ', 1)[0]
    return name


def process_lesson(subject_name, section_name, lesson_title, lesson_text, lesson_href=""):
    """Обрабатывает один материал: классифицирует, генерирует конспект или заглушку, сохраняет."""
    display_title = f"{section_name} — {lesson_title}" if lesson_title.lower() not in section_name.lower() else section_name

    print(f"\n{'='*60}")
    print(f"🎓 {display_title}")
    print(f"{'='*60}")

    # Классифицируем материал
    category = classify_material(lesson_title, section_name)
    folder_name = category_folder(category)
    print(f"   📁 Категория: {folder_name}")

    # Большой файл (>150K) — scraper вернул None
    if lesson_text is None:
        print(f"   ⚠️ Файл слишком большой, создаём заглушку")
        write_large_file_stub(subject_name, folder_name, display_title, lesson_href)
        return folder_name, wiki_link(subject_name, folder_name, display_title)

    print(f"   Символов: {len(lesson_text)}")

    # Слишком мало текста
    if not lesson_text or len(lesson_text) < 300:
        print(f"   ⚠️ Слишком мало текста ({len(lesson_text)} симв.), пропускаем")
        return None, None

    # Генерация конспекта
    print("   ⏳ Генерация конспекта...")
    raw_summary = generate_summary(lesson_text, subject_name, display_title)
    if raw_summary.startswith("Ошибка"):
        print(f"   ❌ {raw_summary}")
        return None, None

    # Сохраняем
    write_material(subject_name, folder_name, display_title, raw_summary, lesson_href)
    link = wiki_link(subject_name, folder_name, display_title)
    print("   ✅ Готово")
    return folder_name, link


async def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python run_agent.py <program_id>  — собрать всю программу")
        print("  python run_agent.py <program_id> --subject 'Название'  — только разделы с этим словом")
        sys.exit(1)

    program_id = sys.argv[1]
    target_subject = None
    if "--subject" in sys.argv:
        idx = sys.argv.index("--subject")
        target_subject = sys.argv[idx + 1]

    # Очистка старой структуры
    print("🧹 Очистка старой структуры Second Brain...")
    remove_old_structure()
    ensure_new_structure()

    # Авторизация
    scraper = NetologyScraper(headless=True)
    await scraper.start()
    login_ok = await ensure_netology_login(scraper.page, program_id)

    if not login_ok:
        print("🔓 Cookies протухли, переключаюсь на видимый браузер для ручного входа...")
        await scraper.stop()
        scraper = NetologyScraper(headless=False)
        await scraper.start()
        login_ok = await ensure_netology_login(scraper.page, program_id)
        if not login_ok:
            print("❌ Не удалось авторизоваться в Нетологии")
            await scraper.stop()
            sys.exit(1)

    try:
        print("=" * 60)
        print("🔍 Сбор структуры...")
        print("=" * 60)

        program_title, disciplines = await scraper.get_program_disciplines(program_id)
        subject_name = program_title

        print(f"\n📚 Предмет: {subject_name}")
        print(f"   Разделов: {len(disciplines)}")

        if target_subject:
            print(f"   🔍 Фильтр: только разделы содержащие '{target_subject}'")

        seen_hrefs = set()

        if target_subject:
            print(f"   🔍 Фильтр: только разделы содержащие '{target_subject}'")

        # Создаём папки дисциплины
        ensure_subject_dirs(subject_name)
        reset_subject_index(subject_name)

        # Собираем ссылки по категориям
        conspect_links = set()
        material_links = set()
        info_links = set()

        seen_hrefs = set()

        for disc in disciplines:
            section_name = disc["title"]

            if target_subject and target_subject.lower() not in section_name.lower():
                continue

            if disc["locked"]:
                print(f"\n   🔒 {section_name} — заблокировано, пропускаем")
                continue

            print(f"\n📂 {section_name}")

            lessons = await scraper.get_discipline_lessons(program_id, disc["lesson_id"], disc.get("links", []))

            if not lessons and disc.get("links"):
                print(f"   🔄 Под-занятия не найдены, берём ссылки раздела напрямую")
                lessons = [
                    {"title": link.get("text", section_name), "href": link["href"], "locked": False}
                    for link in disc["links"]
                    if link.get("href")
                ]

            for lesson in lessons:
                if lesson["locked"]:
                    print(f"   🔒 {lesson['title']}")
                    continue
                if lesson["href"] in seen_hrefs:
                    continue
                seen_hrefs.add(lesson["href"])

                text = await scraper.get_lesson_text_content(lesson["href"])
                folder, link = process_lesson(
                    subject_name,
                    section_name,
                    lesson["title"],
                    text,
                    lesson["href"]
                )

                if link:
                    if folder == "Конспекты":
                        conspect_links.add(link)
                    elif folder == "Учебные материалы":
                        material_links.add(link)
                    elif folder == "Информация по дисциплине":
                        info_links.add(link)

                await asyncio.sleep(10)

            print(f"   ✅ Раздел завершён")

        # Обновляем файл предмета
        update_subject_index(subject_name, conspect_links, material_links, info_links)

        await scraper.save_cookies()
        print("\n" + "=" * 60)
        print("🏁 Всё готово!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n🛑 Остановлено пользователем")
    finally:
        try:
            await scraper.save_cookies()
        except Exception:
            pass
        await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
