---
name: studycore-netology-api
description: Netology platform API integration patterns for StudyCore. Covers authentication flow (cookies, CSRF), key endpoints (schedule, calendar, professions), rate limiting, error handling, and data models. Use when implementing sync services, scraping logic, or API clients for Netology. Do NOT use for general HTTP patterns (use coding-principles) or Playwright automation (use playwright-automation).
---

# StudyCore Netology API

Integration patterns for the Netology educational platform API.

## Authentication Flow

Netology uses session-based auth with CSRF protection.

### Step 1: Load Cookies
- Read stored cookies from `backend/netology_cookies/netology_cookies.json`.
- Cookies include `sessionid`, `csrf_token`, and other Netology session cookies.

### Step 2: Validate Session
- Make authenticated request to a lightweight endpoint (e.g., user profile).
- If 401/403: session expired, need re-auth (manual login via browser).

### Step 3: CSRF Token
- Extract CSRF token from cookies or page HTML.
- Include `X-CSRF-Token` header in POST/PUT/DELETE requests.

### Step 4: Request Pattern
```python
async with aiohttp.ClientSession(cookies=cookies) as session:
    headers = {"X-CSRF-Token": csrf_token, "Referer": "https://netology.ru/"}
    async with session.get(url, headers=headers) as response:
        data = await response.json()
```

## Key Endpoints

### User Profile
```
GET https://api.netology.ru/backend/api/user/profile
```
- Validates auth session.
- Returns user info, enrolled programs.

### Professions / Programs
```
GET https://api.netology.ru/backend/api/user/professions
```
- Lists all enrolled programs.
- Each program has `id`, `title`, `status`.

### Schedule
```
GET https://api.netology.ru/backend/api/user/professions/{profession_id}/schedule
```
- Returns lessons, works, exams for the program.
- Response: list of schedule items with `date`, `type`, `title`, `status`.

### Calendar
```
GET https://api.netology.ru/backend/api/user/calendar
```
- Alternative source for deadline events.
- May contain events not in schedule.

## Data Models

### Schedule Item Types
| Type | Description | Event Category |
|------|-------------|----------------|
| `lesson` | Video lesson / lecture | lessons |
| `consultation` | Group consultation | lessons |
| `work` | Homework / practice | works |
| `test` | Online test / quiz | works |
| `exam` | Final exam | control |
| `credit` | Pass/fail assessment | control |

### Event Status
| Status | Meaning |
|--------|---------|
| `active` | Upcoming, not started |
| `in_progress` | Started, not completed |
| `completed` | Done |
| `missed` | Deadline passed |

## Rate Limiting & Resilience

- **Backoff:** Use exponential backoff on 429 Too Many Requests.
- **Retry:** Max 3 retries for transient failures (5xx, timeout).
- **Batching:** Fetch schedules for multiple programs sequentially, not in parallel (avoid rate limiting).
- **Caching:** Cache API responses in PostgreSQL. Don't hit API on every page load.

## Error Handling

| Error | Action |
|-------|--------|
| 401 Unauthorized | Log auth failure, flag for re-auth |
| 403 Forbidden | CSRF token missing/invalid, refresh token |
| 429 Too Many Requests | Backoff and retry |
| 5xx Server Error | Retry with backoff, max 3 attempts |
| Timeout | Retry once, then fail gracefully |

## Sync Strategy

1. **Full sync:** Delete old events → fetch all programs → fetch each schedule → merge → insert.
2. **Incremental sync:** Compare last sync timestamp, fetch only changed items (if API supports).
3. **Fallback:** If API returns empty, try calendar endpoint as secondary source.

## Grouping Logic

Events are grouped by `(lesson_id, event_type, normalized_title)` to deduplicate:
- Multiple exam dates → one card with "2 варианта" badge.
- Passed events → green badge "Выполнено".
