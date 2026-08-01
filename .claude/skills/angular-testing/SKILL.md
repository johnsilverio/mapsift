---
name: angular-testing
description: Write unit and integration tests for Angular v22 applications using Vitest (via the @angular/build:unit-test builder) with @testing-library/angular, focusing on user-centric testing, AAA pattern, and modern Angular patterns (standalone components, signals, zoneless). Use for testing components, services, and HTTP interactions with Vitest globals and Testing Library DOM matchers.
---

# Angular Testing with Vitest

Test Angular v22 applications with Vitest (through the `@angular/build:unit-test` builder) and
@testing-library/angular, prioritizing user-centric testing over implementation details.

## The project's testing method comes first

`CLAUDE.md` (Testing and TDD) and foundation section 14 govern; this skill is the Angular idiom underneath
them. The parts that bind every test here:

- **Red, Green, Refactor in two clean-context windows.** One pass writes the failing tests as behaviour,
  another implements the minimum to green using those tests as a contract. Design happens in the refactor
  step, never while a test is red.
- **Test behaviour, not implementation.** Assert what the app guarantees (rendered DOM, returned values,
  emitted errors, the requests issued, the navigation that happened), never private shape or call order. A
  test changes only when a requirement changes.
- **Lean, no bloat.** One behaviour per test, one test per behaviour. Do not test trivial or generated code,
  third-party libraries, or unbuilt futures.
- If a behaviour can only be tested by standing up the whole app, it was factored wrong; pull the decision
  out. If it is client domain, sync or geometry logic, it belongs in `libs/core`, not in Angular.

`specs/testing.md` is the canonical method document and does not exist yet. Do not invent its content.

## Core Principles

- **User-Centric Testing:** Simulate real user behavior using `@testing-library/angular`. Avoid testing implementation details or private state.
- **Modern Angular:** Follow Angular v22 standards (standalone components, signals, `@if/@for` control flow, `OnPush` as the schematic default).
- **Zoneless:** zoneless change detection is the default since v21, so there is no `zone.js` in a new project. Prefer Testing Library's async helpers and `await fixture.whenStable()` over sprinkling `fixture.detectChanges()`, and never rely on Zone-based auto-detection to flush an update.
- **Accessibility:** Use semantic queries (getByRole, getByLabelText) that promote accessible markup.

## Framework & Syntax

### Running Tests

Run through `ng test` (the `@angular/build:unit-test` builder, whose default runner is Vitest), never the
Vitest CLI directly: only the builder wires the `tsconfig` path aliases such as `@mapsift/ui`. Watch defaults
to true in a TTY, so a single run is `ng test --watch=false`, and one file is
`--include=**/<name>.spec.ts`. Tests run in Node with jsdom unless `--browsers` opts into a real browser.

### Vitest Globals

Always use Vitest globals:
- `describe`, `it`, `expect`, `vi` (e.g., `vi.fn()`, `vi.spyOn()`)
- Import from `'vitest'` if globals are not enabled in the test config
- Never use `jasmine`, `spyOn`, `done()`, or Karma

### Testing Library DOM Matchers

Use `@testing-library/jest-dom` matchers for better assertions:

```typescript
// Good - Use jest-dom matchers
expect(button).toHaveClass('primary');
expect(text).toBeVisible();
expect(element).toHaveTextContent('Hello');
expect(button).toBeDisabled();

// Bad - Avoid direct DOM manipulation
expect(element.classList.contains('name')).toBe(true);
expect(element.style.display).toBe('none');
```

## Test Structure (AAA Pattern)

### Strict AAA Guidelines

Structure every test into **Arrange**, **Act**, and **Assert** blocks:

1. **Leave exactly one empty line** between Arrange/Act/Assert blocks
2. **Do NOT include** `// Arrange` or `// Act` or `// Assert` comments
3. **Use meaningful test titles** with active voice

### Test Naming

- Use active voice, describe what the test does
- Avoid "should" phrasing

```typescript
// Bad - Generic "should" title
it('should handle submit', () => { });

// Good - Descriptive and specific
it('prevents submission when the email field is invalid', () => { });

// Good - Clear behavior description
it('updates the profile when the save button is clicked', () => { });
```

## Component Testing Strategy

### Isolation

Each `it` block must be self-contained. Use `beforeEach` only for setup truly shared across all tests.

### Query Selection

Use Testing Library queries in order of preference:
1. `screen.getByRole()` - Most accessible and semantic
2. `screen.getByLabelText()` - For form elements
3. `screen.getByText()` - For static text content
4. `screen.getByTestId()` - Last resort only

### User Interactions

Use `userEvent` from `@testing-library/user-event` for realistic interactions instead of native DOM events.

### Public API Testing

Test only public fields and methods. Test `protected` or `private` logic only through public triggers (user interactions, input changes, public method calls).

### Business Logic Focus

Do not test Angular's built-in directives (like `@if`, `@for`). Test the component's unique inputs, outputs, and business logic.

## Mocking & Async

### Effective Mocking

Use `vi.spyOn()` or `vi.fn()` to isolate dependencies. Avoid importing heavy modules; mock services and APIs at the boundary.

### Async Handling

Use `async/await` for all promises returned by queries or events. Never leave a promise unhandled.

### Signals

Set a writable signal with `instance.someSignal.set(...)` and a signal input with
`fixture.componentRef.setInput(...)`, then let the change propagate (`await fixture.whenStable()`, or a
Testing Library query that already waits) before asserting the DOM. Every component is `OnPush` and the app is
zoneless, so nothing flushes on its own.

### HTTP

Use `HttpTestingController` and `provideHttpClientTesting()` for service tests.

## Best Practices Summary

1. **User-Centric:** Test what users see and interact with
2. **AAA Pattern:** Arrange, Act, Assert with clear separation
3. **Meaningful Names:** Active voice, specific behavior
4. **Isolation:** Each test is self-contained
5. **Accessibility:** Use semantic queries (getByRole, getByLabelText)
6. **Public API Only:** Don't test private implementation
7. **Async Handling:** Always await promises and user events
8. **Mock at Boundaries:** Mock services, not internal logic
9. **Business Logic Focus:** Don't test Angular's built-in directives
10. **DOM Matchers:** Use jest-dom for readable assertions

For complete usage examples and patterns, see [references/testing-patterns.md](references/testing-patterns.md).
