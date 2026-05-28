import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "summary"))

from netology_scraper import NetologyScraper


async def main():
    scraper = NetologyScraper()
    await scraper.start()

    print("=" * 60)
    print("🔍 Ручной сбор HTML авторизации")
    print("=" * 60)
    print("1. Откроется браузер на /profile?modal=sign_in")
    print("2. Нажми в браузере кнопки для входа (как обычно)")
    print("3. После КАЖДОГО клика жми Enter в этом терминале")
    print("4. Я сохраню HTML каждого шага в data/debug_step_*.html")
    print("=" * 60)

    await scraper._safe_goto("https://netology.ru/profile?modal=sign_in")
    await asyncio.sleep(2)

    step = 1
    while True:
        html = await scraper.page.content()
        url = scraper.page.url
        path = f"data/debug_step_{step}_{url.replace('https://', '').replace('/', '_').replace('?', '_')[:60]}.html"
        os.makedirs("data", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n💾 Шаг {step} сохранён: {path}")
        print(f"   URL: {url}")

        user_input = input("⏎ Нажми Enter для сохранения следующего шага (или 'q' для выхода): ")
        if user_input.strip().lower() == "q":
            break
        step += 1
        await asyncio.sleep(1)

    await scraper.stop()
    print("\n🏁 Готово. Все HTML-дампы в data/")


if __name__ == "__main__":
    asyncio.run(main())
