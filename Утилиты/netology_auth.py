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
    """
    Авторизация в Нетологии.
    Если cookies живы — возвращает True.
    Если нет — открывает страницу входа и просит пользователя зайти вручную
    (капча блокирует автоматический ввод).
    """
    # Проверяем текущее состояние
    await page.goto("https://netology.ru/profile", wait_until="domcontentloaded", timeout=15000)
    await asyncio.sleep(2)

    if not await _needs_auth(page):
        print("✅ Уже авторизованы")
        return True

    print("=" * 60)
    print("🔒 Требуется авторизация в Нетологии")
    print("=" * 60)
    print("Открыл страницу входа в браузере.")
    print("Действия:")
    print("  1. Нажми 'Авторизоваться'")
    print("  2. Выбери удобный способ (включая 'Другие способы входа' → 'Войти по почте')")
    print("  3. Пройди капчу и войди")
    print("  4. Когда увидишь свой профиль — нажми Enter здесь")
    print("=" * 60)

    # Открываем страницу входа в видимом браузере
    await page.goto("https://netology.ru/profile?modal=sign_in", wait_until="domcontentloaded", timeout=15000)

    # Ждём ручного входа
    input("⏎ Нажми Enter после успешного входа...")
    await asyncio.sleep(2)

    # Проверяем, авторизовались ли
    await page.goto("https://netology.ru/profile", wait_until="domcontentloaded", timeout=15000)
    await asyncio.sleep(2)

    if await _needs_auth(page):
        print("❌ Авторизация не подтверждена. Попробуй снова.")
        return False

    print("✅ Авторизация подтверждена")
    return True
