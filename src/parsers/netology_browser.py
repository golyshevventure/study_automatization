import asyncio
import os
import json
from playwright.async_api import async_playwright

COOKIES_FILE = "data/netology_cookies.json"

async def main():
    async with async_playwright() as p:
        # Изолированный профиль — браузер "чистый", только для агента
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"  # для WSL
            ]
        )
        
        context = await browser.new_context()
        
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
            print("🍪 Cookies загружены")
        
        page = await context.new_page()
        print("🌐 Открываю Нетологию...")
        await page.goto("https://netology.ru")
        
        print("\n" + "="*50)
        print("ИНСТРУКЦИЯ:")
        print("1. Залогиньтесь на сайте вручную")
        print("2. Перейдите на программу 'Финансы и анализ данных'")
        print("3. Откройте первую лекцию")
        print("4. Вернитесь в терминал и нажмите Enter")
        print("="*50)
        input("\nНажмите Enter после логина...")
        
        cookies = await context.cookies()
        os.makedirs("data", exist_ok=True)
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)
        print("🍪 Cookies сохранены")
        
        html = await page.content()
        with open("data/netology_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("💾 HTML сохранён в data/netology_page.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
