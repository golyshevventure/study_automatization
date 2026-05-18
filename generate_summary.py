import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

CHUNK_SIZE = 70000
MAX_CHUNKS = 3


def load_prompt():
    with open("Промпты/system.txt", "r", encoding="utf-8") as f:
        return f.read()


def generate_chunk(text, subject, topic, retries=3):
    system = load_prompt()
    user_msg = f"Предмет: {subject}\nТема: {topic}\n\nТекст вебинара:\n{text[:CHUNK_SIZE]}"

    for attempt in range(retries + 1):
        time.sleep(15)
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "Study Automation Agent"
                },
                json={
                    "model": "deepseek/deepseek-v3.2",
                    "provider": {
                        "allow_fallbacks": True
                    },
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_msg}
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.3
                },
                timeout=300
            )
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                wait = 15 + attempt * 15
                print(f"   ⏳ Сетевая ошибка ({e}), ждём {wait} сек... (попытка {attempt + 1}/{retries})")
                time.sleep(wait)
                continue
            return f"Ошибка сети: {e}"
        except Exception as e:
            if attempt < retries:
                wait = 15 + attempt * 15
                print(f"   ⏳ Неизвестная ошибка ({e}), ждём {wait} сек... (попытка {attempt + 1}/{retries})")
                time.sleep(wait)
                continue
            return f"Ошибка: {e}"
        if resp.status_code == 200:
            result = resp.json()["choices"][0]["message"].get("content") or ""
            if not result:
                return "Ошибка: пустой ответ от модели"
            result = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+', '', result)
            result = re.sub(r'\n{3,}', '\n\n', result)
            return result
        if resp.status_code == 429 and attempt < retries:
            wait = 30 + attempt * 30
            print(f"   ⏳ 429 Rate limit, ждём {wait} сек... (попытка {attempt + 1}/{retries})")
            time.sleep(wait)
            continue
        return f"Ошибка {resp.status_code}: {resp.text[:200]}"
    return "Ошибка 429: исчерпаны попытки"


def classify_lesson_via_llm(lesson_title: str, item_titles: list, subject: str, retries=2) -> str:
    """
    Отправляет title урока + список item'ов в LLM для определения стратегии.
    Возвращает одну из: "skip", "split", "merge_conspect", "split_program"
    """
    items_str = "\n".join(f"- {t}" for t in item_titles)
    user_msg = (
        f"Предмет: {subject}\n"
        f"Название занятия: {lesson_title}\n"
        f"Материалы внутри:\n{items_str}\n\n"
        f"Определи стратегию обработки. Верни ТОЛЬКО одно слово из списка:\n"
        f"- skip — если это домашнее задание, тест, контрольная, опрос, задание к вебинару\n"
        f"- split — если это обычные учебные материалы без видео (тексты, презентации)\n"
        f"- merge_conspect — если это вебинар, лекция, видеоурок, итоги темы (нужен один конспект)\n"
        f"- split_program — если это 'Рабочая программа дисциплины'\n\n"
        f"Ответ (одно слово):"
    )

    for attempt in range(retries + 1):
        time.sleep(5)
        try:
            resp = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "Study Automation Agent"
                },
                json={
                    "model": "deepseek/deepseek-v3.2",
                    "provider": {"allow_fallbacks": True},
                    "messages": [
                        {"role": "system", "content": "Ты — классификатор учебных материалов. Отвечай ТОЛЬКО одним словом: skip, split, merge_conspect или split_program."},
                        {"role": "user", "content": user_msg}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                timeout=60
            )
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                time.sleep(10)
                continue
            print(f"   ⚠️ LLM classification error: {e}")
            return "split"
        if resp.status_code == 200:
            result = resp.json()["choices"][0]["message"].get("content", "").strip().lower()
            for valid in ["skip", "split", "merge_conspect", "split_program"]:
                if valid in result:
                    print(f"   🧠 LLM стратегия: {valid}")
                    return valid
            print(f"   ⚠️ LLM вернул неожиданный ответ: {result}")
            return "split"
        if resp.status_code == 429 and attempt < retries:
            time.sleep(30)
            continue
        print(f"   ⚠️ LLM classification HTTP {resp.status_code}")
        return "split"
    return "split"


def generate_summary(text, subject, topic):
    if len(text) <= CHUNK_SIZE:
        return generate_chunk(text, subject, topic)

    chunks = []
    current = ""
    for sentence in re.split(r'(?<=[.!?:])\s+', text):
        if len(current) + len(sentence) > CHUNK_SIZE - 1000:
            chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence
    if current:
        chunks.append(current.strip())

    if len(chunks) > MAX_CHUNKS:
        print(f"   ⚠️ Слишком много частей ({len(chunks)}), ограничиваем {MAX_CHUNKS}")
        chunks = chunks[:MAX_CHUNKS]

    print(f"   📦 Текст разбит на {len(chunks)} частей")

    partial_summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"   ⏳ Часть {i}/{len(chunks)}...")
        summary = generate_chunk(chunk, subject, topic)
        if not summary.startswith("Ошибка"):
            summary = re.sub(r'^# .+?\n+', '', summary, flags=re.MULTILINE)
            partial_summaries.append(summary.strip())
        if i < len(chunks):
            time.sleep(15)

    if not partial_summaries:
        return "Ошибка генерации"

    combined = "\n\n".join(partial_summaries)
    return combined
