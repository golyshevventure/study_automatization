import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))

from netology_scraper import NetologyScraper

async def main():
    scraper = NetologyScraper()
    await scraper.start()

    urls = [
        "https://netology.ru/profile?modal=sign_in",
        "https://netology.ru/login",
        "https://netology.ru/users/sign_in",
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
        debug_path = f"data/debug_login_{url.split('/')[-1].replace('?', '_')}.html"
        os.makedirs("data", exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"💾 HTML: {debug_path}")

        has_email = 'type="email"' in html or 'type=\'email\'' in html
        has_password = 'type="password"' in html or 'type=\'password\'' in html
        has_voyti = 'Войти по почте' in html
        print(f"   email input: {has_email}")
        print(f"   password input: {has_password}")
        print(f"   'Войти по почте': {has_voyti}")

    await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())
