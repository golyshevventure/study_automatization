---
name: security-best-practices
description: Language and framework specific security best practices for StudyCore. Covers Python (FastAPI) and JavaScript/TypeScript (React) secure-by-default coding, vulnerability detection, and security reviews. Use when writing new code, reviewing existing code, or when asked for a security audit. Do NOT use for general code review, debugging, or threat modeling.
---

# Security Best Practices

Secure-by-default coding for StudyCore's technology stack.

## Workflow

1. **Identify stack:** Determine if working on backend (FastAPI) or frontend (React).
2. **Load references:** Read the relevant reference file:
   - FastAPI backend: `references/python-fastapi-security.md`
   - React frontend: `references/javascript-react-security.md`
3. **Apply:** Follow MUST/SHOULD requirements when writing code.
4. **Passive review:** Notice security issues in touched code and mention them.
5. **Active audit:** When asked to "scan" or "audit", systematically search for violations.

## Report Format

When producing a security report:

```markdown
# Security Audit Report

## Executive Summary
Brief overview of findings.

## Critical
| ID | Finding | File | Line | Fix |
|----|---------|------|------|-----|
| 1 | Description | path.py | 42 | Use parameterized query |

## High
...

## Medium
...

## Low
...
```

## Overrides

If project-specific reasons require bypassing a security practice, document the override in code comments or project docs. Do not fight the user on this, but explain the risk.
