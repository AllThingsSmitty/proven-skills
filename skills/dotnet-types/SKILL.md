---
name: dotnet-types
description: C# and .NET type system advisor. Always use this skill when working with C# nullable reference types, records, pattern matching, switch expressions, generics, value types, or sealed classes. Use when the user asks "how do I handle nulls in C#", "record vs class", "how do I use pattern matching", "CS8600 nullable warning", "how do I enable nullable reference types", "sealed class hierarchy", "switch expression in C#", "struct vs class", or "how do I constrain a generic in C#". Read this skill before answering any C# type system question.
---

# C# Types

C#'s type system has grown significantly: nullable reference types, records, and pattern matching change how you model data and handle null. Use them. Code written without these features tends to be both more verbose and less safe.

## Enable nullable reference types

Enable `<Nullable>enable</Nullable>` in your project file. This makes all reference types non-nullable by default: you must opt into nullability with `?`.

```xml
<!-- .csproj -->
<PropertyGroup>
  <Nullable>enable</Nullable>
</PropertyGroup>
```

```csharp
// Non-nullable — compiler guarantees this is never null
string name = GetName();

// Nullable — must check before use
string? email = GetEmail();
if (email is not null)
{
    Send(email); // safe
}
```

Don't suppress the warnings with `!` (null-forgiving operator) unless you genuinely know more than the compiler; it's the C# equivalent of `as any`.

```csharp
// Bad: suppresses the warning without checking
string email = GetEmail()!;

// Good: check or propagate nullability
string? email = GetEmail();
string resolvedEmail = email ?? throw new InvalidOperationException("Email required");
```

## Records for immutable data

Use `record` for immutable data transfer objects, domain value types, and anything where value equality matters. Records generate `Equals`, `GetHashCode`, `ToString`, and deconstruction automatically.

```csharp
// Immutable record — value equality by default
public record UserId(string Value);
public record User(UserId Id, string Name, string? Email);

// With-expression for non-destructive mutation
var updated = user with { Email = "new@example.com" };
```

**Record vs class**: use a record when the identity of the object is defined by its data (two users with the same fields are equal), not its reference. Use a class when identity is reference-based or the type has mutable state.

**Record struct** (C# 10+): value type semantics with record convenience (good for small value objects in performance-sensitive code):

```csharp
public readonly record struct Money(decimal Amount, string Currency);
```

## Pattern matching

Pattern matching reduces defensive null-checking boilerplate and replaces long if/else chains with readable switch expressions.

```csharp
// Switch expression with property patterns
string Describe(Shape shape) => shape switch
{
    Circle { Radius: > 10 } => "large circle",
    Circle c => $"circle with radius {c.Radius}",
    Rectangle { Width: var w, Height: var h } when w == h => "square",
    Rectangle r => $"rectangle {r.Width}×{r.Height}",
    _ => "unknown shape"
};
```

**Is-pattern for null checking**:

```csharp
if (user is not null && user.Email is string { Length: > 0 } email)
{
    Send(email);
}
```

**List patterns** (C# 11):

```csharp
int[] arr = { 1, 2, 3 };
bool result = arr is [1, .., 3]; // true — starts with 1, ends with 3
```

Exhaustiveness: the compiler warns when a switch expression doesn't cover all cases for discriminated union types (closed hierarchies). Use `abstract` base + `sealed` derived types to get this guarantee:

```csharp
public abstract record Result<T>;
public sealed record Ok<T>(T Value) : Result<T>;
public sealed record Err<T>(string Message) : Result<T>;

string Display<T>(Result<T> result) => result switch
{
    Ok<T> ok => ok.Value?.ToString() ?? "",
    Err<T> err => $"Error: {err.Message}",
    // compiler warns if a case is missing
};
```

## Generics and constraints

Constrain type parameters when you need to access members:

```csharp
// Bad: T is unconstrained — can't call any members
public T First<T>(IEnumerable<T> items) { ... }

// Good: constrain to what you need
public T Max<T>(IEnumerable<T> items) where T : IComparable<T>
{
    return items.Aggregate((a, b) => a.CompareTo(b) > 0 ? a : b);
}
```

Common constraints:

| Constraint             | Meaning                       |
| ---------------------- | ----------------------------- |
| `where T : class`      | Reference type                |
| `where T : struct`     | Value type                    |
| `where T : new()`      | Has parameterless constructor |
| `where T : IInterface` | Implements interface          |
| `where T : BaseClass`  | Inherits from class           |
| `where T : notnull`    | Non-nullable (NRT-aware)      |

## Value types vs reference types

`struct` is a value type: copied on assignment, no heap allocation, no inheritance. Use for small, immutable data with value semantics (coordinates, money, identifiers).

```csharp
// Good as a struct: small, immutable, value equality makes sense
public readonly struct Temperature(double Celsius)
{
    public double Fahrenheit => Celsius * 9 / 5 + 32;
}
```

Avoid mutable structs; they produce surprising copy semantics. Mark structs `readonly` to enforce immutability.

## `var` usage

Use `var` when the type is obvious from the right-hand side or when the exact type is not important:

```csharp
var users = new List<User>();           // obvious
var user = repository.FindById(id);    // fine — type isn't the point

// Don't use var when it hides intent
var x = Calculate();   // what type is x? use explicit type here
```

## What to watch for in code review

- Reference types without `?` in a nullable-enabled project (missing nullability annotation)
- `!` (null-forgiving) without a comment explaining why the value can't be null
- Classes with value semantics that should be records
- `object` parameters or return types that could be generic
- Mutable structs: they produce confusing copy behavior
- Long if/else chains over type checks that pattern matching would simplify
