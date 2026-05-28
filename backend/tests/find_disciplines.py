import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary", "summary_programs"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv

load_dotenv()


async def main():
    scraper = NetologyScraper(headless=True)
    await scraper.start()

    login_ok = await ensure_netology_login(scraper.page, "bhebfad-25")
    if not login_ok:
        print("❌ Не удалось авторизоваться")
        await scraper.stop()
        return

    # Попробуем разные URL
    urls = [
        "https://netology.ru/profile/program/bhebfad-25/schedule/all",
        "https://netology.ru/profile/program/bhebfad-25/schedule",
    ]

    for url in urls:
        print(f"\n🌐 {url}")
        ok = await scraper._safe_goto(url, wait_until="domcontentloaded", timeout=60000)
        if not ok:
            print("  ❌ Не загрузилась")
            continue

        await asyncio.sleep(5)

        html = await scraper.page.content()
        with open(f"data/debug_{url.split('/')[-1]}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  💾 HTML сохранён")

        # Попробуем найти любые ссылки на дисциплины
        links = await scraper.page.evaluate("""
        () => {
            const results = [];
            document.querySelectorAll('a[href*="/lessons/"]').forEach(a => {
                results.push({text: a.textContent.trim(), href: a.getAttribute('href')});
            });
            return results;
        }
        """)
        print(f"  Найдено ссылок на lessons: {len(links)}")
        for link in links[:20]:
            print(f"    {link['text'][:60]} -> {link['href']}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
