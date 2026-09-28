---
type: llm
criteria: |
  The agent should explain the deadlock mechanism:
  - `.Result` blocks the current thread while holding a synchronization context
  - The async continuation needs that same context to resume, creating a deadlock
  - Explain why it works in unit tests (no sync context) but hangs in production (ASP.NET classic, WPF, etc.)
---
