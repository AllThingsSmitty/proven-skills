---
name: context-cancellation
tags:
  - go-concurrency
  - context
runs: 3
max_turns: 6
---

I'm writing a Go HTTP handler that calls three external services sequentially: first a user service, then an inventory service, then a pricing service. Each call can take up to a second on its own, but I want to enforce a 2-second overall timeout across all three. If any one of them fails, I don't want to bother calling the remaining services.

How should I use context to implement this properly? I'm not sure where to create the context, how to pass it, or what happens to the later calls if an earlier one fails or the timeout fires. Can you show me how to wire this up correctly?
