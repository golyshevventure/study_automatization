import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

def load_prompt():
    with open("prompts/system.txt", "r", encoding="utf-8") as f:
        return f.read()

def generate_chunk(text, subject, topic):
    system = load_prompt()
    instructions = f"""Сделай РАЗВЁРНУТЫЙ конспект по тексту вебинара. Требования:
- Минимум 800 слов.
- НЕ сокращай до тезисов — пиши полноценные абзацы.
- НЕ цитируй дословно речь лектора, перерабатывай в свой текст.
- Выделяй жирным ключевые термины.
- Давай примеры и контекст.
- Если упоминается исторический период — опиши его подробно.
- В конце блок ## Термины с терминами и определениями через |.
- Каждый термин пиши жирным: **Название** | определение.
- Каждый термин: Название | РАЗВЁРНУТОЕ определение (минимум 3 предложения, примеры, контекст использования). НЕ одна строка.

Предмет: {subject}
Тема: {topic}
"""

    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Study Automation Agent"
        },
        json={
            "model": "deepseek/deepseek-v4-flash:free",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": instructions + "\n\nТекст вебинара:\n" + text[:20000]}
            ],
            "max_tokens": 4000,
            "temperature": 0.3
        }
    )
    if resp.status_code == 200:
        result = resp.json()["choices"][0]["message"].get("content") or ""
        if not result:
            return "Ошибка: пустой ответ от модели"
        result = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]+', '', result)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result
    return f"Ошибка {resp.status_code}"

def generate_summary(text, subject, topic):
    if len(text) <= 20000:
        return generate_chunk(text, subject, topic)

    chunks = []
    current = ""
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if len(current) + len(sentence) > 19000:
            chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence
    if current:
        chunks.append(current.strip())

    if len(chunks) > 10:
        print(f"   ⚠️ Слишком много частей ({len(chunks)}), ограничиваем 10")
        chunks = chunks[:10]

    print(f"   📦 Текст разбит на {len(chunks)} частей")

    partial_summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"   ⏳ Часть {i}/{len(chunks)}...")
        summary = generate_chunk(chunk, subject, topic)
        if not summary.startswith("Ошибка"):
            summary = re.sub(r'^# .+?\n+', '', summary, flags=re.MULTILINE)
            partial_summaries.append(summary.strip())

    if not partial_summaries:
        return "Ошибка генерации"

    header = f"# {topic}\n\n**Предмет:** {subject}\n\n"
    combined = header + "\n\n".join(partial_summaries)
    return combined

if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'src')
    from parsers.netology_scraper import NetologyScraper
    with open("data/test_subtitles.vtt", "r", encoding="utf-8") as f:
        text = NetologyScraper._parse_vtt(f.read())
    result = generate_summary(text, "История экономических учений", "Вебинар 14.02")
    print(f"\n{'='*60}")
    print(f"Результат: {len(result)} символов, {len(result.split())} слов")
    print(result[:1000])
