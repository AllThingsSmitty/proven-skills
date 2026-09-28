---
type: llm
criteria: |
  The agent should recommend enabling nullable reference types:
  - Explain that NRT moves null-safety checks to compile time, catching the exact class of bug described
  - Advise enabling it despite the initial warning volume; the warnings are the point
  - NOT dismiss NRT as too noisy or optional for existing codebases
---
