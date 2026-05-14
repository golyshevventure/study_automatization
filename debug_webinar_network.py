# debug_webinar_network.py
import asyncio
import json
import os
from playwright.async_api import async_playwright

COOKIES_FILE = "data/netology_cookies.json"
DEBUG_DIR = "data/html_debug"

async def safe_goto(page, url, timeout=60000):
    """Fallback: networkidle → domcontentloaded → load"""
    for wait_until in ["networkidle", "domcontentloaded", "load"]:
        try:
            print(f"   Пробуем wait_until='{wait_until}'...")
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            print(f"   ✅ Успех с '{wait_until}'")
            return True
        except Exception as e:
            print(f"   ❌ Не удалось: {str(e)[:80]}")
    return False

async def main():
    url = input("Вставь URL страницы вебинара: ").strip()
    
    os.makedirs(DEBUG_DIR, exist_ok=True)
    requests_log = []

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

        # Перехват запросов
        async def handle_route(route, request):
            req_info = {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
            }
            requests_log.append(req_info)
            await route.continue_()

        await page.route("**/*", handle_route)

        print(f"\n🌐 Открываю: {url}")
        ok = await safe_goto(page, url)
        if not ok:
            print("❌ Страница не открылась совсем. Сохраняю то, что есть...")
        else:
            await asyncio.sleep(5)
            print("⏳ Ждём загрузку плеера...")

        # Сохраняем HTML в любом случае
        try:
            html = await page.content()
            html_path = os.path.join(DEBUG_DIR, "webinar_raw.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"💾 HTML сохранён: {html_path} ({len(html)} символов)")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить HTML: {e}")

        # Сохраняем лог запросов
        log_path = os.path.join(DEBUG_DIR, "webinar_network.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(requests_log, f, ensure_ascii=False, indent=2)
        print(f"💾 Network-лог сохранён: {log_path} ({len(requests_log)} запросов)")

        # Ищем video/iframe
        try:
            media = await page.evaluate("""() => {
                const v = document.querySelector('video');
                if (v && v.src) return {type: 'video', src: v.src};
                const ifr = document.querySelector('iframe');
                if (ifr && ifr.src) return {type: 'iframe', src: ifr.src};
                const scripts = [...document.querySelectorAll('script')].map(s => s.textContent);
                return {type: 'none', scripts: scripts.filter(s => s.includes('video') || s.includes('player') || s.includes('webinar')).slice(0,3)};
            }""")
            print(f"🔍 Медиа в DOM: {json.dumps(media, ensure_ascii=False, indent=2)[:500]}")
        except Exception as e:
            print(f"⚠️ Не удалось просканировать DOM: {e}")

        await browser.close()
        print("\n✅ Готово. Пришли файлы из data/html_debug/")

if __name__ == "__main__":
    asyncio.run(main())