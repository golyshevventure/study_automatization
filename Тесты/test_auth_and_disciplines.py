import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))

from dotenv import load_dotenv
from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login

load_dotenv()

PROGRAM_ID = "bhebfad-25-ieu-2"

async def main():
    scraper = NetologyScraper()
    await scraper.start()

    print("=" * 60)
    print("🔐 Тест авторизации...")
    print("=" * 60)
    login_ok = await ensure_netology_login(scraper.page)
    if not login_ok:
        print("❌ Авторизация провалена")
        await scraper.stop()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🔍 Тест сбора дисциплин...")
    print("=" * 60)
    program_title, disciplines = await scraper.get_program_disciplines(PROGRAM_ID)
    print(f"\n📚 Программа: {program_title}")
    print(f"   Разделов найдено: {len(disciplines)}")

    if disciplines:
        print("\n✅ Дисциплины найдены:")
        for d in disciplines[:5]:
            status = "🔒" if d["locked"] else "✅"
            print(f"  {status} {d['title']}")
        if len(disciplines) > 5:
            print(f"   ... и ещё {len(disciplines) - 5}")
    else:
        print("\n❌ Дисциплины НЕ найдены")

    await scraper.save_cookies()
    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
