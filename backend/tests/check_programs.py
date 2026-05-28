import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary", "summary_programs"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login
from dotenv import load_dotenv

load_dotenv()

PROGRAMS = [
    "bhebfad-25-memeo-2",
    "bhebfad-25-et-2",
    "bhebfad-25-ieu-2",
    "bhebfad-25-pol-2",
]


async def main():
    scraper = NetologyScraper(headless=True)
    await scraper.start()

    login_ok = await ensure_netology_login(scraper.page, "bhebfad-25")
    if not login_ok:
        print("❌ Не удалось авторизоваться")
        await scraper.stop()
        return

    for prog_id in PROGRAMS:
        url = f"https://netology.ru/profile/program/{prog_id}/schedule"
        ok = await scraper._safe_goto(url, wait_until="domcontentloaded", timeout=30000)
        if not ok:
            print(f"{prog_id}: ❌ не загрузилась")
            continue
        await asyncio.sleep(3)

        title = await scraper.page.evaluate("""
        () => {
            const el = document.querySelector('[data-testid="program-header"]');
            return el ? el.textContent.trim() : document.title;
        }
        """)
        print(f"{prog_id}: {title}")

    await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
