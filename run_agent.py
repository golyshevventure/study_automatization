import asyncio
import os
import sys
import re
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from parsers.netology_scraper import NetologyScraper
from dotenv import load_dotenv
from generate_summary import generate_summary

load_dotenv()

SECONDBRAIN = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain"
STUDY_DIR = os.path.join(SECONDBRAIN, "Учеба (Фин. Ун.)")
PREDMETY = os.path.join(STUDY_DIR, "Предметы")
KONSPECTY = os.path.join(STUDY_DIR, "Конспекты")
TERMINY = os.path.join(STUDY_DIR, "Термины")

def ensure_dirs():
    os.makedirs(PREDMETY, exist_ok=True)
    os.makedirs(KONSPECTY, exist_ok=True)
    os.makedirs(TERMINY, exist_ok=True)

def safe_filename(name, max_len=80):
    name = re.sub(r'[\\/:"*?<>|]', '', name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(' ', 1)[0]
    return name

def parse_terms(full_text):
    pattern = re.compile(r'##?\s*Термины\n(.*?)(?:\n---END_TERMS---|\Z)', re.DOTALL)
    match = pattern.search(full_text)
    if not match:
        return full_text, []
    clean_text = full_text[:match.start()] + full_text[match.end():]
    block = match.group(1).strip()
    terms = []
    for line in block.split('\n'):
        line = line.strip()
        if '|' in line:
            parts = line.split('|', 1)
            name = parts[0].strip().strip('[]')
            desc = parts[1].strip()
            if name and desc:
                terms.append((name, desc))
    return clean_text, terms

def create_term_files(terms, subject_name):
    created = []
    for name, desc in terms:
        name = re.sub(r"[\-–—\s]+", " ", name).strip().title()
        if name.lower() == subject_name.lower():
            continue
        filename = f"{safe_filename(name)}.md"
        filepath = os.path.join(TERMINY, filename)
        if os.path.exists(filepath):
            continue
        content = f"""---
type: термин
subject: {subject_name}
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {name}

{desc}

## Связи
- [[{subject_name}]]
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(name)
        print(f"   📝 Термин: {name}")
    return created

def ensure_subject_file(subject_name):
    path = os.path.join(PREDMETY, f"{safe_filename(subject_name)}.md")
    if not os.path.exists(path):
        content = f"""---
type: предмет
status: active
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {subject_name}

## Прогресс
- [ ] Не начато

## Конспекты

## Связи
- [[МОС - Учёба]]
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📁 Создан предмет: {path}")
    return path

def add_conspect_link(subject_path, topic_title):
    with open(subject_path, "r", encoding="utf-8") as f:
        content = f.read()
    link_line = f"- [[{topic_title}]]"
    if link_line in content:
        return
    if "## Конспекты" in content:
        content = content.replace("## Конспекты", f"## Конспекты\n{link_line}", 1)
    else:
        content += f"\n\n## Конспекты\n{link_line}"
    with open(subject_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"   🔗 Ссылка добавлена")

def save_conspect(content, subject_name, topic_title):
    conspect_dir = os.path.join(KONSPECTY, safe_filename(subject_name))
    os.makedirs(conspect_dir, exist_ok=True)
    filename = f"{safe_filename(topic_title)}.md"
    filepath = os.path.join(conspect_dir, filename)
    meta = f"---\nsubject: {subject_name}\ntopic: {topic_title}\ndate: {datetime.now().strftime('%Y-%m-%d')}\ntype: конспект\nsource: Нетология\n---\n\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(meta + content)
    print(f"   💾 Конспект: {filepath}")
    return filepath

def process_lesson(subject_name, lesson_title, lesson_text):
    print(f"\n{'='*60}")
    print(f"🎓 {lesson_title}")
    print(f"{'='*60}")
    print(f"   Символов: {len(lesson_text)}")
    if not lesson_text or len(lesson_text) < 300:
        print("   ⚠️ Слишком мало текста, пропускаем")
        return
    print("   ⏳ Генерация конспекта...")
    raw_summary = generate_summary(lesson_text, subject_name, lesson_title)
    if raw_summary.startswith("Ошибка"):
        print(f"   ❌ {raw_summary}")
        return
    clean_summary, terms = parse_terms(raw_summary)
    if terms:
        print(f"   🔍 Терминов: {len(terms)}")
        create_term_files(terms, subject_name)
    subject_path = ensure_subject_file(subject_name)
    save_conspect(clean_summary, subject_name, lesson_title)
    add_conspect_link(subject_path, lesson_title)
    print("   ✅ Готово")

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

    ensure_dirs()

    scraper = NetologyScraper()
    await scraper.start()

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

        for disc in disciplines:
            section_name = disc["title"]

            if target_subject and target_subject.lower() not in section_name.lower():
                continue

            if disc["locked"]:
                print(f"\n   🔒 {section_name} — заблокировано, пропускаем")
                continue

            print(f"\n📂 {section_name}")

            # Силлабус
            syllabus_link = None
            for link in disc["links"]:
                if "рабочая программа" in link["text"].lower():
                    syllabus_link = link["href"]
                    break

            if syllabus_link:
                print("   📋 Извлекаем силлабус...")
                syllabus_text = await scraper.get_lesson_text_content(syllabus_link)
                syl_path = os.path.join(PREDMETY, f"{safe_filename(subject_name)} — Силлабус.md")
                if not os.path.exists(syl_path):
                    with open(syl_path, "w", encoding="utf-8") as f:
                        f.write(f"---\ntype: силлабус\nsubject: {subject_name}\n---\n\n# Силлабус: {subject_name}\n\n{syllabus_text[:5000]}")
                    print(f"   💾 Силлабус сохранён")
                    subj_path = ensure_subject_file(subject_name)
                    with open(subj_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    syl_link = f"- [[{subject_name} — Силлабус|Силлабус]]"
                    if syl_link not in content:
                        if "## Силлабус" not in content:
                            content += f"\n\n## Силлабус\n{syl_link}"
                        else:
                            content = content.replace("## Силлабус", f"## Силлабус\n{syl_link}")
                        with open(subj_path, "w", encoding="utf-8") as f:
                            f.write(content)

            # Проходим по занятиям
            lessons = await scraper.get_discipline_lessons(program_id, disc["lesson_id"], disc.get("links", []))

            for lesson in lessons:
                if lesson["locked"]:
                    print(f"   🔒 {lesson['title']}")
                    continue
                if lesson["href"] in seen_hrefs:
                    continue
                seen_hrefs.add(lesson["href"])

                conspect_dir = os.path.join(KONSPECTY, safe_filename(subject_name))
                conspect_file = os.path.join(conspect_dir, f"{safe_filename(lesson['title'])}.md")
                if os.path.exists(conspect_file):
                    print(f"   ⏭️ Уже есть: {lesson['title']}")
                    continue

                text = await scraper.get_lesson_text_content(lesson["href"])
                lesson_title = lesson['title']
                if lesson_title.lower() not in section_name.lower():
                    display_title = f"{section_name} — {lesson_title}"
                else:
                    display_title = section_name
                process_lesson(subject_name, display_title, text)
                await asyncio.sleep(2)

            print(f"   ✅ Раздел завершён")

        await scraper.save_cookies()
        print("\n" + "=" * 60)
        print("🏁 Всё готово!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n🛑 Остановлено пользователем")
    finally:
        await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
