#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login

async def main():
    scraper = NetologyScraper(headless=True)
    await scraper.start()
    ok = await ensure_netology_login(scraper.page, "bhebfad-25-memeo-2")
    if ok:
        print("✅ Авторизация OK")
        await scraper.save_cookies()
    else:
        print("❌ Нужна ручная авторизация")
    await scraper.stop()

asyncio.run(main())
