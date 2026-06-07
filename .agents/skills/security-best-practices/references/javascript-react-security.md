# React Security Spec (Compact)

Security requirements for React frontend in StudyCore.

## 0) Boundaries

- MUST NOT commit secrets to frontend code (anything in the bundle is visible to users).
- MUST NOT trust data from APIs without validation/sanitization.
- MUST provide evidence-based findings during audits.

## 1) XSS Prevention

### dangerouslySetInnerHTML

```tsx
// ❌ NEVER with untrusted data
<div dangerouslySetInnerHTML={{ __html: data.fromApi }} />

// ✅ Only with sanitized HTML
import DOMPurify from "dompurify"
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(data.fromApi) }} />

// ✅ Prefer textContent for plain text
<div>{data.fromApi}</div>
```

### Direct DOM Access

```tsx
// ❌ NEVER
element.innerHTML = userInput

document.write(userInput)

// ✅ Safe alternatives
element.textContent = userInput
element.innerHTML = DOMPurify.sanitize(userInput)
```

## 2) URL Validation

```tsx
// ❌ javascript: protocol in href
<a href={userProvidedUrl}>Link</a>

// ✅ Validate URL scheme
function isSafeUrl(url: string): boolean {
  try {
    const parsed = new URL(url, window.location.origin)
    return parsed.protocol === "http:" || parsed.protocol === "https:"
  } catch {
    return false
  }
}

<a href={isSafeUrl(url) ? url : "#"}>Link</a>
```

## 3) Data from APIs

- Treat ALL API data as untrusted until validated.
- Don't use API data directly in `eval()`, `new Function()`, `setTimeout(string)`.
- Validate shapes with TypeScript, but remember runtime data can be anything.

```tsx
// ✅ Type guard + validation
function isDeadlineEvent(data: unknown): data is DeadlineEvent {
  return (
    typeof data === "object" &&
    data !== null &&
    "id" in data &&
    typeof (data as Record<string, unknown>).id === "string"
  )
}
```

## 4) Auth & Session

- Store tokens in `httpOnly` cookies when possible (server sets them).
- If using `localStorage` for tokens: clear on logout, validate before each request.
- Never log tokens to console.

```tsx
// ✅ Centralized API client
apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

## 5) Error Boundaries

- MUST have error boundaries to prevent UI crashes from exposing stack traces.

```tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) {
      return <FallbackUI />
    }
    return this.props.children
  }
}
```

## 6) Dependencies

- Run `npm audit` regularly.
- Keep React and dependencies updated.
- Review new dependencies before adding.

## 7) postMessage

- If using `window.postMessage`: validate `event.origin` strictly.
- Never trust message data without validation.
