---
name: ts-testing
description: TypeScript testing advisor. Always use this skill when writing tests in TypeScript, setting up Jest or Vitest with TypeScript, creating type-safe mocks, or writing type-level tests. Use when the user asks "how do I mock this in TypeScript", "my mock has the wrong type", "how do I test that a type is correct", "jest.fn doesn't match my interface", "how do I set up Jest with TypeScript", "how do I avoid as any in tests", or "how do I write a type-level test". Read this skill before writing any TypeScript tests or mocks.
---

# TypeScript Testing

Tests that use `as any` to satisfy the type checker aren't testing the types; they're hiding them. The goal is tests that are type-safe at the boundary and test the public interface rather than internals. They should also give meaningful errors when types change.

## Jest setup for TypeScript

Use `ts-jest` or Vitest's native TypeScript support. Avoid transpile-only setups (like `babel-jest` without type checking) for type-related tests: they skip type errors.

**Vitest** (preferred for new projects):
```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
export default defineConfig({ test: { globals: true } });
```

**Jest with ts-jest**:
```json
// jest.config.json
{ "preset": "ts-jest", "testEnvironment": "node" }
```

## Type-safe mocks with `jest.fn`

Always provide the type parameter to `jest.fn`; don't let it default to `jest.Mock` (which is effectively `any`).

```ts
// Bad: loses type information
const fetchUser = jest.fn();

// Good: typed mock
const fetchUser = jest.fn<Promise<User>, [string]>();
fetchUser.mockResolvedValue({ id: '1', name: 'Alice' });
```

For mocking module-level functions, use `jest.mocked()` (Jest 27+) or `vi.mocked()` (Vitest) instead of casting:

```ts
import { sendEmail } from './email';
jest.mock('./email');

const mockSendEmail = jest.mocked(sendEmail);
mockSendEmail.mockResolvedValue(undefined);
```

`jest.mocked()` returns the function with its mock type overlaid; no `as any` needed.

## Mocking interfaces and classes

Use `Partial` + casting only as a last resort. Prefer purpose-built mock factories or dependency injection.

```ts
// Acceptable for simple cases, but loses full interface coverage
const mockRepo: jest.Mocked<UserRepository> = {
  findById: jest.fn(),
  save: jest.fn(),
  delete: jest.fn(),
};

// Better: inject the mock through the constructor
const service = new UserService(mockRepo);
```

If you find yourself adding `as any` to satisfy a mock type, that's usually a signal the interface is too wide or the test is coupled to implementation details.

## Testing the public interface, not internals

TypeScript's `private` keyword is a compile-time constraint. In tests, resist the urge to test private methods. They're an implementation detail.

```ts
// Bad: testing a private method directly (requires `as any` to bypass TS)
expect((service as any).buildQuery(params)).toEqual(...);

// Good: test through the public method that exercises the behavior
expect(await service.search(params)).toEqual(expectedResults);
```

If you feel pulled to test a private method, that's often a design signal: the logic may deserve its own module with a public interface.

## Type-level testing

Use `expectTypeOf` (Vitest) or `tsd` (standalone) to assert that types are what you expect, important when building utility types or library code.

**Vitest:**
```ts
import { expectTypeOf } from 'vitest';

expectTypeOf(parseDate('2026-01-01')).toEqualTypeOf<Date>();
expectTypeOf(first([])).toEqualTypeOf<undefined | number>();
```

**tsd** (for libraries, runs as part of CI):
```ts
// index.test-d.ts
import { expectType } from 'tsd';
import { parseDate } from '.';

expectType<Date>(parseDate('2026-01-01'));
```

Type tests catch regressions in generic utilities that runtime tests can't: a function that works correctly at runtime can still have a broken type signature.

## The `satisfies` operator in test assertions

When asserting shape, `satisfies` is often cleaner than `as`:

```ts
const config = {
  timeout: 5000,
  retries: 3,
} satisfies Partial<Config>;

// TypeScript validates the shape AND preserves literal types
// so config.timeout is 5000, not number
```

## Testing async code

Always return or await promises in tests; otherwise failures become false positives.

```ts
// Bad: test passes even if the promise rejects
it('should save user', () => {
  service.save(user); // not awaited — test exits before the promise settles
});

// Good
it('should save user', async () => {
  await service.save(user);
  expect(mockRepo.save).toHaveBeenCalledWith(user);
});
```

For testing rejected promises:

```ts
await expect(service.save(invalidUser)).rejects.toThrow('Validation failed');
```

## What to watch for in code review

- `jest.fn()` without a type parameter (loses the mock's type contract)
- `as any` used to satisfy mock types (hides type mismatches that should be fixed)
- Tests that access private members via `as any`
- Unawaited promises in async tests
- Mocks that return hardcoded shapes that diverge from the actual type will pass tests but fail at runtime when the real type changes
