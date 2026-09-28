---
name: py-async
description: Python async patterns advisor. Always use this skill when working with asyncio, async/await, the Python event loop, aiohttp, FastAPI, or Celery. Use when the user asks about blocking calls in async context, asyncio.gather, run_in_executor, bridging sync and async, or says "blocking in my async function", "requests.get in async endpoint", "my FastAPI endpoint is slow", "how do I run tasks concurrently in Python", "asyncio.run vs get_event_loop", or "celery and asyncio". Read this before advising on any Python async or concurrency question.
---

# Python Async Patterns

Python's asyncio runs on a single thread. Like Node.js, blocking that thread stalls every coroutine waiting to run. Most asyncio bugs are either blocking calls in async context or mismanaged coroutine scheduling.

## Never block the event loop

Any synchronous I/O or CPU-heavy work inside an `async` function blocks all other coroutines.

```python
# Bad: requests is synchronous — blocks the event loop entirely
async def fetch_user(user_id: str) -> dict:
    response = requests.get(f'/users/{user_id}')  # blocks
    return response.json()

# Good: use an async HTTP client
import httpx

async def fetch_user(user_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f'/users/{user_id}')
        return response.json()
```

Common blocking calls to replace:
| Blocking | Async alternative |
|---|---|
| `requests` | `httpx` (async), `aiohttp` |
| `time.sleep` | `await asyncio.sleep` |
| `open()` / file I/O | `aiofiles` or `asyncio.to_thread` |
| `psycopg2` | `asyncpg`, `psycopg3` (async mode) |

For sync code you can't replace, run it in a thread:

```python
import asyncio

async def process():
    result = await asyncio.to_thread(blocking_cpu_work, data)
    return result
```

`asyncio.to_thread` (Python 3.9+) runs the function in a thread pool executor without blocking the event loop.

## Always `await` coroutines

Calling a coroutine without `await` creates a coroutine object but never runs it. Python will warn about it, but it won't raise an exception: the code silently does nothing.

```python
# Bad: coroutine created but never awaited — save_user never runs
async def register(data: dict) -> None:
    user = create_user(data)
    save_user(user)  # forgot await — this is a no-op

# Good
async def register(data: dict) -> None:
    user = create_user(data)
    await save_user(user)
```

If you see `RuntimeWarning: coroutine 'X' was never awaited`, that's the symptom.

## Concurrent operations: `asyncio.gather`

Run independent coroutines concurrently with `asyncio.gather`: don't await them sequentially when order doesn't matter.

```python
# Bad: sequential — total time = sum of all durations
user = await fetch_user(id)
orders = await fetch_orders(id)
prefs = await fetch_prefs(id)

# Good: concurrent — total time = slowest of the three
user, orders, prefs = await asyncio.gather(
    fetch_user(id),
    fetch_orders(id),
    fetch_prefs(id),
)
```

`asyncio.gather` raises on the first exception by default. Use `return_exceptions=True` when partial results are acceptable:

```python
results = await asyncio.gather(fetchA(), fetchB(), fetchC(), return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        logger.warning('fetch failed', exc_info=result)
    else:
        use(result)
```

## Tasks vs awaited coroutines

`await coroutine()` runs the coroutine sequentially. `asyncio.create_task(coroutine())` schedules it to run concurrently with the current coroutine.

```python
# Sequential: waits for send_email before continuing
await send_email(user.email)

# Concurrent: send_email runs in the background
task = asyncio.create_task(send_email(user.email))
# ... do other work ...
await task  # wait for it before the function returns
```

Fire-and-forget tasks must be stored; if you don't hold a reference, the task may be garbage collected before it completes:

```python
# Bad: task may be GC'd
asyncio.create_task(send_email(user.email))

# Good: keep a reference
background_tasks: set[asyncio.Task] = set()

task = asyncio.create_task(send_email(user.email))
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)
```

## `asyncio.run` is the entry point

Use `asyncio.run()` to start an async program. Don't manage the event loop manually with `get_event_loop()` / `loop.run_until_complete()`; that API is error-prone and deprecated in 3.10+.

```python
# Bad: manual loop management
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()

# Good
asyncio.run(main())
```

In frameworks (FastAPI, Django Channels, etc.), the framework manages the event loop: don't call `asyncio.run` inside a handler.

## `async with` and `async for`

Use async context managers for resources that need async cleanup:

```python
async with httpx.AsyncClient() as client:
    response = await client.get(url)
# client.aclose() is called automatically
```

Use `async for` to consume async iterables (database cursors, streaming responses):

```python
async for row in db.execute('SELECT * FROM users'):
    process(row)
```

## What to watch for in code review

- `requests`, `time.sleep`, synchronous file I/O inside `async def`: blocks the event loop
- Coroutine calls without `await`: silently does nothing
- Sequential `await` calls that could be `asyncio.gather`
- `asyncio.create_task` without storing the reference: task may be GC'd mid-run
- `get_event_loop()` instead of `asyncio.run()` at the program entry point
- Mixing `asyncio.run()` with frameworks that manage their own event loop
