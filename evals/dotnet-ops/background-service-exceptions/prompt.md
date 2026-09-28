---
name: "dotnet-ops: warns about silent BackgroundService failures"
tags: ["dotnet-ops", "reliability"]
runs: 3
max_turns: 6
---

I have a background job in my ASP.NET Core app using BackgroundService that processes a queue. Sometimes it just stops processing: no errors in the logs, the app keeps running, but the job is dead. What's happening?
