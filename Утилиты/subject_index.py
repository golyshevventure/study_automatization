import os
import re


STUDY_DIR = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain/Учеба (Фин. Ун.)"


def _safe_filename(name, max_len=80):
    name = re.sub(r'[\\/:"*?<>|]', '', name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(' ', 1)[0]
    return name


def _extract_existing_links(content, section):
    """Извлекает существующие wiki-ссылки из раздела."""
    pattern = rf"## {re.escape(section)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return set()
    block = match.group(1)
    links = re.findall(r'- \[\[(.+?)\]\]', block)
    return set(links)


def update_subject_index(subject_name, conspects, materials, info_items):
    """
    Обновляет файл предмета внутри папки дисциплины.
    Создаёт или перезаписывает файл {subject}/{subject}.md
    """
    safe = _safe_filename(subject_name)
    if not safe:
        print("⚠️ Пустое имя предмета, индексный файл не создан")
        return
    subject_dir = os.path.join(STUDY_DIR, "Дисциплины", safe)
    os.makedirs(subject_dir, exist_ok=True)

    filepath = os.path.join(subject_dir, f"{safe}.md")

    # Читаем существующий файл, если есть
    existing_conspects = set()
    existing_materials = set()
    existing_info = set()

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        existing_conspects = _extract_existing_links(content, "Конспекты")
        existing_materials = _extract_existing_links(content, "Учебные материалы")
        existing_info = _extract_existing_links(content, "Информация по дисциплине")

    # Добавляем новые
    existing_conspects.update(conspects)
    existing_materials.update(materials)
    existing_info.update(info_items)

    lines = [f"# {subject_name}", ""]

    if existing_conspects:
        lines.append("## Конспекты")
        for link in sorted(existing_conspects):
            lines.append(f"- [[{link}]]")
        lines.append("")

    if existing_materials:
        lines.append("## Учебные материалы")
        for link in sorted(existing_materials):
            lines.append(f"- [[{link}]]")
        lines.append("")

    if existing_info:
        lines.append("## Информация по дисциплине")
        for link in sorted(existing_info):
            lines.append(f"- [[{link}]]")
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"📝 Файл предмета обновлён: {filepath}")


def reset_subject_index(subject_name):
    """Очищает файл предмета (перед новым прогоном)."""
    safe = _safe_filename(subject_name)
    if not safe:
        return
    filepath = os.path.join(STUDY_DIR, "Дисциплины", safe, f"{safe}.md")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Очищаем только разделы со ссылками, оставляя заголовок
        content = re.sub(r'\n## Конспекты\n.*?(?=\n## |\Z)', '\n## Конспекты\n', content, flags=re.DOTALL)
        content = re.sub(r'\n## Учебные материалы\n.*?(?=\n## |\Z)', '\n## Учебные материалы\n', content, flags=re.DOTALL)
        content = re.sub(r'\n## Информация по дисциплине\n.*?(?=\n## |\Z)', '\n## Информация по дисциплине\n', content, flags=re.DOTALL)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🔄 Файл предмета очищен: {filepath}")
