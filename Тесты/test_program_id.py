import asyncio
import sys

sys.path.insert(0, "src")
from parsers.netology_scraper import NetologyScraper


async def main():
    scraper = NetologyScraper()
    await scraper.start()

    for pid in ["bhebfad-25", "bhebfad-25-ieu-2"]:
        print(f"\n{'='*50}")
        print(f"🔍 Тестируем program_id = {pid}")
        try:
            title, discs = await scraper.get_program_disciplines(pid)
            print(f"✅ Найдено: {title}")
            print(f"📚 Разделов: {len(discs)}")
            for d in discs[:5]:
                print(f"   - {d['title']} (id: {d['lesson_id']})")
            if len(discs) > 5:
                print(f"   ... и ещё {len(discs)-5}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
