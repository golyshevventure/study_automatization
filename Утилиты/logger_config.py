"""Конфигурация логирования для StudyCore."""

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Настраивает корневой логгер."""
    logger = logging.getLogger("studycore")
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Форматтер
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Консольный вывод (только INFO и выше)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Файловый вывод (DEBUG и выше)
    file_handler = logging.FileHandler(
        LOG_DIR / "studycore.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Отдельный файл для ошибок
    error_handler = logging.FileHandler(
        LOG_DIR / "errors.log", encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер для модуля."""
    return logging.getLogger(f"studycore.{name}")
