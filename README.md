# Proven Skills

A collection of Claude Code skills for software development workflows. Stack-agnostic, principles-based — designed to work across any language or framework.

[![CI](https://github.com/AllThingsSmitty/proven-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/AllThingsSmitty/proven-skills/actions/workflows/validate.yml)

Every skill is backed by model-graded evals that must pass before merge, and a weekly run scores each one with and without the skill loaded so the improvement is measured, not assumed. See the latest [with/without results](evals/results/published/latest.md).

## Skills

### General Dev

| Skill                                | Description                                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| [debug](skills/debug/SKILL.md)       | Hypothesis-driven debugging: frame the problem, form a hypothesis, narrow scope, prove it, fix the root cause |
| [test-gen](skills/test-gen/SKILL.md) | Generate tests that verify contracts and edge cases, not just happy paths                                     |
| [refactor](skills/refactor/SKILL.md) | Safe, disciplined refactoring with test-first discipline and small reversible steps                           |
| [pr-prep](skills/pr-prep/SKILL.md)   | Pre-PR checklist: diff review, test coverage, migration safety, blast radius, PR description                  |

### Web / Distributed Systems

| Skill                                      | Description                                                                                                |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| [api-design](skills/api-design/SKILL.md)   | REST and GraphQL API design: resource modeling, HTTP semantics, error shapes, versioning, breaking changes |
| [db-review](skills/db-review/SKILL.md)     | Schema design, indexing strategy, query analysis, and safe migrations under concurrent load                |
| [perf](skills/perf/SKILL.md)               | Performance investigation: profiling, N+1 detection, caching strategy, load testing                        |
| [incident](skills/incident/SKILL.md)       | Incident response: triage, blast radius, mitigation, communication cadence, post-mortem                    |
| [arch-review](skills/arch-review/SKILL.md) | Distributed systems review: service boundaries, failure modes, consistency, observability, operability     |
| [security](skills/security/SKILL.md)       | Security review: threat modeling, injection, auth/authz, secrets, dependencies, crypto, web headers        |

### TypeScript / Node.js

| Skill                                    | Description                                                                                         |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------- |
| [ts-types](skills/ts-types/SKILL.md)     | TypeScript type system: generics, discriminated unions, narrowing, utility types, avoiding `any`    |
| [ts-testing](skills/ts-testing/SKILL.md) | Testing in TypeScript: typed mocks, Jest/Vitest setup, type-level tests, avoiding `as any` in tests |
| [node-async](skills/node-async/SKILL.md) | Node.js async patterns: event loop, Promises, streams, back-pressure, unhandled rejections          |
| [node-ops](skills/node-ops/SKILL.md)     | Production Node.js: graceful shutdown, health checks, clustering, memory, uncaught exceptions       |

### Python

| Skill                                    | Description                                                                                      |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------ |
| [py-types](skills/py-types/SKILL.md)     | Python type system: type hints, mypy, Protocol, TypedDict, dataclasses, generics, avoiding `Any` |
| [py-async](skills/py-async/SKILL.md)     | Python async patterns: asyncio, blocking call detection, `asyncio.gather`, task management       |
| [py-testing](skills/py-testing/SKILL.md) | Testing with pytest: fixtures, parametrize, patch location, async tests, monkeypatch             |
| [py-ops](skills/py-ops/SKILL.md)         | Production Python: WSGI vs ASGI, gunicorn/uvicorn, graceful shutdown, config validation          |

### .NET / C#

| Skill                                            | Description                                                                                             |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| [dotnet-types](skills/dotnet-types/SKILL.md)     | C# type system: nullable reference types, records, pattern matching, generics, value types              |
| [dotnet-async](skills/dotnet-async/SKILL.md)     | C# async patterns: avoiding deadlocks, `async void`, `ConfigureAwait`, `CancellationToken`, `ValueTask` |
| [dotnet-testing](skills/dotnet-testing/SKILL.md) | .NET testing: xUnit, Moq/NSubstitute, FluentAssertions, WebApplicationFactory integration tests         |
| [dotnet-ops](skills/dotnet-ops/SKILL.md)         | Production .NET: graceful shutdown, health checks, `IOptions` config validation, `BackgroundService`    |

### Go

| Skill                                            | Description                                                                                 |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| [go-types](skills/go-types/SKILL.md)             | Go type system: interfaces, embedding, generics, type assertions, error wrapping            |
| [go-concurrency](skills/go-concurrency/SKILL.md) | Go concurrency: goroutines, channels, context, sync primitives, goroutine leak detection    |
| [go-testing](skills/go-testing/SKILL.md)         | Go testing: table-driven tests, subtests, interface mocks, testify, benchmarks              |
| [go-ops](skills/go-ops/SKILL.md)                 | Production Go: graceful shutdown, signal handling, health checks, pprof, structured logging |

## Installation

**macOS / Linux:**

```bash
# Install specific skills into the current project
./install.sh debug test-gen pr-prep

# Install all skills
./install.sh all

# Install globally (available in every project)
./install.sh --global all
```

**Windows (PowerShell):**

```powershell
# Install specific skills into the current project
.\install.ps1 debug, test-gen, pr-prep

# Install all skills
.\install.ps1 all

# Install globally (available in every project)
.\install.ps1 -Global all
```

Skills install into `.claude/skills/` in the current directory, or `~/.claude/skills/` with the global flag. Claude Code loads them automatically — no further configuration needed.

## Usage

Invoke any skill explicitly by name — this is the most reliable way to use them:

```
/debug
/ts-types
/py-async
/dotnet-ops
```

Skills can also trigger automatically when the task context clearly matches the skill's description. Claude Code presents available skills to Claude, which decides whether to consult one based on your prompt. Explicit invocation is always reliable; auto-triggering varies by skill and task.

Run `/skills` in Claude Code to see all available skills and their descriptions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add skills, write evals, and submit pull requests.
