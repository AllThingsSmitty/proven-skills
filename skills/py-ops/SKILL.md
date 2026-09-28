---
name: py-ops
description: Production Python operations advisor. Always use this skill when deploying or operating Python web apps, choosing between WSGI and ASGI, configuring gunicorn or uvicorn, handling graceful shutdown, SIGTERM, config validation, or health checks. Use when the user asks "gunicorn vs uvicorn", "how many workers should I use", "how do I handle SIGTERM in Python", "graceful shutdown in Django or FastAPI", "validate env vars at startup", "my Python app leaks memory", or "WSGI vs ASGI". Read this before advising on any Python production or deployment question.
---

# Production Python Operations

Python web apps have two distinct runtime models, synchronous (WSGI) and asynchronous (ASGI), with different servers, worker models, and operational characteristics. Mixing them up or misconfiguring workers is the most common source of Python production problems.

## WSGI vs ASGI

|                   | WSGI                   | ASGI                                        |
| ----------------- | ---------------------- | ------------------------------------------- |
| Frameworks        | Django, Flask, Falcon  | FastAPI, Starlette, Django 4+ (async views) |
| Server            | gunicorn               | uvicorn, hypercorn, daphne                  |
| Concurrency model | One request per worker | Many requests per worker (async)            |
| I/O concurrency   | Via multiple workers   | Via event loop within each worker           |

**WSGI** handles one request per worker at a time. Scale by adding workers. Blocking I/O is fine: each worker blocks independently.

**ASGI** handles many requests per worker concurrently via the event loop. Blocking I/O kills concurrency (see `py-async`). Fewer workers needed, but each worker must be async-safe.

## Gunicorn worker sizing (WSGI)

The classic formula: `(2 × CPU cores) + 1`.

```bash
gunicorn myapp.wsgi:application \
  --workers 5 \          # 2 × 2 cores + 1
  --worker-class sync \  # default; gthread for threaded
  --timeout 30 \
  --bind 0.0.0.0:8000
```

For WSGI apps with heavy I/O (database calls, external APIs), use `--worker-class gthread` with `--threads` to get concurrency within each worker without going fully async.

## Uvicorn for ASGI

```bash
uvicorn myapp.main:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8000
```

Or run gunicorn with uvicorn's worker class (recommended for production; gunicorn handles process management, uvicorn handles async):

```bash
gunicorn myapp.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

Never use `--reload` in production. It watches the filesystem and restarts workers on every file change, which is a serious performance and security problem in production.

## Graceful shutdown

Gunicorn handles `SIGTERM` gracefully by default: it finishes in-flight requests before exiting. Configure the timeout:

```bash
gunicorn --graceful-timeout 30  # wait up to 30s for workers to finish
```

For custom shutdown logic in your app (closing database connections, flushing queues):

```python
import signal
import sys

def handle_sigterm(signum, frame):
    # flush pending work, close connections
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
```

In a containerized environment, also handle `SIGINT` (Ctrl+C / docker stop):

```python
signal.signal(signal.SIGINT, handle_sigterm)
```

## Health checks

Separate liveness from readiness:

```python
# FastAPI example
@app.get('/health/live')
async def liveness():
    return {'status': 'ok'}  # just confirms the process is running

@app.get('/health/ready')
async def readiness():
    try:
        await db.execute('SELECT 1')
        return {'status': 'ok'}
    except Exception:
        raise HTTPException(status_code=503, detail='Database unavailable')
```

The readiness check should fail during startup (before the DB pool is ready) and during shutdown. Liveness should only fail if the process itself is broken, not if a dependency is down.

## Memory management

Python's garbage collector handles most memory automatically, but leaks happen:

- **Circular references**: Python's GC handles these, but they delay collection. Use `weakref` for back-references (parent → child → parent patterns).
- **Large objects in module scope**: loaded once at import time and never freed. Load lazily or on demand.
- **Unbounded caches**: use `functools.lru_cache(maxsize=N)` not `{}` for in-process caching.
- **Generator vs list**: for large sequences, use generators (`yield`) to avoid loading everything into memory at once.

Diagnose with `tracemalloc` (stdlib) for snapshots or `memory-profiler` for line-by-line profiling:

```python
import tracemalloc
tracemalloc.start()
# ... run the suspected code ...
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:10]:
    print(stat)
```

## Environment configuration

Use environment variables for all configuration. Fail at startup if required config is missing:

```python
# pydantic-settings (recommended)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str         # required — raises at startup if missing
    secret_key: str
    debug: bool = False
    max_connections: int = 10

settings = Settings()         # reads from env vars automatically
```

`pydantic-settings` validates types, provides defaults, and raises a clear error on startup for missing required values, not on the first request that needs them.

## Logging for production

Configure structured logging at startup, not scattered throughout the codebase:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

Or use `structlog` for a production-ready structured logging setup with less boilerplate.

## What to watch for in code review

- `--reload` flag in production scripts or Dockerfiles
- ASGI framework (FastAPI/Starlette) deployed with a WSGI server (plain gunicorn without UvicornWorker)
- No graceful timeout configured: workers killed mid-request during deploys
- Required config accessed with `os.environ.get('KEY')` returning `None` silently instead of failing fast
- Single worker in production (no concurrency, single point of failure)
- `lru_cache` without `maxsize` (unbounded, will grow forever)
