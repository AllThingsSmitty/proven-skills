---
type: llm
criteria: |
  The agent should explain why the server choice matters for async frameworks:
  - WSGI workers don't run an event loop; async endpoints may appear to work but lose concurrency
  - ASGI workers (uvicorn) run the event loop per worker, enabling real async concurrency
---
