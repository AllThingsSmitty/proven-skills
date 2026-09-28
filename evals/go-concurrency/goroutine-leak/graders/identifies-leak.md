---
type: llm
criteria: |
  The agent should identify that the goroutine will leak if the items channel is never closed. The response must explain that the goroutine blocks indefinitely on the range statement waiting for new values or a channel close, and that because the caller has no way to signal the goroutine to stop (other than closing the channel), abandoning the operation leaves the goroutine running forever.

  The agent should explain that goroutines are not garbage collected when their parent function returns; they run until they exit on their own or the program ends. A goroutine that is blocked with no path to exit is a leak that consumes memory and may hold references to other resources, preventing them from being collected.
---
