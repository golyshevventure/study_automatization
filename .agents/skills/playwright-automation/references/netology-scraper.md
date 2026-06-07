# Netology Scraper Patterns

## Login Flow

```python
async def ensure_auth(page, cookies_path="backend/netology_cookies/netology_cookies.json"):
    """Ensure authenticated session. Returns True if auth successful."""
    with open(cookies_path) as f:
        cookies = json.load(f)
    await page.context.add_cookies(cookies)
    
    await page.goto("https://netology.ru/profile")
    
    # Check if still on login page
    if "login" in page.url:
        raise AuthError("Session expired. Manual re-auth required.")
    
    return True
```

## Schedule Extraction

```python
async def extract_schedule(page, program_id: int) -> list[dict]:
    url = f"https://netology.ru/profile/programs/{program_id}/schedule"
    await page.goto(url)
    
    # Wait for schedule to load
    await page.wait_for_selector(".schedule-list", timeout=10000)
    
    items = await page.query_selector_all(".schedule-item")
    results = []
    
    for item in items:
        data = {
            "title": await get_text(item, ".schedule-item__title"),
            "date": await get_text(item, ".schedule-item__date"),
            "type": await get_attribute(item, ".schedule-item__type", "data-type"),
            "status": await get_text(item, ".schedule-item__status"),
        }
        results.append(data)
    
    return results

async def get_text(element, selector: str) -> str:
    el = await element.query_selector(selector)
    return await el.text_content() if el else ""

async def get_attribute(element, selector: str, attr: str) -> str:
    el = await element.query_selector(selector)
    return await el.get_attribute(attr) if el else ""
```

## Discipline List

```python
async def extract_disciplines(page, program_id: int) -> list[dict]:
    url = f"https://netology.ru/profile/programs/{program_id}"
    await page.goto(url)
    
    await page.wait_for_selector(".discipline-list")
    
    items = await page.query_selector_all(".discipline-item")
    return [{
        "id": await item.get_attribute("data-id"),
        "title": await get_text(item, ".discipline-title"),
    } for item in items]
```

## Debug Helpers

```python
async def save_debug_state(page, prefix: str):
    """Save HTML and screenshot for debugging."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    html = await page.content()
    with open(f"data/html_debug/{prefix}_{timestamp}.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    await page.screenshot(
        path=f"data/html_debug/{prefix}_{timestamp}.png",
        full_page=True
    )
```

## Common Selectors

| Element | Selector |
|---------|----------|
| Login form | `#login-form` |
| Profile menu | `.profile-menu` |
| Program list | `.program-list-item` |
| Schedule container | `.schedule-list` |
| Schedule item | `.schedule-item` |
| Discipline list | `.discipline-list` |
| Lesson card | `.lesson-card` |
| Modal dialog | `.modal-content` |

## Rate Limiting

```python
async def safe_goto(page, url: str, delay_ms: int = 1000):
    """Navigate with rate limiting."""
    await page.wait_for_timeout(delay_ms)
    await page.goto(url)
```
