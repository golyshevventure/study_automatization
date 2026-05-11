import asyncio
import os
import json
from playwright.async_api import async_playwright

COOKIES_FILE = "data/netology_cookies.json"
DEBUG_DIR = "data/html_debug"

async def save_html(page, name):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    html = await page.content()
    path = os.path.join(DEBUG_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"💾 Сохранено: {path}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = await browser.new_context()
        
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
            print("🍪 Cookies загружены")
        
        page = await context.new_page()
        
        # 1. Программа (список дисциплин)
        print("🌐 Открываю страницу программы...")
        await page.goto("https://netology.ru/profile/program/bhebfad-25-vvs-2/schedule")
        await page.wait_for_timeout(3000)
        await save_html(page, "program_schedule")
        
        print("\n" + "="*60)
        print("ШАГ 1: На экране список дисциплин.")
        print("Нажмите Enter, когда страница загрузится...")
        input()
        
        # 2. Дисциплина (силлабус + темы)
        print("\n👉 Теперь откройте ЛЮБУЮ дисциплину (кликните на неё).")
        print("Дождитесь загрузки и нажмите Enter...")
        input()
        await save_html(page, "discipline_overview")
        
        # 3. Вебинар/лекция
        print("\n👉 Теперь откройте ЛЮБОЙ вебинар или лекцию внутри дисциплины.")
        print("Дождитесь загрузки и нажмите Enter...")
        input()
        await save_html(page, "webinar_page")
        
        # 4. Материалы к вебинару (если есть вкладка/ссылка)
        print("\n👉 Если есть презентации/материалы — откройте их.")
        print("Или просто нажмите Enter для завершения...")
        input()
        await save_html(page, "materials_page")
        
        print("\n✅ Все HTML сохранены в data/html_debug/")
        print("Скиньте эту папку — я напишу парсер.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
