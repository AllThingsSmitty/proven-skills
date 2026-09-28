---
name: py-testing
description: Python testing advisor. Always use this skill when writing Python tests, working with pytest, fixtures, conftest, mocking, patching, or parametrize. Use when the user asks "how do I mock this in Python", "how do I patch a function", "where should I patch", "why isn't my patch working", "how do I parametrize tests", "how do I test async Python code", "how do I use fixtures", or "pytest conftest". Read this skill before writing any Python test or debugging a failing mock or patch.
---

# Python Testing

pytest is the standard. Its fixture system is more composable than unittest's setUp/tearDown, its output is more readable, and parametrize eliminates test duplication cleanly. Use it.

## Fixtures

Fixtures are pytest's dependency injection system. A test declares what it needs; pytest provides it.

```python
# conftest.py — fixtures available to all tests in the directory
import pytest
from myapp.db import Database

@pytest.fixture
def db():
    database = Database(':memory:')
    database.migrate()
    yield database          # yield instead of return for teardown
    database.close()        # runs after the test completes

# test_users.py
def test_create_user(db):   # pytest injects the db fixture
    user = db.create_user('Alice')
    assert user.name == 'Alice'
```

**Scope**: fixtures run once per test by default. Use `scope='module'` or `scope='session'` for expensive resources (database connections, containers) that are safe to share:

```python
@pytest.fixture(scope='session')
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()
```

**conftest.py**: put shared fixtures here, not in individual test files. pytest discovers conftest.py automatically at every directory level.

## Parametrize

Replace repeated test functions with `@pytest.mark.parametrize`:

```python
# Bad: three functions testing the same logic with different inputs
def test_valid_email_with_plus(): ...
def test_valid_email_simple(): ...
def test_invalid_email_no_at(): ...

# Good: one parametrized test
@pytest.mark.parametrize('email,expected', [
    ('user@example.com', True),
    ('user+tag@example.com', True),
    ('not-an-email', False),
    ('', False),
])
def test_validate_email(email: str, expected: bool):
    assert validate_email(email) == expected
```

Each case appears as a separate test in the output with its own pass/fail status.

## Mocking: patch where it's used, not where it's defined

The most common pytest mistake. `patch` replaces the name in the module under test, not in the module where the object is defined.

```python
# myapp/users.py
from myapp.email import send_email   # imported here

def register(data):
    user = create_user(data)
    send_email(user.email)           # called as send_email, not email.send_email
    return user
```

```python
# test_users.py
from unittest.mock import patch

# Bad: patches in the wrong module
@patch('myapp.email.send_email')
def test_register(mock_send):
    register({'name': 'Alice', 'email': 'a@example.com'})
    mock_send.assert_called_once()   # fails — the name in users.py isn't patched

# Good: patches where the name is used
@patch('myapp.users.send_email')
def test_register(mock_send):
    register({'name': 'Alice', 'email': 'a@example.com'})
    mock_send.assert_called_once()   # passes
```

## pytest-mock for cleaner syntax

`pytest-mock` provides a `mocker` fixture that wraps `unittest.mock` with automatic cleanup:

```python
def test_register(mocker):
    mock_send = mocker.patch('myapp.users.send_email')
    register({'name': 'Alice', 'email': 'a@example.com'})
    mock_send.assert_called_once_with('a@example.com')
```

No `@patch` decorator, no manual cleanup: the mock is restored after the test automatically.

## Testing async code

Use `pytest-asyncio` for async tests:

```python
# pyproject.toml
# [tool.pytest.ini_options]
# asyncio_mode = "auto"

import pytest

@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user('123')
    assert user.id == '123'
```

With `asyncio_mode = "auto"` in config, the `@pytest.mark.asyncio` decorator is optional.

For async fixtures:

```python
@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(app=app) as client:
        yield client
```

## Useful built-in fixtures

| Fixture       | What it provides                                            |
| ------------- | ----------------------------------------------------------- |
| `tmp_path`    | A temporary directory unique to the test (cleaned up after) |
| `monkeypatch` | Safely patch attributes, env vars, dict items               |
| `capfd`       | Capture stdout/stderr                                       |
| `capsys`      | Same, for Python-level output                               |

```python
def test_reads_env_var(monkeypatch):
    monkeypatch.setenv('API_KEY', 'test-key')
    result = get_api_key()
    assert result == 'test-key'
    # env var is restored automatically after the test
```

Prefer `monkeypatch` over `os.environ['KEY'] = 'value'` in tests; it restores state automatically and is safe across parallel test runs.

## Test the public interface

Test behavior through the public API, not internal implementation. Private methods are an implementation detail. They change without notice and shouldn't need direct tests.

```python
# Bad: testing a private method directly
def test_build_query():
    service = UserService(db)
    query = service._build_query(filters)  # testing internals
    assert '...' in query

# Good: testing the observable behavior
def test_search_filters_by_name(db):
    db.insert_user(name='Alice')
    db.insert_user(name='Bob')
    results = service.search(name='Alice')
    assert len(results) == 1
    assert results[0].name == 'Alice'
```

## What to watch for in code review

- Patching at the definition location instead of the usage location
- Fixtures with no teardown for resources that need cleanup
- Duplicate test functions that should be parametrized
- `os.environ` set directly in tests without cleanup (use `monkeypatch.setenv`)
- Async test functions missing `@pytest.mark.asyncio` (they run synchronously and silently pass)
- Tests asserting on internal state instead of observable behavior
