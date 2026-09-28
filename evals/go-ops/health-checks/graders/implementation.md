---
type: llm
criteria: |
  The agent should show or describe implementing both endpoints as simple HTTP handlers (e.g., `/healthz` and `/readyz`). The readiness check should attempt a lightweight check of dependencies (e.g., `db.PingContext(ctx)`). Should caution against making liveness checks too complex: if liveness depends on DB connectivity, a DB outage restarts all pods unnecessarily.
---
