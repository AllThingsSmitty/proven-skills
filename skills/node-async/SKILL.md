---
name: node-async
description: Node.js async patterns advisor. Always use this skill when working with async/await, Promises, the event loop, streams, backpressure, callbacks, or concurrent operations in Node.js. Use when the user asks about unhandled promise rejections, blocking the event loop, Promise.all vs Promise.allSettled, slow Node.js under load, stream backpressure, or says "my Node app lags under load", "event loop is blocked", "how do I implement backpressure", "unhandled promise rejection", or "concurrent requests". Read this before debugging any Node.js async or concurrency issue.
---

# Node.js Async Patterns

Node.js runs on a single thread. Everything async works because the event loop defers I/O. But that model breaks the moment you block the thread or mismanage promises. Most Node.js production issues trace back to one of a handful of async mistakes.

## Never block the event loop

The event loop handles every request. If you block it (with a CPU-intensive loop, a synchronous file read, or heavy JSON parsing), every in-flight request stalls until you're done.

```ts
// Bad: blocks the event loop for every caller
app.get("/report", (req, res) => {
  const result = fs.readFileSync("large-file.csv"); // synchronous — blocks
  res.send(process(result));
});

// Good: yields to the event loop
app.get("/report", async (req, res) => {
  const result = await fs.promises.readFile("large-file.csv");
  res.send(process(result));
});
```

**CPU-bound work** (parsing, hashing, compression) belongs in a Worker Thread, not the event loop. Offload it:

```ts
import { Worker } from "worker_threads";

function runInWorker(data: unknown): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const worker = new Worker("./worker.js", { workerData: data });
    worker.on("message", resolve);
    worker.on("error", reject);
  });
}
```

## Handle every rejected promise

In modern Node.js (v15+), an unhandled promise rejection crashes the process. In older versions it silently swallows the error, often worse.

```ts
// Bad: rejection is swallowed if sendEmail rejects
async function notify(user: User) {
  sendEmail(user.email, "Welcome!"); // fire and forget — dangerous
}

// Good: either await it or explicitly handle the rejection
async function notify(user: User) {
  await sendEmail(user.email, "Welcome!");
}

// Or if you genuinely mean fire-and-forget, handle the rejection explicitly
sendEmail(user.email, "Welcome!").catch((err) =>
  logger.error("email failed", err),
);
```

Listen for the process-level safety net, but don't rely on it as a substitute for proper handling:

```ts
process.on("unhandledRejection", (reason) => {
  logger.error("Unhandled rejection", reason);
  process.exit(1); // exit rather than continue in unknown state
});
```

## Concurrent operations: Promise.all and Promise.allSettled

Run independent async operations concurrently: don't await them sequentially when order doesn't matter.

```ts
// Bad: sequential — total time = sum of all durations
const user = await fetchUser(id);
const orders = await fetchOrders(id);
const prefs = await fetchPrefs(id);

// Good: concurrent — total time = slowest of the three
const [user, orders, prefs] = await Promise.all([
  fetchUser(id),
  fetchOrders(id),
  fetchPrefs(id),
]);
```

**`Promise.all` vs `Promise.allSettled`**:

- `Promise.all`: rejects immediately if any promise rejects. Use when all results are required.
- `Promise.allSettled`: waits for all, gives you success/failure for each. Use when partial results are acceptable.

```ts
const results = await Promise.allSettled([fetchA(), fetchB(), fetchC()]);
for (const result of results) {
  if (result.status === "fulfilled") use(result.value);
  else logger.warn("fetch failed", result.reason);
}
```

## Async iteration and streams

For large data, streams beat loading everything into memory. Use async iteration (Node 12+) to consume them cleanly:

```ts
import { createReadStream } from "fs";
import { createInterface } from "readline";

async function processLines(path: string) {
  const rl = createInterface({ input: createReadStream(path) });
  for await (const line of rl) {
    process(line); // one line at a time — constant memory
  }
}
```

Watch for back-pressure: if you write to a writable stream faster than it drains, you'll buffer unbounded data in memory. Respect the return value of `write()` and wait for the `drain` event, or use `pipeline()`:

```ts
import { pipeline } from "stream/promises";
await pipeline(readableSource, transformStream, writableDestination);
```

`pipeline()` handles back-pressure and cleanup automatically. Prefer it over manually piping.

## async/await over raw Promises

Prefer async/await. It's easier to read, easier to debug (stack traces are meaningful), and error handling is straightforward with try/catch.

```ts
// Harder to follow; error handling scattered across .catch chains
fetchUser(id)
  .then((user) => fetchOrders(user.id))
  .then((orders) => process(orders))
  .catch((err) => handle(err));

// Easier: linear flow, single error handler
try {
  const user = await fetchUser(id);
  const orders = await fetchOrders(user.id);
  process(orders);
} catch (err) {
  handle(err);
}
```

One exception: when composing promises at a higher level (e.g., `Promise.all`), raw promise APIs are still natural.

## Avoid async in constructors

Constructors can't be async. If initialization requires async work, use a static factory method:

```ts
// Bad: constructor silently ignores the async work
class Database {
  constructor() {
    this.connect(); // fire-and-forget — db may not be ready when used
  }
}

// Good: factory that returns a fully-initialized instance
class Database {
  private constructor(private conn: Connection) {}

  static async create(): Promise<Database> {
    const conn = await openConnection();
    return new Database(conn);
  }
}

const db = await Database.create();
```

## What to watch for in code review

- `await` inside a loop where `Promise.all` would work (sequential when concurrent is safe)
- Promises that aren't awaited and don't have `.catch()` handlers
- Synchronous fs/crypto/zlib calls inside request handlers
- Heavy CPU work (parsing, hashing large data) on the event loop thread
- Streams being consumed via `.on('data')` without back-pressure handling
