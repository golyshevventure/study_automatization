import os
import shutil


SECONDBRAIN = "/mnt/c/Users/golys/OneDrive/Рабочий стол/Second brain"
STUDY_DIR = os.path.join(SECONDBRAIN, "Учеба (Фин. Ун.)")


def remove_old_structure():
    """Удаляет старую структуру Second Brain перед прогоном."""
    paths_to_remove = [
        os.path.join(STUDY_DIR, "Конспекты"),
        os.path.join(STUDY_DIR, "Термины"),
        os.path.join(STUDY_DIR, "Предметы"),
        os.path.join(STUDY_DIR, "МОС - Учёба.md"),
    ]
    for path in paths_to_remove:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            print(f"🗑️ Удалена папка: {path}")
        elif os.path.isfile(path):
            os.remove(path)
            print(f"🗑️ Удалён файл: {path}")


def ensure_new_structure():
    """Создаёт корневую папку Дисциплины, если её нет."""
    disciplines_dir = os.path.join(STUDY_DIR, "Дисциплины")
    os.makedirs(disciplines_dir, exist_ok=True)
    return disciplines_dir


def ensure_subject_dirs(subject_name):
    """Создаёт папки дисциплины и 3 подпапки."""
    safe = _safe_filename(subject_name)
    base = os.path.join(STUDY_DIR, "Дисциплины", safe)
    for sub in ["Конспекты", "Учебные материалы", "Информация по дисциплине"]:
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    return base


def _safe_filename(name, max_len=80):
    name = __import__('re').sub(r'[\\/:"*?<>|]', '', name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(' ', 1)[0]
    return name
