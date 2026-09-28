---
name: go-types
description: Go type system advisor. Always use this skill when designing Go interfaces, working with structs and embedding, using generics, performing type assertions or type switches, defining custom error types, choosing between named types and aliases, or thinking about zero values. Use when the user says "how do I type this in Go", "when should I use an interface", "should I embed or compose", "how do I write a generic function", "how do I assert a type", "how do I wrap an error", "named type vs type alias", or "is my interface too big". Read this skill before answering any Go type system question.
---

# Go Types

Go's type system rewards restraint. The most common mistakes (large interfaces, premature generics, type assertions without comma-ok) all come from over-engineering. Prefer concrete types until abstraction earns its place.

## Interfaces

Interfaces are satisfied implicitly. No `implements` keyword; if a type has the methods, it satisfies the interface. This makes interfaces powerful and dangerous: it's easy to define one that nobody actually satisfies.

**Keep interfaces small.** The standard library's best interfaces have one or two methods: `io.Reader`, `io.Writer`, `fmt.Stringer`. One method = one behavior = easy to satisfy, easy to compose.

```go
// Good: focused, composable
type Reader interface {
    Read(p []byte) (n int, err error)
}

// Bad: eight methods means eight things your mock, stub, or test double must implement
type UserService interface {
    GetUser(id string) (*User, error)
    ListUsers() ([]*User, error)
    CreateUser(u *User) error
    UpdateUser(u *User) error
    DeleteUser(id string) error
    SearchUsers(query string) ([]*User, error)
    GetUserByEmail(email string) (*User, error)
    CountUsers() (int, error)
}
```

**Define interfaces at the point of use, not the point of definition.** The package that *uses* an abstraction should own the interface. The package that *implements* it should expose a concrete type. This avoids unnecessary coupling and import cycles.

```go
// Bad: defined in the implementing package — forces callers to import it even if they want a subset
// package userrepo
type UserRepository interface { ... }

// Good: defined in the consuming package — only asks for what it needs
// package billing
type UserLookup interface {
    GetUser(id string) (*User, error)
}
```

**Interface pollution warning.** If you're defining an interface before you have two implementations, you probably don't need it yet. Concrete types are easier to understand and refactor. Add the interface when the second implementation arrives.

## Structs and Embedding

Embedding promotes methods and fields from an inner type to the outer type. Use it to compose behavior, not to model inheritance.

```go
// Embedding: Logger's methods are promoted to Server
type Server struct {
    *log.Logger
    addr string
}

s := Server{Logger: log.New(os.Stdout, "", 0), addr: ":8080"}
s.Printf("listening on %s", s.addr) // promoted from *log.Logger
```

**Embed for behavior promotion; use a named field for has-a relationships.**

```go
// Use a named field when you want to control access or the relationship is conceptual
type Order struct {
    User    *User   // named field: an order has a user, not is-a user
    db      *sql.DB // named field: implementation detail
}
```

Embedding an interface inside a struct satisfies that interface at compile time and is useful for partial mocking in tests, but it's a footgun in production code: unimplemented methods panic at runtime.

## Generics (Go 1.18+)

Use generics when the logic is genuinely type-agnostic and duplicating it for each type would be worse than the added complexity. Don't use them to avoid writing two functions.

```go
// Good: logic is identical regardless of type, constraint is meaningful
func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

// Probably not worth it: the concrete version is clearer
func MaxInt(a, b int) int {
    if a > b { return a }
    return b
}
```

**Use type constraints, not `any`, when you need operations on the type.**

```go
import "golang.org/x/exp/constraints"

func Max[T constraints.Ordered](a, b T) T {
    if a > b { return a }
    return b
}
```

Custom interface constraints work for domain-specific requirements:

```go
type Numeric interface {
    ~int | ~int64 | ~float64
}

func Sum[T Numeric](vals []T) T {
    var total T
    for _, v := range vals {
        total += v
    }
    return total
}
```

**Don't over-generify.** Generics add cognitive overhead. If a function only ever handles one or two concrete types, write those functions. Readable, concrete code beats clever, generic code.

## Type Assertions and Type Switches

Always use the comma-ok form for type assertions. A bare assertion panics if the type doesn't match.

```go
var i interface{} = "hello"

// Bad: panics if i is not a string
s := i.(string)

// Good: safe
s, ok := i.(string)
if !ok {
    // handle the mismatch
}
```

Use a type switch when branching on multiple types:

```go
func describe(i interface{}) string {
    switch v := i.(type) {
    case string:
        return fmt.Sprintf("string: %q", v)
    case int:
        return fmt.Sprintf("int: %d", v)
    case error:
        return fmt.Sprintf("error: %s", v.Error())
    default:
        return fmt.Sprintf("unknown: %T", v)
    }
}
```

If you find yourself writing many type assertions against an `interface{}` or `any`, that's a design signal: the types probably deserve a real interface or a concrete wrapper.

## Error Types

`error` is an interface with one method: `Error() string`. Custom error types let you carry structured information and support `errors.Is` and `errors.As`.

```go
// Custom error type — carry structured data
type NotFoundError struct {
    Resource string
    ID       string
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s %q not found", e.Resource, e.ID)
}
```

Wrap errors with `%w` to preserve the chain:

```go
if err != nil {
    return fmt.Errorf("loading user %s: %w", id, err)
}
```

Check errors with `errors.Is` (sentinel values) and `errors.As` (typed unwrapping):

```go
var nfe *NotFoundError
if errors.As(err, &nfe) {
    log.Printf("missing %s %s", nfe.Resource, nfe.ID)
}

if errors.Is(err, ErrTimeout) {
    // retry
}
```

Never compare errors with `==` unless they are sentinel values you control and don't wrap. Wrapping breaks `==` but not `errors.Is`.

## Named Types vs Type Aliases

A **named type** (`type Celsius float64`) creates a distinct type. Assignment between the named type and its underlying type requires an explicit conversion. Use named types to prevent misuse, add methods, or express domain meaning.

```go
type UserID string
type OrderID string

// Compiler stops you from mixing these up
func GetUser(id UserID) (*User, error) { ... }

var oid OrderID = "order-123"
GetUser(oid) // compile error: cannot use OrderID as UserID
```

A **type alias** (`type Celsius = float64`) is an exact synonym: the two names are interchangeable. Use aliases for gradual refactoring or to re-export a type from another package.

```go
// Alias: allows migrating callers incrementally
type OldName = NewPackage.NewName
```

Default to named types for domain concepts. Use aliases only when you need referential identity across package boundaries.

## Zero Values

Design structs so the zero value is either useful or clearly invalid. A zero value that silently misbehaves is a source of hard-to-find bugs.

```go
// Good: zero value is immediately usable
var buf bytes.Buffer
buf.WriteString("hello") // no initialization required

// Good: zero value of sync.Mutex is an unlocked mutex
var mu sync.Mutex
mu.Lock()

// Bad: zero value panics — requires explicit initialization
type Cache struct {
    m map[string]string // nil map — writes will panic
}

// Fixed: initialize in a constructor or use sync.Map
func NewCache() *Cache {
    return &Cache{m: make(map[string]string)}
}
```

For types that cannot have a useful zero value, use a constructor function (`NewFoo`) and make the type's fields unexported so callers cannot bypass it.

## Code Review Checklist

- Interface defined in the implementing package rather than the consuming package
- Interface with more than 3 methods (consider splitting)
- Type assertion without the comma-ok form
- Generic function constrained with `any` that uses operators (`<`, `+`, etc.) on the type parameter
- Generic function written where a pair of concrete functions would be clearer
- `fmt.Errorf` wrapping an error without `%w`
- Error comparison with `==` instead of `errors.Is` / `errors.As`
- Struct with a nil-map or nil-slice field that is not initialized before use
- Named type used where a type alias (or vice versa) is more appropriate
- Embedding an interface inside a struct in non-test code
