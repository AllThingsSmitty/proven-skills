---
type: llm
criteria: |
  The agent should recommend a concrete type-testing tool or approach:
  - Mention `expectTypeOf` (Vitest) or `tsd` (for library authors) as purpose-built options
  - Show or describe how to assert that a function's return type matches an expected type
  - NOT just say "check the type in your IDE"; that's not a reproducible test
---
