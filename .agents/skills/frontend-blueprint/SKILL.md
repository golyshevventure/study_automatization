---
name: frontend-blueprint
description: Frontend architecture and component design patterns for StudyCore. Covers component structure, state management with React Query, Tailwind conventions, API integration, and atomic component design. Use when building new pages, designing components, refactoring frontend architecture, or improving UI patterns. Do NOT use for backend logic or database design.
---

# Frontend Blueprint

Frontend architecture and design patterns for the StudyCore React + TypeScript + Tailwind application.

## Component Structure

```
frontend/src/
├── pages/           # Route-level pages (coarse, data-fetching)
├── components/      # Reusable UI components (fine, presentational)
├── hooks/           # Custom React hooks (data, logic, side effects)
├── api/             # API client functions
├── types/           # TypeScript interfaces and types
└── lib/             # Utilities, helpers, constants
```

### Rules
- **Pages:** Coarse components that handle routing and data fetching. Keep thin.
- **Components:** Fine-grained, presentational. Receive data via props. No direct API calls.
- **Hooks:** Encapsulate data fetching, mutations, and complex logic. Return typed state and actions.

## State Management

### Server State → React Query

```typescript
// ✅ Use React Query for server state
const { data, isLoading } = useQuery({
  queryKey: ["deadlines", filter],
  queryFn: () => getDeadlines(filter),
})

// ✅ Use useMutation for mutations
const { mutate } = useMutation({
  mutationFn: syncDeadlines,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["deadlines"] }),
})
```

### Client State → React Context

```typescript
// ✅ Use Context for global client state (theme, auth, sidebar)
// ✅ Use useState for local component state
// ❌ Don't use Context for frequently changing state
```

### Rules
- Server state ALWAYS goes to React Query.
- Don't duplicate server state in Context or useState.
- Cache invalidation is key: invalidate queries after mutations.

## API Integration

### API Client Pattern

```typescript
// api/deadlines.ts
export async function getDeadlines(filter: string, limit: number, offset: number) {
  const response = await fetch(`/api/deadlines?filter=${filter}&limit=${limit}&offset=${offset}`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json() as Promise<DeadlineListResponse>
}
```

### Error Handling

```typescript
// ✅ Centralized error handling in hooks
export function useDeadlines(filter: string) {
  return useQuery({
    queryKey: ["deadlines", filter],
    queryFn: () => getDeadlines(filter),
    retry: 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
```

## Tailwind Conventions

### Utility-First

```tsx
// ✅ Utility classes directly on elements
<div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow">

// ❌ Don't create one-off component classes in CSS files
```

### Common Patterns

| Pattern | Classes |
|---------|---------|
| Card | `bg-white rounded-lg shadow p-4` |
| Button (primary) | `px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700` |
| Button (secondary) | `px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300` |
| Layout container | `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8` |
| Flex row | `flex items-center gap-2` |
| Flex column | `flex flex-col gap-2` |

### Responsive

```tsx
// Mobile-first
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

## Component Design

### Props Interface

```tsx
// ✅ Explicit props interface
interface DeadlineCardProps {
  event: DeadlineEvent
  onClick?: (id: string) => void
}

export function DeadlineCard({ event, onClick }: DeadlineCardProps) {
  ...
}
```

### Composition Over Configuration

```tsx
// ✅ Composition
<Card>
  <CardHeader title={event.title} />
  <CardBody>{event.description}</CardBody>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>

// ❌ Boolean props
<Card title={event.title} description={event.description} showFooter hasAction />
```

## Loading & Error States

```tsx
// ✅ Consistent loading/error patterns
if (isLoading) return <Skeleton count={5} />
if (error) return <ErrorMessage error={error} retry={refetch} />
if (!data?.length) return <EmptyState message="No deadlines found" />
```
