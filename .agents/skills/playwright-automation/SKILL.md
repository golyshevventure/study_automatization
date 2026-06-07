---
name: playwright-automation
description: Browser automation with Playwright for StudyCore. Covers authentication, navigation, data extraction, and HTML debugging for the Netology platform. Use when implementing scrapers, debugging auth issues, extracting data not available via API, or validating page structure. Do NOT use for general API calls (use studycore-netology-api) or non-browser automation.
---

# Playwright Automation

Browser automation for scraping and debugging the Netology platform.

## When to Use

- Data not available via API (rare pages, dynamic content).
- Debugging auth flow or page structure.
- Validating HTML structure after UI changes.
- Extracting data from JavaScript-rendered pages.

## Setup

```bash
npm install playwright
npx playwright install chromium
```

## Auth Flow

1. **Load cookies** from stored session:
```python
import json
from playwright.async_api import async_playwright

with open("backend/netology_cookies/netology_cookies.json") as f:
    cookies = json.load(f)

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context()
    await context.add_cookies(cookies)
```

2. **Navigate to protected page** and verify auth:
```python
page = await context.new_page()
await page.goto("https://netology.ru/profile")
# Check if redirected to login → auth failed
```

3. **Handle CSRF** if needed:
```python
csrf_token = await page.evaluate("() => document.querySelector('meta[name=csrf-token]')?.content")
```

## Data Extraction

### Schedule Page

```python
await page.goto(f"https://netology.ru/profile/programs/{program_id}/schedule")

# Wait for content
await page.wait_for_selector("[data-testid='schedule-item']")

# Extract data
items = await page.query_selector_all("[data-testid='schedule-item']")
for item in items:
    title = await item.query_selector_eval(".title", "el => el.textContent")
    date = await item.query_selector_eval(".date", "el => el.textContent")
```

### Debug HTML

```python
# Save HTML for debugging
html = await page.content()
with open(f"data/html_debug/debug_{page_name}.html", "w", encoding="utf-8") as f:
    f.write(html)
```

## Best Practices

- **Headless by default:** Use `headless=True` for production scraping.
- **Rate limiting:** Add delays between requests (`page.wait_for_timeout(1000)`).
- **Error handling:** Wrap in try/except, save screenshot on failure.
- **Cleanup:** Always close browser context.

```python
try:
    await page.goto(url)
except Exception as e:
    await page.screenshot(path=f"data/html_debug/error_{timestamp}.png")
    raise
finally:
    await context.close()
    await browser.close()
```

## Fallback Strategy

1. Try API first (faster, more reliable).
2. If API returns incomplete data → use Playwright.
3. Save extracted data to JSON for caching.
4. Log all extraction attempts.

Load `references/netology-scraper.md` for specific Netology scraping patterns.
