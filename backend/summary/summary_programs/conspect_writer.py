import os
import re
from datetime import datetime

STUDY_DIR = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain/Учеба (Фин. Ун.)"


def _safe_filename(name, max_len=80):
    name = re.sub(r'[\\/:"*?<>|]', "", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0]
    return name


def write_material(subject_name, category, title, content, url=""):
    """
    Записывает материал в нужную папку.
    category: "Конспекты" | "Учебные материалы" | "Информация по дисциплине"
    """
    safe_subject = _safe_filename(subject_name)
    safe_title = _safe_filename(title)

    folder = os.path.join(STUDY_DIR, "Дисциплины", safe_subject, category)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{safe_title}.md")

    header = f"# {title}\n\n"
    if url:
        header += f"**Источник:** {url}\n\n"
    header += f"**Дата создания:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
    header += "---\n\n"

    full_content = header + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"💾 Сохранено: {filepath}")
    return filepath


def write_large_file_stub(subject_name, category, title, url=""):
    """Создаёт заглушку для большого файла."""
    content = (
        "⚠️ **Файл слишком большой для автоматической обработки.**\n\n"
        "Этот материал требует самостоятельного изучения.\n\n"
        "Рекомендуется ознакомиться с оригиналом на платформе Нетология.\n"
    )
    return write_material(subject_name, category, title, content, url)


def wiki_link(subject_name, category, title):
    """Возвращает wiki-ссылку для Obsidian."""
    safe_subject = _safe_filename(subject_name)
    safe_title = _safe_filename(title)
    return f"Дисциплины/{safe_subject}/{category}/{safe_title}"
