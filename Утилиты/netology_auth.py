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


async def ensure_netology_login(page, program_id=None):
    """
    Авторизация в Нетологии.
    Если cookies живы — возвращает True.
    Если нет — открывает страницу входа и ждёт ручной авторизации
    (капча блокирует автоматический ввод).
    """
    # Проверяем авторизацию на рабочей странице программы (быстрее и надёжнее)
    check_url = (
        f"https://netology.ru/profile/program/{program_id}/schedule"
        if program_id
        else "https://netology.ru/profile"
    )
    try:
        await page.goto(check_url, wait_until="domcontentloaded", timeout=60000)
    except Exception:
        # Если даже domcontentloaded не сработал, пробуем commit
        try:
            await page.goto(check_url, wait_until="commit", timeout=30000)
        except Exception:
            pass
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
    print("  4. Я сам подхвачу, когда профиль загрузится")
    print("=" * 60)

    # Открываем страницу входа в видимом браузере
    await page.goto(
        "https://netology.ru/profile?modal=sign_in", wait_until="domcontentloaded", timeout=60000
    )

    # Ждём ручного входа: проверяем каждые 3 секунды, не более 5 минут
    max_wait = 300  # 5 минут
    elapsed = 0
    while True:
        try:
            needs = await _needs_auth(page)
        except Exception:
            # Страница перезагружается (навигация) — пропускаем проверку
            needs = True
        if not needs:
            break
        await asyncio.sleep(3)
        elapsed += 3
        if elapsed % 15 == 0:
            print(f"   ⏳ Жду авторизации... ({elapsed} сек)")
        if elapsed >= max_wait:
            print("❌ Таймаут ожидания авторизации (5 минут)")
            return False

    print("✅ Авторизация подтверждена")
    return True
