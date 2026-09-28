---
name: go-ops
description: "Production Go operations advisor. Always use this skill when deploying or operating Go applications, handling graceful shutdown, signal handling, health checks, structured logging, profiling with pprof, or managing configuration. Use when the user asks 'how do I handle SIGTERM in Go', 'graceful shutdown in Go', 'how do I add health checks', 'how do I profile a Go service', 'structured logging in Go', 'slog vs zerolog vs zap', 'how do I read config from env vars', or 'Go kubernetes'. Read this skill before advising on any Go production or deployment topic."
---

## Graceful Shutdown

Never use `log.Fatal(http.ListenAndServe(...))`. It makes your service unkillable gracefully: Kubernetes sends SIGTERM and your pods drop in-flight requests.

The correct pattern uses `signal.NotifyContext` (Go 1.16+) or `signal.Notify` with a channel:

```go
package main

import (
    "context"
    "errors"
    "log/slog"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    srv := &http.Server{
        Addr:    ":8080",
        Handler: routes(),
    }

    // Catch SIGINT and SIGTERM
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()

    // Start serving in a goroutine
    go func() {
        slog.Info("server starting", "addr", srv.Addr)
        if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
            slog.Error("server error", "err", err)
            os.Exit(1)
        }
    }()

    // Block until signal received
    <-ctx.Done()
    slog.Info("shutdown signal received")

    // Give in-flight requests up to 30 seconds to complete
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(shutdownCtx); err != nil {
        slog.Error("shutdown error", "err", err)
        os.Exit(1)
    }

    slog.Info("server stopped cleanly")
}
```

Key rules:
- Use `Shutdown(ctx)` not `Close()`: `Shutdown` waits for in-flight requests; `Close` drops them.
- Always give the shutdown a deadline (30s is a good default). Without it, a hung request hangs your pod forever.
- Kubernetes default `terminationGracePeriodSeconds` is 30s, so align your timeout to be slightly less.

---

## Health Checks

Two endpoints, two different jobs:

| Endpoint | Purpose | Failing behavior |
|----------|---------|-----------------|
| `/healthz` | Liveness: is the process alive? | Kubernetes restarts the pod |
| `/readyz` | Readiness: can it serve traffic? | Kubernetes removes pod from load balancer |

**Liveness must be trivial.** If liveness checks the database and the database goes down, Kubernetes restarts every pod, making an outage worse. Liveness should only confirm the process is not deadlocked.

```go
// Liveness — always 200 as long as the process is running
mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("ok"))
})

// Readiness — check actual dependencies
mux.HandleFunc("/readyz", func(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
    defer cancel()

    if err := db.PingContext(ctx); err != nil {
        slog.Error("readiness: db ping failed", "err", err)
        http.Error(w, "db unavailable", http.StatusServiceUnavailable)
        return
    }

    if err := redisClient.Ping(ctx).Err(); err != nil {
        slog.Error("readiness: redis ping failed", "err", err)
        http.Error(w, "redis unavailable", http.StatusServiceUnavailable)
        return
    }

    w.WriteHeader(http.StatusOK)
    w.Write([]byte("ok"))
})
```

Kubernetes probe config:
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

---

## Structured Logging

Use `log/slog` (stdlib, Go 1.21+) for new projects. Never use `fmt.Printf` in production: you can't query or filter it.

```go
import "log/slog"

// Default logger goes to stderr as text; switch to JSON for production
logger := slog.New(slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))
slog.SetDefault(logger)

// Log with structured key-value attributes
slog.Info("request handled",
    "method", r.Method,
    "path", r.URL.Path,
    "status", statusCode,
    "duration_ms", duration.Milliseconds(),
    "request_id", requestID,
)

// Log errors with context
slog.Error("database query failed",
    "err", err,
    "query", queryName,
    "user_id", userID,
)
```

Always carry context through your logs:
- `request_id`: correlate all log lines for a single request
- `trace_id` / `span_id`: if using distributed tracing (OpenTelemetry)
- `service` / `version`: if running multiple services

**When to use zerolog or zap instead:** Only when benchmarks prove `slog` is a bottleneck (rare). Both zerolog and zap have steeper APIs. Prefer `slog` unless you're logging millions of lines per second.

---

## Configuration

Follow 12-factor: read config from environment variables, not files, not hardcoded constants.

```go
type Config struct {
    Port        string
    DatabaseURL string
    RedisAddr   string
    LogLevel    string
    Debug       bool
}

func loadConfig() (Config, error) {
    cfg := Config{
        Port:     getEnv("PORT", "8080"),
        LogLevel: getEnv("LOG_LEVEL", "info"),
        Debug:    os.Getenv("DEBUG") == "true",
    }

    // Required — fail fast at startup
    cfg.DatabaseURL = os.Getenv("DATABASE_URL")
    if cfg.DatabaseURL == "" {
        return Config{}, fmt.Errorf("DATABASE_URL is required")
    }

    cfg.RedisAddr = os.Getenv("REDIS_ADDR")
    if cfg.RedisAddr == "" {
        return Config{}, fmt.Errorf("REDIS_ADDR is required")
    }

    return cfg, nil
}

func getEnv(key, defaultVal string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return defaultVal
}
```

Fail fast: call `loadConfig()` at the very start of `main()`. If required config is missing, crash immediately with a clear message. A service that starts without its config and silently misbehaves is harder to debug than one that refuses to start.

For complex configs, `github.com/kelseyhightower/envconfig` or `github.com/caarlos0/env` reduce boilerplate while staying 12-factor compliant.

---

## Profiling with pprof

Register the pprof HTTP handlers in your server, but **never expose them publicly**. Gate them behind an internal port or require authentication.

```go
import _ "net/http/pprof" // registers /debug/pprof/* handlers on DefaultServeMux

// Use a separate internal server, never the public one
go func() {
    internalMux := http.NewServeMux()
    internalMux.Handle("/debug/pprof/", http.DefaultServeMux)
    http.ListenAndServe("127.0.0.1:6060", internalMux)
}()
```

The 4 key profiles:

```bash
# CPU profile — 30s sample
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Heap profile — current allocations
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutine dump — all goroutines and their stacks
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Execution trace — scheduling, GC, syscalls (use sparingly, high overhead)
curl -o trace.out http://localhost:6060/debug/pprof/trace?seconds=5
go tool trace trace.out
```

In benchmarks, capture profiles with flags:

```go
func BenchmarkHandler(b *testing.B) {
    // go test -bench=. -cpuprofile=cpu.out -memprofile=mem.out
    // go tool pprof cpu.out
}
```

---

## Build and Deploy

Multi-stage Docker build (small, static, no shell):

```dockerfile
# Stage 1: build
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w -X main.version=${VERSION} -X main.commit=${COMMIT}" \
    -o /bin/server ./cmd/server

# Stage 2: run
FROM gcr.io/distroless/static-debian12
COPY --from=builder /bin/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

Embed version info at build time:

```go
// main.go
var (
    version = "dev"
    commit  = "none"
)

func main() {
    slog.Info("starting", "version", version, "commit", commit)
    // ...
}
```

```bash
# Build with version info
go build -ldflags="-X main.version=$(git describe --tags) -X main.commit=$(git rev-parse --short HEAD)" ./cmd/server
```

Key flags:
- `CGO_ENABLED=0`: fully static binary, no libc dependency
- `-s -w`: strip debug symbols and DWARF info (smaller binary)
- `distroless/static`: no shell, no package manager, minimal attack surface

---

## Common Operational Mistakes

**Not handling SIGTERM.** Kubernetes sends SIGTERM before killing a pod. If you ignore it, in-flight requests fail and you get 502s during rolling deploys.

**Unstructured log lines.** `log.Printf("user %d failed: %v", id, err)` is unsearchable in Splunk, Loki, or CloudWatch. Use `slog` with key-value pairs.

**Missing /readyz.** Without a readiness probe, Kubernetes sends traffic to pods that haven't connected to the database yet. Always implement `/readyz`.

**Exposing pprof publicly.** The goroutine dump and heap profile reveal your entire application state. Bind pprof to localhost or an internal port only.

**Panics that crash the service.** An unrecovered panic kills the entire process, not just one request. Add a recover middleware:

```go
func recoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if rec := recover(); rec != nil {
                slog.Error("panic recovered",
                    "panic", rec,
                    "stack", string(debug.Stack()),
                    "path", r.URL.Path,
                )
                http.Error(w, "internal server error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}
```

**Ignoring context cancellation in database calls.** Always pass `r.Context()` (or a derived context) to `db.QueryContext`, `db.ExecContext`, etc. This allows queries to be cancelled when the client disconnects.

---

## Code Review Checklist

Before shipping a Go service to production:

- [ ] `main()` listens for SIGTERM/SIGINT and calls `srv.Shutdown(ctx)` with a deadline
- [ ] `/healthz` returns 200 immediately (no dependency checks)
- [ ] `/readyz` checks all dependencies with a short timeout (≤2s)
- [ ] All log calls use `slog` with key-value pairs (no `fmt.Printf` or bare `log.Println`)
- [ ] Config is loaded from env vars; missing required vars cause startup failure
- [ ] pprof is only reachable on an internal/localhost port
- [ ] A `recover` middleware is wrapping HTTP handlers
- [ ] All database and external calls pass a context derived from `r.Context()`
- [ ] Docker image uses multi-stage build with `distroless` or `scratch`
- [ ] Binary built with `CGO_ENABLED=0` for a fully static binary
- [ ] Version and commit hash embedded via `-ldflags`
