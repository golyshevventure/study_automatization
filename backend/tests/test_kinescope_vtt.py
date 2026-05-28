import asyncio
import json
from playwright.async_api import async_playwright


async def main():
    # URL видео из лекции (из твоего лога)
    url = "https://kinescope.io/dyr5LLMquSzqHY4L34hcGd"
    vtt_urls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        page = await browser.new_page()

        async def handle_route(route, request):
            req_url = request.url
            if ".vtt" in req_url or "subtitle" in req_url:
                vtt_urls.append(req_url)
                print(f"🎯 Найден VTT: {req_url}")
            await route.continue_()

        await page.route("**/*", handle_route)

        print(f"🌐 Открываю Kinescope: {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)

        print("⏳ Ждём 5 сек...")
        await asyncio.sleep(5)

        print(f"\n📊 Всего VTT найдено: {len(vtt_urls)}")
        for u in vtt_urls:
            print(f"   {u}")

        # Если нашли — сохраняем
        if vtt_urls:
            with open("data/vtt_lecture_urls.json", "w") as f:
                json.dump(vtt_urls, f, ensure_ascii=False, indent=2)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
