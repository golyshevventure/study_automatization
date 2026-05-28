import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

with open("data/test_subtitles.vtt", "r", encoding="utf-8") as f:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))
    from netology_scraper import NetologyScraper

    text = NetologyScraper._parse_vtt(f.read())

chunk = text[:8000]  # Одна часть для теста

models = [
    "poolside/laguna-m.1:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-chat:free",
]
