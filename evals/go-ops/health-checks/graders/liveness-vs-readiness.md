---
type: llm
criteria: |
  The agent should clearly distinguish liveness (is the process alive and not deadlocked; should be trivial, e.g., always return 200) from readiness (is the service ready for traffic; can check DB/Redis connectivity). Should explain that a failing liveness probe causes a pod restart, while a failing readiness probe just removes the pod from the load balancer.
---
