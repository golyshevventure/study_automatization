#!/usr/bin/env python3
import asyncio
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "Скрейперы"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Утилиты"))

from netology_scraper import NetologyScraper
from netology_auth import ensure_netology_login


async def main():
    scraper = NetologyScraper(headless=True)
    await scraper.start()
    login_ok = await ensure_netology_login(scraper.page, "bhebfad-25-memeo-2")
    if not login_ok:
        print("Auth failed")
        return
    url = "https://netology.ru/profile"
    await scraper._safe_goto(url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(3)
    programs = await scraper.page.evaluate("""
    () => {
        const results = [];
        const seen = new Set();
        document.querySelectorAll('a[href*="/profile/program/"]').forEach(a => {
            const href = a.getAttribute('href');
            const m = href.match(/program\\/([^\\/?#]+)/);
            if (!m) return;
            const pid = m[1];
            if (seen.has(pid)) return;
            seen.add(pid);
            let title = '';
            const h = a.querySelector('h3, h2, h1, [class*="title"], [class*="name"]');
            if (h) title = h.textContent.trim();
            if (!title) title = a.textContent.trim().split('\\n')[0].trim();
            results.push({title, program_id: pid, href});
        });
        return results;
    }
    """)
    for p in programs:
        print(f"{p['title']} -> {p['program_id']}")
    await scraper.save_cookies()
    await scraper.stop()


asyncio.run(main())
