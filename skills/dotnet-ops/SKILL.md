---
name: dotnet-ops
description: Production .NET operations advisor. Always use this skill when deploying or operating ASP.NET Core applications, configuring Kestrel, IHostedService, BackgroundService, health checks, graceful shutdown, SIGTERM, structured logging, or IOptions validation. Use when the user asks "graceful shutdown in ASP.NET Core", "BackgroundService exception handling", "IOptions eager validation", "health checks in .NET", "structured logging with Serilog", "SIGTERM in .NET", or "run background work in .NET". Read this skill before advising on any .NET production or deployment topic.
---

# Production .NET Operations

ASP.NET Core is production-ready out of the box, but several defaults need explicit configuration before a service is truly operational: graceful shutdown, meaningful health checks, structured logging, and validated configuration. These aren't nice-to-haves; they're the difference between a service that degrades gracefully and one that drops requests during deploys.

## Graceful shutdown

.NET's generic host handles `SIGTERM` and `SIGINT` automatically: it triggers `IHostApplicationLifetime.ApplicationStopping` and waits for hosted services to stop. Configure the timeout:

```csharp
// Program.cs
builder.Services.Configure<HostOptions>(options =>
{
    options.ShutdownTimeout = TimeSpan.FromSeconds(30);
});
```

For Kestrel (HTTP), in-flight requests are drained during shutdown. To stop accepting new connections while draining:

```csharp
var lifetime = app.Services.GetRequiredService<IHostApplicationLifetime>();
lifetime.ApplicationStopping.Register(() =>
{
    // Signal readiness probe to return 503 — stops new traffic from routing here
    _isShuttingDown = true;
});
```

For custom resources (message consumers, database connections), implement `IHostedService`:

```csharp
public class MyConsumer : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var message in _queue.ReadAsync(stoppingToken))
        {
            await ProcessAsync(message, stoppingToken);
        }
        // Loop exits cleanly when stoppingToken is cancelled
    }
}
```

`BackgroundService` handles the hosted service lifecycle. Override `ExecuteAsync` and respect the `stoppingToken`.

## Health checks

ASP.NET Core has built-in health check middleware. Separate liveness from readiness:

```csharp
builder.Services.AddHealthChecks()
    .AddCheck("live", () => HealthCheckResult.Healthy(), tags: ["live"])
    .AddNpgsql(connectionString, tags: ["ready"])    // checks DB connectivity
    .AddCheck<CustomReadinessCheck>("app-ready", tags: ["ready"]);

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("live"),
});
app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready"),
    ResultStatusCodes = {
        [HealthStatus.Healthy] = 200,
        [HealthStatus.Degraded] = 200,
        [HealthStatus.Unhealthy] = 503,
    },
});
```

The readiness check should fail during startup (before the app is configured) and during shutdown. Use `IHostApplicationLifetime` to flip a flag on shutdown and include it in the readiness check.

## Configuration with IOptions

Don't read `IConfiguration` directly in services; bind it to typed options classes and inject those instead. This validates at startup, is testable, and is refactor-safe.

```csharp
// Options class
public class EmailOptions
{
    public const string Section = "Email";

    [Required]
    public string SmtpHost { get; init; } = default!;

    [Range(1, 65535)]
    public int SmtpPort { get; init; } = 587;
}

// Registration — ValidateDataAnnotations catches missing required config at startup
builder.Services.AddOptions<EmailOptions>()
    .BindConfiguration(EmailOptions.Section)
    .ValidateDataAnnotations()
    .ValidateOnStart();   // fail at startup, not on first use

// Usage
public class EmailService(IOptions<EmailOptions> options)
{
    private readonly EmailOptions _opts = options.Value;
}
```

Environment variable overrides: .NET configuration providers stack in order. The `ASPNETCORE_` and `DOTNET_` prefixes are automatically mapped; for custom sections use double underscore for nesting: `Email__SmtpHost=smtp.example.com`.

## Structured logging

Use `ILogger<T>`; it's built in and integrates with any sink. Add Serilog for production-quality structured output:

```csharp
// Program.cs
builder.Host.UseSerilog((ctx, config) =>
{
    config
        .ReadFrom.Configuration(ctx.Configuration)
        .Enrich.FromLogContext()
        .WriteTo.Console(new JsonFormatter());  // JSON for log aggregators
});
```

```csharp
// In services — use source-generated logging for performance
public partial class UserService(ILogger<UserService> logger)
{
    [LoggerMessage(Level = LogLevel.Information, Message = "User {UserId} created")]
    private partial void LogUserCreated(string userId);
}
```

Source-generated logging (`[LoggerMessage]`) avoids boxing and string allocation on the hot path; use it in high-throughput services.

Log levels: `Error` for actionable failures, `Warning` for degraded but functional, `Information` for significant lifecycle events, `Debug` for local dev only. Never `Debug` in production by default.

## Background services

For recurring work, use `BackgroundService`:

```csharp
public class CleanupJob : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            await DoCleanupAsync(stoppingToken);
            await Task.Delay(TimeSpan.FromHours(1), stoppingToken);
        }
    }
}

builder.Services.AddHostedService<CleanupJob>();
```

If `ExecuteAsync` throws, the host logs the exception but continues running: the background service stops silently. Handle exceptions inside `ExecuteAsync` or use `IHostApplicationLifetime.StopApplication()` to fail the whole process if the job is critical.

## Kestrel in production

Behind a reverse proxy (nginx, YARP, Azure Front Door), Kestrel's defaults are fine. Direct internet exposure needs tuning:

```csharp
builder.WebHost.ConfigureKestrel(options =>
{
    options.Limits.MaxConcurrentConnections = 1000;
    options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);
    options.Limits.MaxRequestBodySize = 10 * 1024 * 1024; // 10 MB
});
```

Always set `ASPNETCORE_ENVIRONMENT` to `Production` in production: it disables developer exception pages and switches behavior in several middleware components.

## What to watch for in code review

- `ShutdownTimeout` not configured: process killed mid-request during deploys
- A single `/health` endpoint serving both liveness and readiness purposes
- `IConfiguration["Key"]` read directly in services instead of `IOptions<T>`
- `ValidateOnStart()` missing: config errors surface at runtime, not startup
- `BackgroundService.ExecuteAsync` without exception handling: job fails silently
- `Console.WriteLine` or `Debug.WriteLine` instead of `ILogger`
- `ASPNETCORE_ENVIRONMENT` not set: app runs in Development mode in production
