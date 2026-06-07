---
name: react-patterns
description: React composition patterns for building flexible, maintainable components in the StudyCore frontend. Use when refactoring components with boolean prop proliferation, building reusable UI, designing component APIs, or reviewing React architecture. Covers compound components, context providers, state lifting, and composition over configuration. Do NOT use for general React performance optimization.
---

# React Composition Patterns

Composition patterns for building flexible, maintainable React components. Avoid boolean prop proliferation by using compound components, lifting state, and composing internals.

## When to Apply

- Refactoring components with many boolean props
- Building reusable component libraries
- Designing flexible component APIs
- Reviewing component architecture
- Working with compound components or context providers

## 1. Component Architecture (HIGH)

### Avoid Boolean Props

Don't add boolean props to customize behavior; use composition instead.

```tsx
// ❌ Boolean prop proliferation
<Button primary large disabled loading />

// ✅ Composition
<Button size="large" variant="primary" disabled>
  {isLoading ? <Spinner /> : "Submit"}
</Button>
```

### Compound Components

Structure complex components with shared context.

```tsx
// ✅ Compound pattern
<Modal>
  <Modal.Header>Title</Modal.Header>
  <Modal.Body>Content</Modal.Body>
  <Modal.Footer>
    <Button>Close</Button>
  </Modal.Footer>
</Modal>
```

## 2. State Management (MEDIUM)

### Decouple Implementation

Provider is the only place that knows how state is managed.

```tsx
// ✅ State inside provider, consumers use hooks
function useDeadlines() {
  const context = useContext(DeadlinesContext);
  if (!context) throw new Error("useDeadlines must be inside Provider");
  return context;
}
```

### Lift State

Move state into provider components for sibling access.

```tsx
// ✅ Lifted state in DeadlinesProvider
// Components use useDeadlines() instead of prop drilling
```

## 3. Implementation Patterns (MEDIUM)

### Explicit Variants

Create explicit variant components instead of boolean modes.

```tsx
// ❌ One component with many modes
<Card type="deadline" | "lesson" | "exam" />

// ✅ Separate components with shared base
<BaseCard>
  <DeadlineCard />
  <LessonCard />
  <ExamCard />
</BaseCard>
```

### Children Over Render Props

Use children for composition instead of renderX props.

```tsx
// ❌ Render prop
<DataGrid renderRow={(row) => <Row data={row} />} />

// ✅ Children
<DataGrid>
  {rows.map(row => <Row key={row.id} data={row} />)}
</DataGrid>
```

## 4. React 18+ APIs

- `useId()` for stable IDs in forms and accessibility.
- `useTransition()` for non-urgent state updates (filters, search).
- `useDeferredValue()` for deferring re-renders of slow components.
- `startTransition()` to mark state updates as transition.
