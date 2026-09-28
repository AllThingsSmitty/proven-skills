---
name: go-concurrency
description: >
  Always use this skill when working with goroutines, channels, context, sync
  primitives, or concurrent Go code. Triggers include: "goroutine leak",
  "channel deadlock", "context cancellation", "how do I use WaitGroup",
  "fan-out fan-in", "worker pool", "data race", "select statement", "buffered
  channel", "sync.Mutex", "sync.Once", "context.WithTimeout", "goroutine
  exits", "channel close", "race condition", "concurrent map write".
  Read this skill before advising on any Go concurrency question.
---

## Goroutines

Goroutines are cheap (a few KB of stack) but not free. Every goroutine must have a clear exit condition; otherwise it leaks. A goroutine leak happens when a goroutine blocks forever on a channel send, channel receive, or lock with no one to unblock it.

```go
// Bad: no exit condition — leaks if done is never closed
go func() {
    for item := range items {
        process(item)
    }
}()

// Good: exits on context cancellation
go func() {
    for {
        select {
        case <-ctx.Done():
            return
        case item, ok := <-items:
            if !ok {
                return
            }
            process(item)
        }
    }
}()
```

## Channels

Unbuffered channels provide a synchronous rendezvous: sender and receiver must both be ready. Buffered channels decouple them up to the buffer size.

```go
unbuffered := make(chan int)      // blocks until receiver is ready
buffered   := make(chan int, 10)  // blocks only when full
```

Use directional channel types in function signatures to make intent explicit:

```go
func produce(out chan<- int) { out <- 42 }
func consume(in <-chan int)  { v := <-in; _ = v }
```

Only the sender should close a channel. Closing from the receiver side or closing twice panics.

```go
// Range exits automatically when the channel is closed
for item := range ch {
    process(item)
}
```

## select

`select` lets a goroutine wait on multiple channel operations simultaneously.

**Timeout with context:**

```go
select {
case result := <-resultCh:
    return result, nil
case <-ctx.Done():
    return zero, ctx.Err()
}
```

**Non-blocking check with default:**

```go
select {
case msg := <-ch:
    handle(msg)
default:
    // nothing ready — continue without blocking
}
```

**Fan-in (merge two channels into one):**

```go
func fanIn(ctx context.Context, a, b <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for {
            select {
            case v, ok := <-a:
                if !ok { a = nil }
                if a == nil && b == nil { return }
                if ok { out <- v }
            case v, ok := <-b:
                if !ok { b = nil }
                if a == nil && b == nil { return }
                if ok { out <- v }
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}
```

## context.Context

Always pass context as the first argument. Never store it in a struct.

```go
// Correct
func fetchUser(ctx context.Context, id int) (*User, error) { ... }

// Wrong — context hidden in struct, can't be updated per-call
type Service struct { ctx context.Context }
```

Derive contexts to add deadlines or cancellation:

```go
ctx, cancel := context.WithTimeout(parentCtx, 2*time.Second)
defer cancel() // always defer cancel to release resources

ctx, cancel = context.WithCancel(parentCtx)
defer cancel()
```

Check `ctx.Done()` in loops and before blocking operations:

```go
for _, item := range items {
    if err := ctx.Err(); err != nil {
        return err
    }
    process(item)
}
```

## sync Package

**Mutex / RWMutex**: prefer `RWMutex` for read-heavy workloads; multiple readers can hold the read lock simultaneously.

```go
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

func (s *SafeMap) Get(key string) int {
    s.mu.RLock()
    defer s.mu.RUnlock()
    return s.m[key]
}

func (s *SafeMap) Set(key string, val int) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.m[key] = val
}
```

Never copy a mutex; always use pointer receivers and pass structs by pointer.

**WaitGroup**: wait for a group of goroutines to finish:

```go
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func(it Item) {
        defer wg.Done()
        process(it)
    }(item)
}
wg.Wait()
```

**Once**: run initialization exactly once regardless of how many goroutines call it:

```go
var once sync.Once
once.Do(func() { expensiveInit() })
```

## Common Patterns

**Worker pool:**

```go
func workerPool(ctx context.Context, jobs <-chan Job, numWorkers int) <-chan Result {
    results := make(chan Result)
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobs:
                    if !ok {
                        return
                    }
                    results <- job.Do()
                case <-ctx.Done():
                    return
                }
            }
        }()
    }
    go func() {
        wg.Wait()
        close(results)
    }()
    return results
}
```

**Semaphore with buffered channel**: limit concurrency without a full worker pool:

```go
sem := make(chan struct{}, maxConcurrent)
for _, item := range items {
    sem <- struct{}{}
    go func(it Item) {
        defer func() { <-sem }()
        process(it)
    }(item)
}
// drain semaphore to wait for all
for i := 0; i < maxConcurrent; i++ {
    sem <- struct{}{}
}
```

## Common Pitfalls

**Goroutine leak, no exit condition:**
A goroutine blocked on a channel with no sender/receiver runs forever. Fix: use context cancellation.

**Channel deadlock, send with no receiver:**
All goroutines blocked on channel ops causes `fatal error: all goroutines are asleep`. Fix: ensure every send has a matching receive path (or use buffered channels + workers).

**Data race, unsynchronized shared state:**
Two goroutines reading and writing the same variable without a lock is undefined behavior. Run `go test -race` and `go run -race` always. Fix: use a mutex or communicate via channels.

**Capturing loop variable in goroutine closure:**
```go
// Bad: all goroutines capture the same 'v' variable
for _, v := range items {
    go func() { process(v) }()
}

// Good: pass as argument
for _, v := range items {
    go func(item Item) { process(item) }(v)
}
// Or in Go 1.22+, loop variable is scoped per iteration automatically
```

## Code Review Checklist

- Every goroutine has an explicit exit path (context, channel close, or done signal)
- `cancel()` from `WithCancel`/`WithTimeout`/`WithDeadline` is always deferred immediately
- Channels are closed only by the sender
- Mutexes are not copied (struct passed by pointer, pointer receivers used)
- `wg.Add(n)` is called before launching goroutines, not inside them
- Loop variables captured in goroutine closures are passed as arguments
- `go test -race` passes
- No `context.Background()` used inside request-scoped code: propagate the incoming context
