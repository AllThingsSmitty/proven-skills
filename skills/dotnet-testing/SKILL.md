---
name: dotnet-testing
description: .NET testing advisor. Always use this skill when writing tests in C#, working with xUnit, NUnit, MSTest, Moq, NSubstitute, FluentAssertions, or WebApplicationFactory. Use when the user asks "how do I mock an interface in C#", "mock interface vs concrete class", "how do I test an ASP.NET Core controller", "WebApplicationFactory integration test", "how do I write FluentAssertions", "how do I parametrize tests in C#", or "how do I verify a method was called". Read this skill before writing any .NET test.
---

# .NET Testing

xUnit is the modern standard for .NET: it's what ASP.NET Core itself uses internally. Its constructor-based setup (no `[SetUp]` attribute) encourages smaller, more focused test classes. Use it for new projects.

## xUnit basics

```csharp
public class UserServiceTests
{
    private readonly UserService _sut;
    private readonly IUserRepository _repository;

    // Constructor runs before each test — replaces [SetUp]
    public UserServiceTests()
    {
        _repository = Substitute.For<IUserRepository>(); // NSubstitute
        _sut = new UserService(_repository);
    }

    [Fact]
    public async Task GetUser_WhenUserExists_ReturnsUser()
    {
        // Arrange
        var userId = "user-1";
        _repository.FindByIdAsync(userId, Arg.Any<CancellationToken>())
            .Returns(new User(userId, "Alice"));

        // Act
        var result = await _sut.GetUserAsync(userId);

        // Assert
        result.Should().NotBeNull();
        result!.Name.Should().Be("Alice");
    }
}
```

**Test naming**: `MethodName_Scenario_ExpectedResult` is readable and searchable. Keep it consistent across the project.

## Parametrized tests with `[Theory]`

Replace repeated `[Fact]` methods with `[Theory]` + `[InlineData]`:

```csharp
[Theory]
[InlineData("user@example.com", true)]
[InlineData("user+tag@example.com", true)]
[InlineData("not-an-email", false)]
[InlineData("", false)]
public void ValidateEmail_ReturnsExpectedResult(string email, bool expected)
{
    var result = EmailValidator.Validate(email);
    result.Should().Be(expected);
}
```

For complex test data, use `[MemberData]` with a static property returning `IEnumerable<object[]>`, or `[ClassData]` for a dedicated data class.

## Mocking: Moq vs NSubstitute

Both are solid. NSubstitute has cleaner syntax for most cases:

```csharp
// NSubstitute
var repo = Substitute.For<IUserRepository>();
repo.FindByIdAsync("1", Arg.Any<CancellationToken>()).Returns(new User("1", "Alice"));
await repo.Received(1).FindByIdAsync("1", Arg.Any<CancellationToken>());

// Moq equivalent
var mock = new Mock<IUserRepository>();
mock.Setup(r => r.FindByIdAsync("1", It.IsAny<CancellationToken>()))
    .ReturnsAsync(new User("1", "Alice"));
mock.Verify(r => r.FindByIdAsync("1", It.IsAny<CancellationToken>()), Times.Once);
```

Mock interfaces, not concrete classes. If a dependency is hard to mock because it's a concrete class, that's a design signal: extract an interface or redesign.

## FluentAssertions

FluentAssertions produces readable failure messages and supports complex object comparison:

```csharp
// Without FluentAssertions — poor failure messages
Assert.Equal("Alice", user.Name);
Assert.NotNull(user.Email);

// With FluentAssertions — clear, readable, better failure output
user.Name.Should().Be("Alice");
user.Email.Should().NotBeNullOrEmpty();
user.Should().BeEquivalentTo(expected, options => options.Excluding(u => u.CreatedAt));
```

`BeEquivalentTo` does deep structural comparison; it's very useful for asserting complex objects without writing field-by-field assertions.

## Integration testing with WebApplicationFactory

Test ASP.NET Core endpoints against a real (in-memory) server without deploying:

```csharp
public class UsersApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UsersApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real DB with in-memory or test double
                services.AddSingleton<IUserRepository, FakeUserRepository>();
            });
        }).CreateClient();
    }

    [Fact]
    public async Task GetUser_Returns200WithUser()
    {
        var response = await _client.GetAsync("/users/1");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var user = await response.Content.ReadFromJsonAsync<UserDto>();
        user!.Name.Should().Be("Alice");
    }
}
```

`IClassFixture<T>` shares the factory across all tests in the class: the server starts once per class, not per test.

## Async tests

xUnit handles async natively, so return `Task` from test methods:

```csharp
[Fact]
public async Task SaveUser_PersistsToRepository()
{
    await _sut.SaveAsync(new User("1", "Alice"));
    await _repository.Received(1).SaveAsync(Arg.Is<User>(u => u.Name == "Alice"), Arg.Any<CancellationToken>());
}
```

Don't use `.Result` or `.Wait()` in tests; it defeats async and can deadlock.

## Test isolation

Each test should be independent. Shared state causes flaky tests.

- Use constructor setup (xUnit) or `[SetUp]` (NUnit) to create fresh instances per test
- Don't use `static` fields for mocks; they persist across tests
- For database tests, wrap each test in a transaction and roll back: `IDbContextTransaction` with `RollbackAsync()`

## What to watch for in code review

- Tests sharing mock instances across test methods via `static` fields
- `.Result` or `.Wait()` in async tests: blocks the thread and can deadlock
- Assertions on multiple unrelated concerns in a single test (hard to diagnose on failure)
- `[Theory]` without enough cases to actually cover the interesting boundaries
- WebApplicationFactory tests that hit a real external database: use a test double or in-memory DB
- Mocking concrete classes instead of interfaces
