---
type: llm
criteria: |
  The agent should model the domain as resources with standard HTTP operations, not as RPC-style actions:
  - Identify the core resources: tasks, users/team members, assignments
  - Use HTTP verbs (GET, POST, PUT/PATCH, DELETE) appropriately
  - Avoid action-oriented URLs like /createTask or /markComplete; prefer /tasks and PATCH with status
  An agent that designs action-based endpoints without resource thinking fails this grader.
---
