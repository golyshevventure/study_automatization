import os
import sys
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

from database import init_db, add_progress, add_term, term_exists

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

SECONDBRAIN = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain"
STUDY_DIR = os.path.join(SECONDBRAIN, "Учеба (Фин. Ун.)")
PREDMETY = os.path.join(STUDY_DIR, "Предметы")
KONSPECTY = os.path.join(STUDY_DIR, "Конспекты")
TERMINY = os.path.join(STUDY_DIR, "Термины")

def ensure_dirs():
    os.makedirs(PREDMETY, exist_ok=True)
    os.makedirs(KONSPECTY, exist_ok=True)
    os.makedirs(TERMINY, exist_ok=True)

def load_prompt():
    with open("prompts/system.txt", "r", encoding="utf-8") as f:
        return f.read()

def generate_summary(text, subject, topic):
    system = load_prompt()
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Study Automation Agent"
        },
        json={
            "model": "poolside/laguna-m.1:free",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Предмет: {subject}\nТема: {topic}\n\n{text[:8000]}"}
            ],
            "max_tokens": 2500,
            "temperature": 0.4
        }
    )
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"].get("content", "Пустой ответ")
    return f"Ошибка {resp.status_code}: {resp.text[:200]}"

def safe_filename(name):
    return re.sub(r'[\\/:"*?<>|]', '', name).strip()

def get_subject_path(subject_name):
    return os.path.join(PREDMETY, f"{safe_filename(subject_name)}.md")

def get_conspect_dir(subject_name):
    d = os.path.join(KONSPECTY, safe_filename(subject_name))
    os.makedirs(d, exist_ok=True)
    return d

def ensure_subject_file(subject_name):
    path = get_subject_path(subject_name)
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
        print(f"📁 Создан файл предмета: {path}")
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
    
    print(f"🔗 Добавлена ссылка в предмет: {link_line}")

def parse_terms(full_text):
    """Вырезает блок TERMS и возвращает (чистый_конспект, [(название, определение), ...])"""
    pattern = re.compile(r'---TERMS---\n(.*?)\n---END_TERMS---', re.DOTALL)
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
        if name.lower() == subject_name.lower():
            print(f"   ⏭️ Пропущено (название предмета): {name}")
            continue
        if term_exists(name):
            print(f"   ⏭️ Термин уже есть: {name}")
            continue
        
        filename = f"{safe_filename(name)}.md"
        filepath = os.path.join(TERMINY, filename)
        
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
        
        add_term(name, desc, subject_name, filepath)
        created.append(name)
        print(f"   📝 Создан термин: {filepath}")
    
    return created

def save_conspect(content, subject_name, topic_title):
    conspect_dir = get_conspect_dir(subject_name)
    filename = f"{safe_filename(topic_title)}.md"
    filepath = os.path.join(conspect_dir, filename)
    
    meta = f"---\nsubject: {subject_name}\ntopic: {topic_title}\ndate: {datetime.now().strftime('%Y-%m-%d')}\ntype: конспект\nsource: Нетология\n---\n\n"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(meta + content)
    
    print(f"💾 Конспект сохранён: {filepath}")
    return filepath

def main():
    if len(sys.argv) < 4:
        print('Использование:')
        print('  python netology_agent.py "Название предмета" "Тема 1 - Название" lecture.txt')
        sys.exit(1)
    
    subject = sys.argv[1]
    topic = sys.argv[2]
    lecture_file = sys.argv[3]
    
    init_db()
    ensure_dirs()
    
    subject_path = ensure_subject_file(subject)
    
    with open(lecture_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"📖 Предмет: {subject}")
    print(f"🎓 Тема: {topic}")
    print(f"📝 Символов: {len(text)}")
    print("⏳ Генерация конспекта...")
    
    raw_summary = generate_summary(text, subject, topic)
    if raw_summary.startswith("Ошибка"):
        print(raw_summary)
        sys.exit(1)
    
    # Парсим TERMS и создаём файлы
    clean_summary, terms = parse_terms(raw_summary)
    if terms:
        print(f"🔍 Найдено терминов: {len(terms)}")
        create_term_files(terms, subject)
    else:
        print("🔍 Терминов не найдено (модель не выдала блок TERMS)")
    
    # Сохраняем конспект (уже без TERMS-блока)
    conspect_path = save_conspect(clean_summary, subject, topic)
    add_conspect_link(subject_path, topic)
    add_progress(subject, topic, "", conspect_path)
    
    print("✅ Готово!")

if __name__ == "__main__":
    main()
