---
name: dotnet-async
description: C# async/await patterns advisor. Always use this skill when working with async/await in C#, Task, ValueTask, CancellationToken, ConfigureAwait, or deadlocks. Use when the user asks "why is my async code deadlocking", ".Result causing deadlock", "ConfigureAwait(false)", "async void vs async Task", "when to use ValueTask", "how do I cancel an async operation", "thread CancellationToken through async chain", or "can I call async from sync in C#". Read this skill before advising on any C# async or Task question.
---

# C# Async Patterns

C#'s async/await model is powerful but has a handful of well-known pitfalls. Most production async bugs fall into three categories: deadlocks from blocking on async code, unobserved exceptions from `async void`, and missing cancellation support. Know these cold.

## Never block on async code

Calling `.Result` or `.Wait()` on a Task blocks the current thread and can deadlock in contexts with a synchronization context (WinForms, WPF, old ASP.NET):

```csharp
// Bad: can deadlock in sync-context environments
var user = GetUserAsync(id).Result;
var data = FetchDataAsync().GetAwaiter().GetResult();

// Good: async all the way up
var user = await GetUserAsync(id);
```

In ASP.NET Core there is no synchronization context, so `.GetAwaiter().GetResult()` won't deadlock there, but it still blocks a thread pool thread, defeating the purpose of async. Make it async all the way.

If you genuinely need to call async from sync (e.g., a console app entry point or legacy code), use `Task.Run(() => method()).GetAwaiter().GetResult()` as a last resort, but don't normalize it.

## `async void` is dangerous

`async void` methods can't be awaited. If they throw, the exception is unobservable and crashes the process (or is silently swallowed depending on the host). Use `async Task` everywhere except event handlers.

```csharp
// Bad: exception from SendEmailAsync is unobservable
async void NotifyUser(User user)
{
    await SendEmailAsync(user.Email);
}

// Good: exception can be observed by the caller
async Task NotifyUserAsync(User user)
{
    await SendEmailAsync(user.Email);
}
```

The one legitimate use for `async void` is event handlers, where the delegate signature requires `void`:

```csharp
button.Click += async (sender, e) =>
{
    await DoWorkAsync();
};
```

Even then, wrap the body in a try/catch to prevent unobserved exceptions from surfacing.

## ConfigureAwait(false)

In library code, use `ConfigureAwait(false)` on every await to avoid capturing the synchronization context. This prevents deadlocks when library consumers call your code from a context-aware environment.

```csharp
// Library code
public async Task<string> FetchAsync(string url)
{
    var response = await httpClient.GetAsync(url).ConfigureAwait(false);
    return await response.Content.ReadAsStringAsync().ConfigureAwait(false);
}
```

In **application code** (ASP.NET Core controllers, Blazor, etc.), `ConfigureAwait(false)` is not required: ASP.NET Core has no sync context. Omitting it is fine and reduces noise.

Rule of thumb: library authors need it; application developers usually don't.

## CancellationToken: thread it through everything

Accept a `CancellationToken` in every async method and pass it to every downstream async call. This enables proper cooperative cancellation: the request is cancelled, the database query stops, the HTTP call aborts.

```csharp
// Bad: no cancellation support — keeps running after the client disconnects
public async Task<User> GetUserAsync(string id)
{
    return await db.Users.FindAsync(id);
}

// Good: propagates cancellation
public async Task<User> GetUserAsync(string id, CancellationToken ct = default)
{
    return await db.Users.FindAsync(new object[] { id }, ct);
}
```

In ASP.NET Core, inject `CancellationToken` as an action parameter; the framework provides a token that cancels when the client disconnects:

```csharp
[HttpGet("{id}")]
public async Task<User> GetUser(string id, CancellationToken ct)
{
    return await userService.GetUserAsync(id, ct);
}
```

## Task vs ValueTask

`Task` allocates a heap object. For hot paths where the result is often available synchronously (cache hits, simple property access), `ValueTask` avoids the allocation:

```csharp
// ValueTask — no allocation when result is already available
public ValueTask<string> GetCachedAsync(string key)
{
    if (_cache.TryGetValue(key, out var value))
        return ValueTask.FromResult(value);   // no allocation

    return new ValueTask<string>(FetchFromDbAsync(key));
}
```

`ValueTask` rules:

- Can only be awaited once
- Don't store it in a field and await it multiple times
- Don't use it unless profiling shows Task allocation is a bottleneck; `Task` is almost always fine

## Concurrent operations

Use `Task.WhenAll` for concurrent independent operations:

```csharp
// Sequential — total time = sum
var user = await GetUserAsync(id, ct);
var orders = await GetOrdersAsync(id, ct);

// Concurrent — total time = slowest
var (user, orders) = await (GetUserAsync(id, ct), GetOrdersAsync(id, ct));
// Or:
await Task.WhenAll(GetUserAsync(id, ct), GetOrdersAsync(id, ct));
```

`Task.WhenAll` throws `AggregateException` if any task faults. To get partial results when some may fail:

```csharp
var tasks = new[] { FetchA(ct), FetchB(ct), FetchC(ct) };
await Task.WhenAll(tasks);  // awaiting after WhenAll unwraps the first exception
// Check each task individually for partial results
```

## Async in constructors

Constructors can't be async. Use a static factory method:

```csharp
public class Repository
{
    private readonly DbConnection _connection;

    private Repository(DbConnection connection) => _connection = connection;

    public static async Task<Repository> CreateAsync(string connStr, CancellationToken ct = default)
    {
        var conn = new DbConnection(connStr);
        await conn.OpenAsync(ct);
        return new Repository(conn);
    }
}

var repo = await Repository.CreateAsync(connStr, ct);
```

## What to watch for in code review

- `.Result` or `.Wait()`: deadlock risk and thread waste
- `async void` outside of event handlers: unobservable exceptions
- Async methods that don't accept `CancellationToken`
- `await` inside a loop where `Task.WhenAll` would work
- Missing `ConfigureAwait(false)` in library projects
- `ValueTask` stored in a field or awaited multiple times
