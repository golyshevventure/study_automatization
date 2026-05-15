import asyncio
import os


async def _needs_auth(page):
    """Проверяет, требуется ли авторизация (URL или DOM)."""
    return await page.evaluate("""
        () => {
            const bodyText = document.body ? document.body.innerText : '';
            const url = window.location.href;
            const hasLoginUrl = url.includes('login') || url.includes('modal=sign_in');
            const hasAuthPrompt = bodyText.includes('Авторизоваться')
                || bodyText.includes('Войдите в личный кабинет');
            return hasLoginUrl || hasAuthPrompt;
        }
    """)


async def ensure_netology_login(page):
    """Авторизация в Нетологии: проверка → Авторизоваться → Войти по почте → Email/Пароль → Войти."""
    email = os.getenv("NETOLOGY_EMAIL")
    password = os.getenv("NETOLOGY_PASSWORD")
    if not email or not password:
        print("⚠️ NETOLOGY_EMAIL/NETOLOGY_PASSWORD не найдены в .env")
        return False

    # Проверяем, авторизованы ли уже (надежная проверка через DOM + URL)
    await page.goto("https://netology.ru/profile", wait_until="domcontentloaded", timeout=15000)
    await asyncio.sleep(2)

    if not await _needs_auth(page):
        print("✅ Уже авторизованы")
        return True

    print("🔒 Требуется авторизация")

    # Шаг 1: Клик «Авторизоваться"
    try:
        await page.click('button:has-text("Авторизоваться")', timeout=5000)
        await asyncio.sleep(1)
    except:
        pass

    # Шаг 2: Клик «Войти по почте"
    try:
        await page.click('button:has-text("Войти по почте")', timeout=5000)
        await asyncio.sleep(1)
    except Exception as e:
        print(f"⚠️ Не удалось найти 'Войти по почте': {e}")
        return False

    # Шаг 3: Заполнить форму
    try:
        await page.fill('input[placeholder="Email"], input[type="email"]', email, timeout=5000)
        await page.fill('input[placeholder="Пароль"], input[type="password"]', password, timeout=5000)
        await page.click('button:has-text("Войти")', timeout=5000)
        print("⏳ Авторизация...")
        await asyncio.sleep(5)

        if await _needs_auth(page):
            print("❌ Авторизация не удалась")
            return False
        print("✅ Авторизация успешна")
        return True
    except Exception as e:
        print(f"❌ Ошибка при вводе данных: {e}")
        return False
