import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "agent.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY,
        subject TEXT,
        topic TEXT,
        topic_number TEXT,
        status TEXT DEFAULT 'pending',
        conspect_path TEXT,
        created_at TEXT,
        completed_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS terms (
        id INTEGER PRIMARY KEY,
        term TEXT UNIQUE,
        definition TEXT,
        subject TEXT,
        file_path TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def add_progress(subject, topic, topic_number, conspect_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO progress (subject, topic, topic_number, status, conspect_path, created_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (subject, topic, topic_number, 'completed', conspect_path, now, now))
    conn.commit()
    conn.close()

def get_completed_topics(subject):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT topic FROM progress WHERE subject = ? AND status = 'completed'", (subject,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def add_term(term, definition, subject, file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT OR IGNORE INTO terms (term, definition, subject, file_path, created_at) VALUES (?, ?, ?, ?, ?)",
              (term, definition, subject, file_path, now))
    conn.commit()
    conn.close()

def term_exists(term):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM terms WHERE term = ?", (term,))
    exists = c.fetchone() is not None
    conn.close()
    return exists
