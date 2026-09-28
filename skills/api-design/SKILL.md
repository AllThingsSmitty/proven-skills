---
name: api-design
description: Review or design REST and GraphQL APIs for correctness, consistency, and evolvability. Always use this skill when designing a new API, reviewing an existing one, choosing HTTP verbs, designing URL structure, defining error response shapes, thinking through versioning, or writing OpenAPI/Swagger specs. Use when the user says "review this API", "how should I model this resource", "is this endpoint design right", "should I use PUT or PATCH", "is this breaking", or "how should errors look". Use even when the question seems simple.
---

# API Design

An API is a contract with callers you may never meet. Design it to be honest and consistent: easy to use correctly, hard to use wrong. It also has to survive change, meaning you can evolve it without breaking existing clients.

## Resource modeling

Design around resources (nouns), not actions (verbs). A resource is a thing the API manages, not a procedure.

Good: `POST /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/status`
Avoid: `POST /createOrder`, `POST /getOrderById`, `POST /cancelOrder`

When it's genuinely an action with no natural resource (e.g., triggering a batch job, sending a notification), a sub-resource on a relevant entity works well:
`POST /reports/{id}/export`, `POST /users/{id}/password-reset`

**Pluralize consistently.** Pick one convention and hold it: `/users` not `/user`, `/orders/{id}` not `/order/{id}`.

**Nest only one level deep.** `/users/{id}/addresses` is fine. `/users/{id}/addresses/{id}/lines` is where you lose people and create coupling. If the nested resource makes sense standalone, give it a top-level route too.

## HTTP method semantics

| Method | Semantics                        | Idempotent?                    | Safe? |
| ------ | -------------------------------- | ------------------------------ | ----- |
| GET    | Read, no side effects            | Yes                            | Yes   |
| POST   | Create, or non-idempotent action | No                             | No    |
| PUT    | Full replace of a resource       | Yes                            | No    |
| PATCH  | Partial update                   | No (unless designed carefully) | No    |
| DELETE | Remove                           | Yes                            | No    |

- **GET must never have side effects.** Caches, proxies, and clients will retry GETs freely.
- **PUT vs PATCH**: use PUT when the client sends the whole resource; PATCH when sending only changed fields. Don't use PATCH if you can't handle partial updates cleanly; a PUT is more honest.
- **POST for non-idempotent actions** is fine, but make it obvious. Document it; consider making it idempotent via a client-supplied idempotency key.

## Status codes

Use the right code. Vague codes (`200 OK` for everything, `500` for validation errors) make clients guess.

Common codes and when to use them:

- `200 OK`: success with a body
- `201 Created`: resource created; include `Location` header pointing to the new resource
- `204 No Content`: success, no body (e.g., DELETE, some PATCHes)
- `400 Bad Request`: client error, such as invalid syntax, a missing required field, or a constraint violation
- `401 Unauthorized`: not authenticated (confusingly named; means "prove who you are")
- `403 Forbidden`: authenticated but not authorized for this action
- `404 Not Found`: resource doesn't exist _or_ the caller doesn't have permission to know it exists (see: 403 vs 404 for security-sensitive resources)
- `409 Conflict`: state conflict (e.g., optimistic lock failure, duplicate key)
- `422 Unprocessable Entity`: syntactically valid but semantically wrong (good for business rule violations)
- `429 Too Many Requests`: rate limited; include `Retry-After`
- `500 Internal Server Error`: something unexpected went wrong; don't leak stack traces

## Error shapes

Errors must be machine-readable, not just human-readable. Callers need to handle errors programmatically.

A solid error shape:

```json
{
  "error": {
    "code": "VALIDATION_FAILED", // stable machine-readable code
    "message": "Email is required.", // human-readable, localizable
    "field": "email", // for field-level errors
    "request_id": "abc-123" // for support/tracing correlation
  }
}
```

Rules:

- `code` must be a stable, documented string; never change it once published
- Don't use HTTP status codes as the only signal; wrap them with semantic codes
- For validation failures, enumerate all errors in one response. Don't make the client fix one field at a time
- Never include stack traces, internal paths, or database errors in production responses

## Versioning

**URL versioning** (`/v1/`, `/v2/`) is the most practical approach for most APIs. It's explicit, cacheable, and easy to route. The downside is that clients have to opt in to upgrades.

**Header versioning** (`Accept: application/vnd.api+json;version=2`) is cleaner theoretically but harder to test and debug.

**No versioning** works only if you commit to never breaking clients, which means additive-only changes forever. Viable for internal APIs with a small, known set of consumers.

Whatever you choose, establish the strategy before shipping v1. Retrofitting versioning is painful.

## Breaking vs non-breaking changes

**Non-breaking (safe to ship without a new version):**

- Adding optional fields to a response
- Adding optional query parameters
- Adding new endpoints
- Adding new error codes for new error conditions

**Breaking (requires a new version or deprecation window):**

- Removing or renaming a field
- Changing a field's type
- Changing HTTP method for an endpoint
- Adding a required field to a request
- Changing the meaning of an existing field or status code

When you're unsure: if any existing client that works today would break after the change, it's breaking.

## Pagination

For any collection that can grow, paginate from day one. Retrofitting it is a breaking change.

**Cursor-based** (preferred for most cases): opaque cursor in the response, client passes it back. Stable under concurrent inserts/deletes. Doesn't allow random access but almost nothing needs it.

**Offset-based** (`?page=2&limit=20`): simple, allows random access, but unstable: a concurrent insert shifts every page. Acceptable for small, stable datasets.

Response shape:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "opaque-token",
    "has_more": true
  }
}
```

## Auth conventions

- Authenticate with `Authorization: Bearer <token>` for API tokens and JWTs, not cookies (unless you're a browser-first API)
- Distinguish 401 (not authenticated) from 403 (authenticated but not allowed)
- Don't put credentials in query strings; they end up in server logs and browser history
- For machine-to-machine, prefer short-lived tokens with refresh over long-lived static secrets

## GraphQL-specific

**N+1 is the first thing to solve.** Any field resolver that executes a query per parent will kill you at scale. Use DataLoader (or equivalent) for batching.

**Limit query depth and complexity.** Unbounded nested queries are a DoS vector. Set a max depth (typically 7-10 levels) and a complexity budget.

**Pagination in GraphQL**: use the Relay cursor connection spec, since it's what clients expect and tools understand.

**Mutations should return the mutated resource**, not just a success flag. Clients need to update their cache.

**Errors in GraphQL**: the top-level `errors` array is for execution errors; use a union type (`SuccessResult | ErrorResult`) for business logic errors that are part of the expected contract.
