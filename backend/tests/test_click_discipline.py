import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))

from netology_scraper import NetologyScraper


async def main():
    scraper = NetologyScraper()
    await scraper.start()

    print("Открываю страницу программы...")
    await scraper._safe_goto("https://netology.ru/profile/program/bhebfad-25/schedule/all")
    await asyncio.sleep(3)

    print("Кликаю 'Безопасность жизнедеятельности'...")
    try:
        await scraper.page.click("text=Безопасность жизнедеятельности", timeout=5000)
        await asyncio.sleep(3)
        url = scraper.page.url
        print(f"\n✅ Текущий URL после клика: {url}")

        # Save HTML
        html = await scraper.page.content()
        with open("data/debug_after_click_bjd.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("💾 HTML сохранён: data/debug_after_click_bjd.html")
    except Exception as e:
        print(f"❌ Ошибка клика: {e}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
