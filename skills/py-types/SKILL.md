---
name: py-types
description: Python type system advisor. Always use this skill when working with Python type hints, mypy, Protocol, TypedDict, dataclasses, or generics. Use when the user asks "how do I type this in Python", "mypy is complaining", "should I use TypedDict or dataclass", "how do I type a dict", "what's Optional", "how do I make a generic class", "Protocol vs ABC vs TypedDict", "how do I annotate a function that returns X or Y", or "how do I avoid Any". Read this skill before answering any Python type annotation question.
---

# Python Types

Python's type system is gradual: you can add hints incrementally without breaking anything. But partial typing is a trap: unannotated code is treated as `Any` by mypy, and `Any` propagates silently. The goal is enough coverage that mypy can catch real mistakes.

## Start with `--strict` in mypy

The default mypy configuration is lenient. Enable strict mode to get meaningful coverage:

```ini
# mypy.ini or pyproject.toml [tool.mypy]
strict = true
```

Or per-file to adopt gradually:
```python
# mypy: strict
```

Key strict flags: `--disallow-untyped-defs`, `--disallow-any-generics`, `--warn-return-any`. Fix these first. They catch the most real bugs.

## `Any` vs `object`

`Any` is a two-way escape hatch: it's compatible with every type and every type is compatible with it. This means errors hide.

```python
# Bad: Any propagates — x.anything() won't be caught
def process(x: Any) -> Any:
    return x.value

# Better: object is the base type — forces you to narrow before using
def process(x: object) -> str:
    if isinstance(x, MyModel):
        return x.value
    raise TypeError(f"Unexpected type: {type(x)}")
```

Use `Any` only at true integration boundaries (untyped third-party libs) and isolate it with a narrow wrapper.

## Nullable types

Always annotate `None` explicitly. A missing annotation and `Optional[X]` are not the same; the latter is checked.

```python
# Python 3.10+: use the union shorthand
def find_user(id: str) -> User | None: ...

# Earlier versions: use Optional
from typing import Optional
def find_user(id: str) -> Optional[User]: ...

# Bad: return type omitted — mypy treats return as Any
def find_user(id: str):
    ...
```

## TypedDict vs dataclass vs NamedTuple vs Pydantic

| Use | When |
|---|---|
| `TypedDict` | Typing existing dict-shaped data (JSON responses, config dicts) |
| `dataclass` | Mutable structured data with methods; Python-native |
| `NamedTuple` | Immutable records; tuple-compatible |
| `Pydantic BaseModel` | External data with validation (API input, config files) |

```python
# TypedDict — for dict shapes you don't control
from typing import TypedDict

class UserDict(TypedDict):
    id: str
    name: str
    email: str | None

# dataclass — for your own structured data
from dataclasses import dataclass, field

@dataclass
class User:
    id: str
    name: str
    tags: list[str] = field(default_factory=list)
```

Don't use plain `dict[str, Any]` for structured data: it hides the shape and loses all checking.

## Protocol for structural subtyping

Python uses duck typing. `Protocol` lets you express "any object with these methods" without requiring inheritance.

```python
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def shutdown(resource: Closeable) -> None:
    resource.close()

# Works for any class that has .close() — no inheritance required
shutdown(open('file.txt'))
shutdown(db_connection)
```

Prefer `Protocol` over `ABC` when the type relationship is structural rather than nominal. It's more Pythonic and doesn't require modifying the implementing class.

## Generics

Use `TypeVar` to write functions that preserve type information:

```python
from typing import TypeVar

T = TypeVar('T')

def first(items: list[T]) -> T | None:
    return items[0] if items else None

# Return type is inferred correctly:
result: str | None = first(['a', 'b'])  # T = str
```

Constrain `TypeVar` when you need to access members:

```python
from typing import TypeVar
from typing import Protocol

class HasId(Protocol):
    id: str

T = TypeVar('T', bound=HasId)

def get_id(item: T) -> str:
    return item.id
```

Python 3.12+ supports the new `type` statement and `[T]` syntax for generics; use it for new code targeting 3.12+.

## `Literal` and `Final`

`Literal` constrains a value to specific options:

```python
from typing import Literal

Direction = Literal['north', 'south', 'east', 'west']

def move(direction: Direction) -> None: ...

move('north')   # ok
move('up')      # mypy error
```

`Final` marks a name as a constant:

```python
from typing import Final

MAX_RETRIES: Final = 3
MAX_RETRIES = 5  # mypy error
```

## Avoiding circular imports with TYPE_CHECKING

Type annotations can cause circular imports. Use the `TYPE_CHECKING` guard to import only at type-check time:

```python
from __future__ import annotations  # enables postponed evaluation of annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User  # only imported during type checking, not at runtime

def process(user: User) -> None:  # string annotation resolved by mypy
    ...
```

## What to watch for in code review

- Functions with no return type annotation: mypy skips them entirely
- `dict` or `list` used without type parameters (`dict[str, Any]` vs `dict`)
- `Optional[X]` return types where `None` is never actually returned (misleads callers)
- `Any` in return types: errors from the returned value won't be caught downstream
- `# type: ignore` comments without an explanation of why
