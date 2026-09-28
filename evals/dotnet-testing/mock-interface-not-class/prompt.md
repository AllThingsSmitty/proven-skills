---
name: "dotnet-testing: recommends mocking interfaces over concrete classes"
tags: ["dotnet-testing", "mocking"]
runs: 3
max_turns: 6
---

I'm trying to mock my `EmailService` class in a test but Moq is complaining that it can't mock it. The class doesn't implement an interface. It's just a plain class with a `SendAsync` method. How do I mock it?
