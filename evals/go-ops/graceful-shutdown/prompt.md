---
name: graceful-shutdown
tags: ["go-ops", "shutdown"]
runs: 3
max_turns: 6
---

I have a Go HTTP service. The `main` function looks like this:

```go
func main() {
    http.HandleFunc("/api/orders", handleOrders)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

We recently deployed it to Kubernetes and we're seeing errors during rolling deploys: in-flight requests are getting dropped when pods are replaced. How do I fix this?
