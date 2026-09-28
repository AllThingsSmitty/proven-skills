---
type: llm
criteria: |
  The agent should recommend a concrete fix, either handling exceptions inside ExecuteAsync or stopping the host:
  - Suggest wrapping the loop body in try/catch to log and continue, OR
  - Using `IHostApplicationLifetime.StopApplication()` to fail the process if the job is critical
  - Explain the tradeoff: catch-and-continue keeps the app up; stop-application triggers a restart
---
