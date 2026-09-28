---
type: llm
criteria: |
  The agent should explain why `Any` is dangerous, not just say "use TypedDict instead":
  - Explain that `Any` is a two-way escape hatch; errors propagate silently downstream
  - Note that silencing mypy is not the same as having correct types
  - NOT just validate the `Any` approach as acceptable
---
