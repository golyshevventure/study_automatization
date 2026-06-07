# FastAPI Security Spec (Compact)

Security requirements for FastAPI backend in StudyCore.

## 0) Boundaries

- MUST NOT commit secrets (API keys, DB URLs with credentials, session cookies).
- MUST NOT log secrets or user passwords.
- MUST NOT disable protections to "make it work" (permissive CORS, skipping validation).
- MUST provide evidence-based findings during audits: cite file paths and code snippets.

## 1) CORS

```python
# ❌ NEVER
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Dangerous combination
)

# ✅ SAFE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],  # Exact frontend origin
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
```

## 2) Input Validation

- MUST validate ALL input with Pydantic models.
- MUST use strict types. Avoid `dict`, `Any`, `list[Any]`.
- MUST validate path/query params with constraints (`ge=0`, `le=500`).

```python
# ✅
class DeadlineSyncRequest(BaseModel):
    program_id: int = Field(gt=0)
    force: bool = False

# ❌
@app.post("/sync")
async def sync(body: dict):  # No validation
```

## 3) SQL Injection Prevention

- MUST use SQLAlchemy 2.0 ORM or parameterized queries.
- MUST NOT use f-strings or string concatenation for SQL.

```python
# ✅
result = await db.execute(select(DeadlineEvent).where(DeadlineEvent.user_id == user_id))

# ❌
await db.execute(f"SELECT * FROM deadline_events WHERE user_id = {user_id}")
```

## 4) Authentication

- MUST use FastAPI dependency injection for auth checks.
- MUST validate session/token on every protected endpoint.
- MUST return 401 for missing auth, 403 for insufficient permissions.

```python
# ✅
async def get_current_user(token: str = Header(...)) -> User:
    user = await validate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@app.get("/deadlines")
async def list_deadlines(user: User = Depends(get_current_user)):
    ...
```

## 5) Error Handling

- MUST NOT leak stack traces or internal paths to clients.
- MUST log full errors server-side.
- MUST return generic messages to clients.

```python
# ✅
except Exception as e:
    logger.exception("Database error in list_deadlines")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## 6) File Handling

- MUST validate file extensions against allowlist.
- MUST limit file size.
- MUST NOT serve user-uploaded files from predictable paths.

```python
# ✅
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
    raise HTTPException(400, "Invalid file type")
```

## 7) SSRF Prevention

- MUST validate outbound URLs against allowlist.
- MUST NOT fetch URLs from user input without validation.

```python
# ✅
ALLOWED_HOSTS = {"api.netology.ru", "netology.ru"}
parsed = urlparse(url)
if parsed.hostname not in ALLOWED_HOSTS:
    raise HTTPException(400, "Invalid URL")
```

## 8) Dependencies

- Run `pip audit` or `safety check` regularly.
- Keep dependencies updated.
- Pin versions in `requirements.txt` or `pyproject.toml`.
