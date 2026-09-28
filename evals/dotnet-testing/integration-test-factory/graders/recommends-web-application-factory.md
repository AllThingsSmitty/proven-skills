---
type: llm
criteria: |
  The agent should recommend WebApplicationFactory as the solution:
  - Explain that it runs the full ASP.NET Core pipeline in-process, no real server needed
  - Show or describe using `IClassFixture<WebApplicationFactory<Program>>` and `CreateClient()`
  - NOT just recommend unit testing controllers directly (which skips middleware and routing)
---
