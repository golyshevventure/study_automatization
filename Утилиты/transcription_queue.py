"""
Очередь задач транскрибации на SQLite.

Приоритеты:
  CRITICAL — пользователь ждёт у экрана
  NORMAL   — фоновая обработка
  BATCH    — ночная массовая обработка
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Optional

DB_PATH = "data/transcription_queue.db"


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицу очереди, если её нет."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id TEXT NOT NULL,
                program_id TEXT NOT NULL,
                audio_path TEXT NOT NULL,
                vtt_output_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'done', 'error')),
                priority TEXT DEFAULT 'NORMAL' CHECK(priority IN ('CRITICAL', 'NORMAL', 'BATCH')),
                error_msg TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority ON queue(status, priority, created_at)
        """)


def enqueue(
    lesson_id: str, program_id: str, audio_path: str, vtt_output_path: str, priority: str = "NORMAL"
) -> int:
    """Добавляет задачу в очередь. Возвращает id задачи."""
    init_db()
    with _get_conn() as conn:
        # Проверяем, нет ли уже такой задачи
        row = conn.execute(
            "SELECT id, status FROM queue WHERE lesson_id = ? AND program_id = ?",
            (lesson_id, program_id),
        ).fetchone()
        if row:
            if row["status"] == "done":
                return row["id"]  # Уже готово
            return row["id"]  # Уже в очереди

        cur = conn.execute(
            """
            INSERT INTO queue (lesson_id, program_id, audio_path, vtt_output_path, priority)
            VALUES (?, ?, ?, ?, ?)
            """,
            (lesson_id, program_id, audio_path, vtt_output_path, priority),
        )
        return cur.lastrowid


def get_next_task() -> Optional[dict]:
    """Забирает следующую задачу из очереди (по приоритету и времени)."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM queue
            WHERE status = 'pending'
            ORDER BY
                CASE priority
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'NORMAL' THEN 2
                    WHEN 'BATCH' THEN 3
                END,
                created_at ASC
            LIMIT 1
            """).fetchone()
        if not row:
            return None

        # Помечаем как processing
        conn.execute("UPDATE queue SET status = 'processing' WHERE id = ?", (row["id"],))
        return dict(row)


def mark_done(task_id: int):
    """Помечает задачу как выполненную."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE queue SET status = 'done', processed_at = ? WHERE id = ?",
            (datetime.now().isoformat(), task_id),
        )


def mark_error(task_id: int, error_msg: str):
    """Помечает задачу как ошибочную."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE queue SET status = 'error', error_msg = ?, processed_at = ? WHERE id = ?",
            (error_msg, datetime.now().isoformat(), task_id),
        )


def get_stats() -> dict:
    """Возвращает статистику очереди."""
    init_db()
    with _get_conn() as conn:
        stats = conn.execute("SELECT status, COUNT(*) as cnt FROM queue GROUP BY status").fetchall()
        return {row["status"]: row["cnt"] for row in stats}


def get_pending_count() -> int:
    """Количество задач в статусе pending."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM queue WHERE status = 'pending'").fetchone()
        return row["cnt"]


def get_vtt_path(lesson_id: str, program_id: str) -> Optional[str]:
    """Возвращает путь к готовому VTT, если задача выполнена."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT vtt_output_path FROM queue WHERE lesson_id = ? AND program_id = ? AND status = 'done'",
            (lesson_id, program_id),
        ).fetchone()
        if row and os.path.exists(row["vtt_output_path"]):
            return row["vtt_output_path"]
        return None


def process_next_task(whisper_pipe=None) -> bool:
    """
    Обрабатывает одну задачу из очереди.
    Возвращает True, если задача была обработана (или ошибка).
    Возвращает False, если очередь пуста.
    """
    import time
    from . import local_whisper

    task = get_next_task()
    if not task:
        return False

    task_id = task["id"]
    audio_path = task["audio_path"]
    vtt_output_path = task["vtt_output_path"]

    try:
        if not os.path.exists(audio_path):
            mark_error(task_id, f"Audio file not found: {audio_path}")
            return True

        print(f"🎙️  Транскрибация [{task_id}]: {os.path.basename(audio_path)}")
        start = time.time()

        # Используем переданный pipe или загружаем новый
        pipe = whisper_pipe or local_whisper._load_model()
        vtt_text = local_whisper.transcribe_to_vtt(audio_path, pipe=pipe)
        local_whisper.save_vtt(vtt_text, vtt_output_path)

        elapsed = time.time() - start
        print(f"✅ Готово [{task_id}] за {elapsed:.1f}с → {vtt_output_path}")
        mark_done(task_id)
        return True

    except Exception as e:
        err = str(e)
        print(f"❌ Ошибка [{task_id}]: {err}")
        mark_error(task_id, err)
        return True


def run_worker(max_tasks: Optional[int] = None, whisper_pipe=None):
    """
    Запускает рабочий цикл обработки очереди.
    max_tasks: ограничение на количество задач (None = бесконечно).
    """
    import time

    processed = 0
    while True:
        if max_tasks is not None and processed >= max_tasks:
            print(f"🏁 Достигнут лимит задач ({max_tasks})")
            break

        had_task = process_next_task(whisper_pipe=whisper_pipe)
        if not had_task:
            print("📭 Очередь пуста. Завершение.")
            break

        processed += 1
        # Небольшая пауза между задачами, чтобы GPU остывал
        time.sleep(2)
