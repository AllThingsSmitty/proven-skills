---
name: refactor
description: Guide safe, disciplined code refactoring. Always use this skill when asked to refactor, restructure, reorganize, clean up, or improve the design of existing code. Use when the user says "this code is messy", "help me clean this up", "this function does too much", "extract this", "break this apart", "this is hard to read", "the codebase is tangled", or any time code structure needs to change without changing behavior. Read this skill before making any structural code changes.
---

# Refactor

Refactoring is changing code structure without changing behavior. The key word is _without_. Every technique here is designed to preserve correctness while improving the code's shape.

## The cardinal rule: tests must be green before you start

If the tests aren't passing before you refactor, you don't have a baseline. You can't tell whether a broken test is the result of your change or was already broken. Fix failing tests first. That's a separate job from the refactoring.

If there are no tests for the code you're about to refactor, write enough to cover the behavior you're going to disturb before touching anything. You don't need 100% coverage: you need enough that a behavioral regression would show up.

## Identify the seam before cutting

A seam is a place where behavior can change without editing the code that uses it, typically a function boundary, interface, or injection point. Find the seam before you start cutting. The seam defines the scope of your refactoring: you're rearranging what's inside it while keeping the seam's behavior the same from the outside.

If the code you need to refactor has no obvious seam, your first task is to introduce one safely (often by extracting a function or class around the region you want to change).

## Work in small, reversible steps

Each step should:

1. Leave the tests green
2. Be a single logical change (rename, extract function, move, inline, etc.)
3. Be independently reviewable

Don't do five things in one commit and call it a refactoring. If something goes wrong, you want to be able to bisect to the exact step that introduced the problem.

A useful rhythm: change → run tests → commit. If the tests go red, undo and understand why before proceeding.

## Common refactoring moves

**Extract function/method**: when a block of code has a single purpose and could be named:

- Name it for what it does, not how it does it
- Pass in what it needs as parameters (avoid reaching for outer scope)
- Verify the caller's behavior is identical before and after

**Rename**: when a name is misleading, vague, or no longer accurate:

- Rename completely and immediately; don't leave both names alive unless there's a real API boundary requiring it
- Update documentation and comments at the same time

**Inline**: when an abstraction is adding indirection without adding clarity:

- Inline functions that are called in only one place and whose name doesn't add understanding
- Don't inline just to reduce line count

**Move**: when code belongs in a different module, class, or file:

- Move one thing at a time
- Update all call sites before committing

**Simplify conditionals**: when nested ifs are hard to follow:

- Early returns / guard clauses to eliminate nesting
- Pull boolean conditions into well-named variables
- Replace complex switch/if chains with a dispatch table or polymorphism when appropriate

**Reduce coupling**: when a module knows too much about another:

- Identify what information actually needs to cross the boundary
- Pass only what's needed, not the whole object

## What refactoring is not

**Not a feature**: Don't add new behavior while refactoring. If you notice something missing, make a note and add it after the refactoring is done and reviewed.

**Not cleanup**: Fixing a bug while refactoring mixes two concerns. When a test reveals a bug during refactoring, stop, fix the bug separately, then continue the refactoring.

**Not rewriting**: Rewriting is starting over. Refactoring is incremental improvement of existing code. If you find yourself wanting to throw it all out and start fresh, that's a different conversation; it may be justified, but it's not refactoring.

## When to stop

Refactoring is in service of a goal, not an end in itself. Stop when:

- The code is clear enough that a reader can understand it without your help
- The next feature would be straightforward to add
- The change you're making has diminishing returns

Don't refactor code that's stable and rarely touched. The cost of changing it (risk, review time) exceeds the benefit. Focus effort on code that's actively worked on.

## Communicate what you're doing

When working on a refactoring:

- State the goal up front: "I'm going to extract the validation logic into a separate function so the handler is easier to read."
- Note the technique: "This is an extract-and-replace. I'm not changing behavior."
- Call out any risks: "This change touches the auth middleware, which has no tests; I'll add coverage before moving it."
- Keep commits focused so the reviewer can tell what changed and why
