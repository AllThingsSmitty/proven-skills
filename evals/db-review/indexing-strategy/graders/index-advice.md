---
type: llm
criteria: |
  The agent should reason about indexes from the stated query patterns:
  - The queries filter by user_id and status together, so a composite index likely makes sense
  - Sorting by created_at DESC means that column should be in the index or covered
  - Discuss cardinality: status has low cardinality, so leading with it in a composite index may not be ideal
  An agent that just says "add indexes" without reasoning about the query patterns fails this grader.
---
