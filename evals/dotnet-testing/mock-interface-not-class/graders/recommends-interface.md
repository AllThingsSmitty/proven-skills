---
type: llm
criteria: |
  The agent should recommend extracting an interface rather than trying to mock the concrete class:
  - Explain that Moq/NSubstitute mock interfaces or virtual methods, not sealed concrete classes
  - Suggest creating `IEmailService` and injecting it; this fixes both testability and the design
  - NOT just suggest making methods `virtual` as the primary solution
---
