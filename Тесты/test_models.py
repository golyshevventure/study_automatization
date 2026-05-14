import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

with open("data/test_subtitles.vtt", "r", encoding="utf-8") as f:
    from src.parsers.netology_scraper import NetologyScraper
    text = NetologyScraper._parse_vtt(f.read())

chunk = text[:8000]  # Одна часть для теста

models = [
    "poolside/laguna-m.1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-chat:free",
]

for model in models:
    print(f"\n{'='*60}")
    print(f"🔍 Тест: {model}")
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты личный ассистент. Пиши развёрнуто, не сокращай."},
                {"role": "user", "content": f"Сделай ПОЛНЫЙ конспект по тексту. Минимум 1500 слов. Не сокращай, не пропускай темы.\n\nПредмет: История экономических учений\nТема: Вебинар 14.02\n\n{text[:6000]}"}
            ],
            "max_tokens": 4000,
            "temperature": 0.3
        }
    )
    if resp.status_code == 200:
        content = resp.json()["choices"][0]["message"].get("content", "")
        words = len(content.split())
        print(f"✅ Слов: {words}, Символов: {len(content)}")
        print(content[:500] + "...")
    else:
        print(f"❌ Ошибка {resp.status_code}: {resp.text[:200]}")