---
name: pr-prep
description: Pre-pull-request review and readiness check. Always use this skill before opening a PR, reviewing a diff, writing a PR description, or checking if changes are ready to merge. Use when the user says "help me prep this PR", "is this ready to merge?", "review my changes before I submit", "check my diff", "write a PR description", "what's the blast radius of this change", or any time changes are being packaged for review. Do not skip this skill when any PR-related task is requested.
---

# PR Prep

A PR is a unit of communication as much as a unit of code change. Before you open one, review it the way a careful reviewer would, catching the issues you'd want flagged before anyone else has to deal with them.

## Step 1: Read your own diff

Pull up the full diff and read it cold, as if you didn't write it:

```bash
git diff main...HEAD   # or whatever the base branch is
```

What to look for:

- **Unintended changes**: whitespace noise, reformatted files, debug logging left in, commented-out code that shouldn't be there
- **Incomplete work**: TODOs added but not addressed, stubs that aren't wired up, feature flags that haven't been connected
- **Sensitive data**: credentials, tokens, API keys, internal hostnames; anything that shouldn't be in source control
- **Scope creep**: changes unrelated to the PR's stated purpose. Pull these into a separate PR or a follow-up commit.

## Step 2: Test coverage check

For every meaningful behavior change in the diff:

- Is there a test that would fail if this code were reverted?
- Are error paths and edge cases covered, not just the happy path?
- If this fixes a bug, is there a regression test?

Missing test coverage isn't always a blocker, but it should be a deliberate choice, not an oversight. If you're leaving coverage thin, say why in the PR description.

## Step 3: Migration and deployment safety

If the change touches a database, schema, or persisted data format:

- Is the migration reversible? Can you roll back the app without rolling back the migration?
- Does the migration need to be run before, during, or after the code deploys? State this explicitly.
- Does the migration lock tables or have other performance implications on large datasets?
- Are there any backward-compatibility concerns if multiple app versions are running simultaneously?

If the change modifies an API (REST, GraphQL, RPC, message schema):

- Are existing consumers broken? If the API is internal and all consumers are being updated in this PR, fine. If external consumers exist, you need a versioning or deprecation strategy.
- Are new required fields added to an existing endpoint? That's a breaking change.

## Step 4: Blast radius

Think about what breaks if this change is wrong:

- What's the worst-case impact of a bug in this code?
- Is the rollback path clear and fast?
- Is this change behind a feature flag, or does it go live for all users immediately on deploy?
- Are there dependent services, jobs, or consumers that could be affected?

If the blast radius is large, say so in the PR description and suggest a staged rollout or flag.

## Step 5: Documentation and callouts

- Update any documentation that describes behavior this PR changes (README, API docs, runbooks, architecture diagrams)
- If the PR has non-obvious side effects or requires action from other teams, call them out explicitly at the top of the description
- If there are known limitations or follow-up work, link or reference them

## Writing the PR description

A good PR description tells the reviewer:

1. **What** changed (a sentence or two)
2. **Why** it changed (the motivation: link to the issue or explain the context)
3. **How** to test or verify it
4. **What to watch for**: any risky areas, non-obvious decisions, or things the reviewer should look closely at

Structure:

```
## What
Brief summary of the change.

## Why
Context: what problem this solves, what request or issue prompted it.

## Testing
How to verify this works. Include manual test steps if there's no automated coverage.

## Notes
Migration steps, deployment order, rollback plan, known limitations, follow-ups.
```

Don't write a PR description that just restates the commit messages. The description should give the reviewer enough context to understand the _why_ without reading the full diff first.

## Before you hit "Open PR"

Quick final check:

- [ ] Branch is rebased or merged with the base branch and has no conflicts
- [ ] CI is green (don't open a PR with a known failing build)
- [ ] Self-review done; diff read, no debug artifacts, no unintended changes
- [ ] PR description written with context, not just "fixes stuff"
- [ ] Right reviewers assigned: people who know the affected areas
- [ ] Size is reviewable: if the diff is >500 lines of logic changes, consider splitting
