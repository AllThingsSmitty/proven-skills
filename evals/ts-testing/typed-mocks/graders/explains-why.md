---
type: llm
criteria: |
  The agent should explain why typed mocks matter, not just show the syntax:
  - Mention that `as any` hides type mismatches; if the real function's signature changes, the test still compiles
  - Connect typed mocks to catching interface regressions at compile time
---
