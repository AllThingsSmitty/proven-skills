---
type: llm
criteria: |
  The agent should explain that when one call fails, whether because of an application error, a network error, or because the 2-second timeout fires, the context deadline is still in effect for subsequent calls. If the context has timed out or been cancelled, subsequent calls that accept the context will return immediately with ctx.Err(), which will be context.DeadlineExceeded or context.Canceled rather than a service-specific error.

  The agent should advise checking the error from each service call and returning early on failure rather than continuing to invoke the remaining services. Explicit early returns make intent clear and prevent unnecessary work:

  ```go
  user, err := userService.Get(ctx, userID)
  if err != nil {
      return nil, fmt.Errorf("user lookup: %w", err)
  }

  inventory, err := inventoryService.Get(ctx, itemID)
  if err != nil {
      return nil, fmt.Errorf("inventory lookup: %w", err)
  }
  ```

  The agent should note that wrapping errors with fmt.Errorf and %w preserves the ability for callers to use errors.Is(err, context.DeadlineExceeded) to distinguish timeout failures from other errors.
---
