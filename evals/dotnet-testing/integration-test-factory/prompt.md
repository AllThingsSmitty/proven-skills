---
name: "dotnet-testing: introduces WebApplicationFactory for API tests"
tags: ["dotnet-testing", "integration"]
runs: 3
max_turns: 6
---

I want to write tests for my ASP.NET Core API endpoints, not unit tests for individual classes, but tests that actually hit the route and go through the middleware pipeline. Do I need to spin up a real server for that?
