---
name: ts-types
description: TypeScript type system advisor. Always use this skill when designing TypeScript types, working with generics, narrowing union types, building discriminated unions, using utility types, or avoiding any. Use when the user says "how do I type this", "why is TypeScript complaining", "object is possibly null", "how do I narrow this", "how do I make this generic", "what's the right type for X", "how do I model this as a union type", or "how do I constrain a generic". Read this skill before answering any TypeScript type question.
---

# TypeScript Types

Good types are constraints, not descriptions. The goal is to make invalid states unrepresentable, so the compiler catches mistakes before they reach runtime.

## Prefer `unknown` over `any`

`any` disables type checking. `unknown` preserves it.

```ts
// Bad: silences all errors downstream
function parse(raw: any) {
  return raw.data.value; // no error, even if raw is null
}

// Good: forces the caller to narrow before using
function parse(raw: unknown) {
  if (typeof raw === 'object' && raw !== null && 'data' in raw) {
    // now safe to use
  }
}
```

Use `any` only at integration boundaries with untyped third-party code, and isolate it; don't let it propagate.

## Avoid type assertions (`as`)

`as T` tells the compiler to trust you. It doesn't check. Use it only when you genuinely know something the compiler can't infer, and add a comment explaining why.

```ts
// Bad: silences a real error
const el = document.getElementById('app') as HTMLDivElement;

// Better: narrow properly
const el = document.getElementById('app');
if (!(el instanceof HTMLDivElement)) throw new Error('Missing #app');
```

## Discriminated unions for modeling state

When a value can be in multiple mutually exclusive states, use a discriminated union: a shared literal field that TypeScript uses to narrow.

```ts
type Result<T> =
  | { status: 'ok'; data: T }
  | { status: 'error'; message: string }
  | { status: 'loading' };

function render(result: Result<User>) {
  if (result.status === 'ok') {
    return result.data.name; // TypeScript knows data exists here
  }
  if (result.status === 'error') {
    return result.message; // TypeScript knows message exists here
  }
  return 'Loading...';
}
```

This beats optional fields (`data?: T; error?: string`) because optional fields allow illegal combinations like `{ data: x, error: y }`.

## Type narrowing

TypeScript narrows types based on control flow. Use the built-in narrowing tools before reaching for type assertions.

- `typeof x === 'string'`: primitive types
- `x instanceof MyClass`: class instances
- `'field' in x`: object shapes
- Custom type guards: `function isUser(x: unknown): x is User`

```ts
function isUser(x: unknown): x is User {
  return typeof x === 'object' && x !== null && 'id' in x && 'name' in x;
}
```

Exhaustiveness checking: make the compiler tell you when you've missed a case:

```ts
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}

function handle(result: Result<User>) {
  switch (result.status) {
    case 'ok': return result.data;
    case 'error': return null;
    case 'loading': return null;
    default: return assertNever(result); // compile error if a case is added but not handled
  }
}
```

## Generics

Generics let you write code that works across types without sacrificing type information. Use them when the relationship between types matters more than the specific type.

```ts
// Bad: loses the return type
function first(arr: unknown[]): unknown { return arr[0]; }

// Good: preserves it
function first<T>(arr: T[]): T | undefined { return arr[0]; }
```

**Constrain generics** when you need to access properties:

```ts
function getId<T extends { id: string }>(item: T): string {
  return item.id;
}
```

**Don't over-generify.** If a function only ever deals with one type, a generic adds complexity without benefit.

## Utility types

Know the built-ins before writing your own:

| Utility | What it does |
|---|---|
| `Partial<T>` | All fields optional |
| `Required<T>` | All fields required |
| `Readonly<T>` | All fields readonly |
| `Pick<T, K>` | Keep only keys K |
| `Omit<T, K>` | Drop keys K |
| `Record<K, V>` | Map from K to V |
| `ReturnType<F>` | Return type of a function |
| `Parameters<F>` | Parameter tuple of a function |
| `NonNullable<T>` | Remove null and undefined |

## The `satisfies` operator

`satisfies` validates that a value matches a type without widening the inferred type. Useful when you want both the type check and the precise literal types.

```ts
const config = {
  port: 3000,
  host: 'localhost',
} satisfies Record<string, string | number>;

// config.port is still inferred as 3000, not number
// but TypeScript validates the shape against Record<string, string | number>
```

## Template literal types

For string manipulation at the type level:

```ts
type EventName<T extends string> = `on${Capitalize<T>}`;
type ClickHandler = EventName<'click'>; // 'onClick'
```

Use sparingly; they add complexity and slow compilation when overused.

## What to watch for in code review

- `any` that propagates past an integration boundary
- `as T` without a comment justifying it
- Optional fields modeling mutually exclusive states (should be a discriminated union)
- Missing exhaustiveness checks in switch statements over union types
- Generics with no constraint accessing properties that might not exist
