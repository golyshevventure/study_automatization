import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))
from netology_scraper import NetologyScraper


async def main():
    scraper = NetologyScraper()
    await scraper.start()

    for pid in ["bhebfad-25", "bhebfad-25-ieu-2"]:
        print(f"\n{'='*50}")
        print(f"🔍 Тестируем program_id = {pid}")
        try:
            url = f"https://netology.ru/backend/api/user/programs/{pid}"
            resp = await scraper.page.evaluate(
                f"async () => {{ const r = await fetch('{url}'); return await r.json(); }}"
            )
            print(f"   ✅ Найдено: {resp.get('name', '???')}")
        except Exception as e:
            print(f"   ❌ {e}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
