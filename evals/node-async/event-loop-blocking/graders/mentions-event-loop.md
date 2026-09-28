---
type: llm
criteria: |
  The agent should explain the event loop impact, not just say "use the async version":
  - Mention that Node.js runs on a single thread and blocking it stalls all other requests
  - Connect the sync call to the observed sluggishness under load
---
