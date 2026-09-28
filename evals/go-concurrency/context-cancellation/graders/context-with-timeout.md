---
type: llm
criteria: |
  The agent should show using context.WithTimeout (or context.WithDeadline) to derive a new context with the 2-second overall timeout, and immediately defer the returned cancel function so resources are always released when the handler returns. The derived context must be passed to all three service calls, not the original request context alone, so that all three calls share the same deadline and the timeout applies to their combined duration, not to each call individually.

  The agent should make clear that the context is typically derived from the incoming request's context (r.Context() in an http.Handler) rather than context.Background(), so the HTTP server's own request cancellation is also respected. A code example should demonstrate this pattern, for instance:

  ```go
  ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
  defer cancel()

  user, err := userService.Get(ctx, userID)
  // ...
  inventory, err := inventoryService.Get(ctx, itemID)
  // ...
  price, err := pricingService.Get(ctx, itemID)
  ```
---
