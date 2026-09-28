---
name: test-gen
description: Generate high-quality tests for existing or new code. Always use this skill when asked to write tests, add test coverage, or generate any kind of test: unit, integration, or end-to-end. Use when the user says "write tests for this", "add coverage", "test this function/class/module/endpoint", "generate unit tests", or when a PR or feature is missing test coverage. Read this skill before writing a single test case.
---

# Test Gen

Good tests verify behavior, not implementation. They should break when something the user cares about breaks, and only then.

## Before writing tests: understand the contract

The contract of a piece of code is what it promises to callers: given these inputs and preconditions, it will produce these outputs or effects. Tests should verify the contract, not the internal mechanics.

Ask before writing:

1. What are the public entry points? (functions, methods, endpoints, events)
2. What does each promise to callers?
3. What are the preconditions (what must be true for the code to work correctly)?
4. What are the postconditions (what must be true after it runs)?
5. What invariants must always hold? (e.g., "the list is always sorted after this call")

If the contract is unclear, clarify it first. A test that verifies vague behavior is itself vague.

## Choosing the right test level

**Unit tests**: verify a single function or class in isolation

- Fast, precise, easy to diagnose when they fail
- Best for: pure functions, business logic, data transformation, edge case enumeration
- Pitfall: over-mocking can make tests verify call sequences rather than behavior

**Integration tests**: verify that components work correctly together

- Slower, but catch interface mismatches unit tests miss
- Best for: database queries, external service calls, message passing between modules
- Use a real dependency (test DB, in-memory queue) where possible; mocked interfaces drift from reality

**End-to-end tests**: verify a complete user-visible workflow

- Expensive but highest confidence
- Reserve for critical paths; don't write these for everything

When in doubt, prefer the lowest level that actually exercises the behavior you care about.

## What to test: a checklist

For each unit under test, cover:

**Happy path**: the primary success case with typical inputs
**Boundary conditions**: values at the edges of the input domain (empty, zero, max, min, exactly-one)
**Error paths**: invalid inputs, missing required data, unexpected types
**Contract invariants**: properties that must hold across multiple calls or states
**Known-problematic cases**: off-by-ones, nulls, Unicode edge cases, floating-point equality

Don't test the framework or language itself. Don't test private implementation details that could change without breaking the contract.

## Avoiding the common pitfalls

**Over-mocking**: If a test mocks more than 2-3 things, ask whether it's testing behavior or just verifying that functions were called in the right order. The latter is fragile and usually useless.

**Testing too much in one test**: Each test should have one reason to fail. If a test is long and covers multiple scenarios, split it. A failing test should immediately tell you what broke.

**Brittle assertions**: Asserting the exact string in an error message, the exact order of unordered results, or internal state that isn't part of the contract leads to tests that break on unrelated changes. Assert the property that matters, not the exact form.

**Happy-path-only coverage**: Error paths and edge cases are where bugs live. They're also what keeps you from breaking someone's production workflow during a refactor.

## Test structure

Use Arrange-Act-Assert (or Given-When-Then for BDD-style):

```
// Arrange: set up preconditions and inputs
// Act: invoke the code under test
// Assert: verify the outcome
```

Keep each section short and obvious. If "Arrange" takes 30 lines, consider a builder or factory helper. If "Assert" checks 10 things, consider whether this is really one test.

Test names should describe the scenario and expected outcome:

- `returns_empty_list_when_no_matching_records`
- `throws_validation_error_when_email_is_missing`
- `preserves_insertion_order_after_deduplication`

Not: `test1`, `testHappyPath`, `testEdgeCase`.

## Property-based thinking

For functions with a clear input-output relationship, think about invariants that should hold for all valid inputs, not just specific examples:

- "For any non-empty list, the result should contain at least one element"
- "Sorting twice should produce the same result as sorting once"
- "Encoding and then decoding should round-trip to the original value"

Even if you don't use a property-based testing library, framing tests this way reveals edge cases you wouldn't have thought to enumerate.

## Integration tests: what to actually test

When testing code that talks to a database, API, or queue:

- Use a real (test/in-memory) instance, not a mock, whenever practical
- Test the boundary behavior: what happens when the external system returns an error, times out, or returns unexpected data?
- Don't test the ORM or HTTP client itself: test your code's behavior given what those return

## When to write the test

For bug fixes: write the failing test first, then fix it. This proves you've identified the right condition and guards against regression.

For new features: write tests in parallel with the code, not after. Writing tests after leads to tests that only describe the implementation you happened to write.

For refactoring: tests must be green before you touch anything. If they're not, fixing them first is the job.
