import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))

from netology_scraper import NetologyScraper


async def main():
    scraper = NetologyScraper()
    await scraper.start()

    urls = [
        "https://netology.ru/profile/program/bhebfad-25/schedule/all",
        "https://netology.ru/profile/program/bhebfad-25/schedule",
    ]

    for url in urls:
        print(f"\n{'='*60}")
        print(f"🌐 {url}")
        print("=" * 60)
        ok = await scraper._safe_goto(url)
        if not ok:
            print("❌ Страница не открылась")
            continue
        await asyncio.sleep(3)

        html = await scraper.page.content()
        debug_path = f"data/debug_schedule_{url.split('/')[-1]}.html"
        os.makedirs("data", exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"💾 HTML: {debug_path}")

        # Check for discipline titles
        has_bjd = "Безопасность" in html
        has_eco = "Экономика" in html or "эконом" in html.lower()
        has_intro = "Введение в специальность" in html
        print(f"   Безопасность: {has_bjd}")
        print(f"   Экономика: {has_eco}")
        print(f"   Введение: {has_intro}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
