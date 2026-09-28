---
name: go-testing
description: "Go testing advisor. Always use this skill when writing Go tests, working with the testing package, table-driven tests, subtests, benchmarks, testify, or interface mocking. Use when the user asks 'how do I write a table-driven test', 'how do I mock in Go', 'how do I benchmark this', 'how do I test this HTTP handler', 'how do I use t.Run', 'testify assert vs require', or 'how do I test a function that calls an external service'. Read this skill before writing any Go test."
---

Go tests should verify behavior, not implementation. Keep tests close to the code they test, name them clearly, and make failures self-explanatory without a debugger.

## Table-Driven Tests

Table-driven tests are the idiomatic Go pattern for testing a function across multiple inputs. Use a slice of structs with `name`, input, and expected fields. Always use `t.Run` for each case: it gives each case an identity in the output.

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -1, -2, -3},
        {"zeros", 0, 0, 0},
        {"mixed signs", -4, 6, 2},
    }

    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            got := Add(tc.a, tc.b)
            if got != tc.expected {
                t.Errorf("Add(%d, %d) = %d, want %d", tc.a, tc.b, got, tc.expected)
            }
        })
    }
}
```

Run a single case: `go test -run TestAdd/positive_numbers`.

## Subtests and t.Run

`t.Run` creates a named subtest. Each subtest is independently reported, filterable, and can be run in parallel.

```go
func TestUserCreate(t *testing.T) {
    // Shared setup runs once here

    t.Run("valid input creates user", func(t *testing.T) {
        t.Parallel() // safe to run alongside other parallel subtests
        // ...
    })

    t.Run("duplicate email returns error", func(t *testing.T) {
        t.Parallel()
        // ...
    })
}
```

Use `t.Helper()` in helper functions so failures point to the call site, not the helper internals:

```go
func assertNoError(t *testing.T, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}
```

Use `t.Cleanup` for teardown (it runs even when the test fails):

```go
func TestWithFile(t *testing.T) {
    f, err := os.CreateTemp("", "test-*")
    assertNoError(t, err)
    t.Cleanup(func() { os.Remove(f.Name()) })
    // ...
}
```

## Testify: assert vs require

Both packages come from `github.com/stretchr/testify`.

- `assert`: records the failure and continues the test
- `require`: records the failure and stops the test immediately (calls `t.FailNow`)

**Use `require` for preconditions**: anything where the rest of the test is meaningless if it fails. Use `assert` for independent checks.

```go
import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestGetUser(t *testing.T) {
    user, err := GetUser(42)
    require.NoError(t, err)          // stop if we can't even get a user
    require.NotNil(t, user)          // stop if user is nil — next lines would panic

    assert.Equal(t, 42, user.ID)     // check all fields, collect all failures
    assert.Equal(t, "Alice", user.Name)
    assert.True(t, user.Active)
}
```

`testify/mock` generates mock implementations from interfaces:

```go
type MockStorer struct {
    mock.Mock
}

func (m *MockStorer) Save(ctx context.Context, item Item) error {
    args := m.Called(ctx, item)
    return args.Error(0)
}

func TestSaveItem(t *testing.T) {
    store := new(MockStorer)
    store.On("Save", mock.Anything, someItem).Return(nil)

    svc := NewService(store)
    err := svc.ProcessItem(ctx, someItem)

    require.NoError(t, err)
    store.AssertExpectations(t)
}
```

## Interface-Based Mocking

Never mock a concrete type (`*sql.DB`, `*http.Client`). Define a narrow interface that captures only the operations your code actually needs, then inject it.

```go
// Define the interface your code needs — not the full DB surface
type UserRepository interface {
    FindByID(ctx context.Context, id int) (*User, error)
    Save(ctx context.Context, u *User) error
}

// Production struct accepts the interface
type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

// In tests: a simple fake backed by a map
type fakeUserRepo struct {
    users map[int]*User
}

func (f *fakeUserRepo) FindByID(_ context.Context, id int) (*User, error) {
    u, ok := f.users[id]
    if !ok {
        return nil, ErrNotFound
    }
    return u, nil
}

func (f *fakeUserRepo) Save(_ context.Context, u *User) error {
    f.users[u.ID] = u
    return nil
}

func TestUserService_GetUser(t *testing.T) {
    repo := &fakeUserRepo{users: map[int]*User{
        1: {ID: 1, Name: "Alice"},
    }}
    svc := NewUserService(repo)

    user, err := svc.GetUser(context.Background(), 1)
    require.NoError(t, err)
    assert.Equal(t, "Alice", user.Name)
}
```

A fake with a map or slice backing store is sufficient for most unit tests. Only reach for `testify/mock` when you need to assert call counts, argument values, or return different results per call.

## Testing HTTP Handlers

Use `httptest.NewRecorder()` and `httptest.NewRequest()`; no real server needed.

```go
func TestCreateUserHandler(t *testing.T) {
    body := `{"name":"Alice","email":"alice@example.com"}`
    req := httptest.NewRequest(http.MethodPost, "/users", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")

    rr := httptest.NewRecorder()

    handler := NewCreateUserHandler(fakeRepo)
    handler.ServeHTTP(rr, req)

    assert.Equal(t, http.StatusCreated, rr.Code)

    var resp UserResponse
    require.NoError(t, json.NewDecoder(rr.Body).Decode(&resp))
    assert.Equal(t, "Alice", resp.Name)
}
```

For a full router, pass `httptest.NewServer(router)` and make real HTTP calls against it in integration tests.

## Benchmarks

Benchmark functions start with `BenchmarkXxx` and accept `*testing.B`. The body runs `b.N` times; the framework adjusts `b.N` until the result is stable.

```go
func BenchmarkJSONMarshal(b *testing.B) {
    user := &User{ID: 1, Name: "Alice", Email: "alice@example.com"}

    b.ResetTimer() // exclude setup time above this line
    for i := 0; i < b.N; i++ {
        _, err := json.Marshal(user)
        if err != nil {
            b.Fatal(err)
        }
    }
}
```

Run benchmarks:

```sh
go test -bench=.                          # run all benchmarks
go test -bench=BenchmarkJSONMarshal       # specific benchmark
go test -bench=. -benchmem               # include allocation stats
go test -bench=. -count=5                # repeat for variance
```

## go test Flags

| Flag | Purpose |
|---|---|
| `-run <regexp>` | Run only matching tests/subtests |
| `-v` | Verbose: print each test name and PASS/FAIL |
| `-race` | Enable the race detector — **always use in CI** |
| `-count N` | Run each test N times (disables caching) |
| `-bench <regexp>` | Run matching benchmarks |
| `-benchmem` | Report allocations in benchmarks |
| `-timeout d` | Fail after duration d (default 10m) |
| `-short` | Signal tests to skip slow paths (`testing.Short()`) |

Canonical CI invocation: `go test -race -count=1 ./...`

## Common Mistakes

**Testing implementation, not behavior.** Tests should break when behavior changes, not when you rename a private variable. Test through the public API.

**Skipping `-race`.** Data races are silent in normal runs. Run `go test -race ./...` in CI, always, no exceptions.

**Mocking concrete types.** Wrapping `*sql.DB` with a mock library couples your tests to the library's internals. Define an interface instead.

**Forgetting `t.Helper()`.** Without it, failure lines point into your helper, not the call site. Add `t.Helper()` as the first line of every test helper.

**Shared mutable state between parallel subtests.** When using `t.Parallel()`, each subtest must use its own copy of loop variables: `tc := tc` (pre-Go 1.22) or rely on Go 1.22+ loop variable semantics.

**Not cleaning up.** Use `t.Cleanup`, not `defer` from a helper, so cleanup is tied to the test's lifetime.

## Code Review Checklist

- [ ] Tests are table-driven for multiple input cases
- [ ] Each case runs under `t.Run` with a descriptive name
- [ ] Helper functions call `t.Helper()`
- [ ] Preconditions use `require`, independent assertions use `assert`
- [ ] Dependencies injected as interfaces, not concrete types
- [ ] No real network/DB calls in unit tests
- [ ] `-race` flag used in CI
- [ ] Benchmarks call `b.ResetTimer()` after setup
- [ ] Test names describe behavior (`TestGetUser_notFound`), not implementation
