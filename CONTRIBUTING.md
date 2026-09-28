# Contributing

This project is released with a [Contributor Code of Conduct](CODE-OF-CONDUCT.md). By participating, you agree to abide by its terms.

## Contents

- [Getting Started](#getting-started)
- [Ways to Contribute](#ways-to-contribute)
- [Skill Structure](#skill-structure)
- [Eval Structure](#eval-structure)
- [Pull Request Guidelines](#pull-request-guidelines)

## Getting Started

No build step, no package manager, no setup. Skills are markdown files. Clone the repo and start editing.

```bash
git clone https://github.com/your-username/proven-skills.git
cd proven-skills
```

To test a skill locally, install it into a project using the install script and try it in Claude Code:

```bash
./install.sh debug        # macOS/Linux
.\install.ps1 debug       # Windows (PowerShell)
```

## Ways to Contribute

### New skills

Add a skill for a domain, workflow, or language tier not yet covered. See [Skill Structure](#skill-structure) for what a skill needs.

Good candidates:
- Domains where Claude tends to give shallow or incorrect guidance without grounding
- Language-specific skills (Python, .NET, Go, etc.) that complement the general-purpose tier
- Workflow skills that bridge existing skills together

### Improving existing skills

- Better guidance in a section that's vague or incomplete
- New sections covering gaps in the current content
- More concrete examples
- Cleaner trigger descriptions (see below; these matter a lot)

### New evals

Each skill ships with at least two evals. Adding evals that test untested behaviors is high-value. See [Eval Structure](#eval-structure).

### Documentation

Updates to the README, usage examples, or install scripts are welcome. Keep examples practical and verified working.

## Skill Structure

Each skill lives at `skills/{name}/SKILL.md`. The frontmatter has two required fields:

```markdown
---
name: skill-name
description: Trigger description (see guidance below).
---
```

### The description field

This is the most important field. Claude Code uses it to decide when to activate the skill. A weak description means the skill fires on the wrong prompts, or doesn't fire at all.

A good description:
- States the domain clearly and early
- Uses assertive language, like "Always use this skill when..." and "Read this skill before...", rather than "Use this skill when..."
- Lists specific phrasings a user might say that should trigger it, including common synonyms and adjacent terms
- Closes with a directive ("Read this skill before answering any X question") to reinforce the trigger
- Is specific enough to avoid false positives on unrelated prompts

Claude tends to answer questions it's confident about directly, without consulting a skill. Assertive trigger language counteracts this tendency. Skills that cover highly specialized or procedural domains (specific framework internals, on-call workflows, migration safety) auto-trigger more reliably than broad general skills. For general-purpose skills, explicit invocation (`/skill-name`) is always reliable.

```markdown
# Too vague: fires on almost anything
description: Help with code quality and best practices.

# Too passive: Claude answers directly and skips the skill
description: TypeScript type system advisor. Use this skill when designing types,
  working with generics, narrowing union types, or when the user says "how do I
  type this", "why is TypeScript complaining", "should I use any here".

# Good: assertive, specific, closes with a directive
description: TypeScript type system advisor. Always use this skill when designing
  TypeScript types, working with generics, narrowing union types, building
  discriminated unions, or avoiding any. Use when the user says "how do I type
  this", "why is TypeScript complaining", "object is possibly null", "how do I
  narrow this", or "how do I constrain a generic". Read this skill before
  answering any TypeScript type question.
```

### Skill content

Skills should be opinionated, not encyclopedic. The goal is to ground Claude in a specific, defensible approach, not to cover every possible option.

- Lead with the core principle, not background
- Use concrete examples (code snippets, not just prose)
- Include a "what to watch for in code review" section where applicable
- Keep sections focused. If a section is getting long, it's probably a separate skill

## Eval Structure

Each eval lives at `evals/{skill-name}/{eval-name}/`, outside the skill's own folder, and contains:

```
evals/
  skill-name/
    eval-name/
      prompt.md       ← the user prompt to test
      graders/
        grader-1.md   ← one grading criterion
        grader-2.md   ← another grading criterion
```

Keeping evals outside `skills/` is required, because `claude plugin eval` won't read eval cases from inside a loaded skill folder. It also keeps them out of users' installs.

To check structure (no API key needed):

```bash
python scripts/validate.py
```

To run a skill's evals for real (this costs money; requires Claude Code 2.1.269 or later):

```bash
claude plugin eval . --tag skill-name --runs 1 --ablation none --max-cost-usd 2 --no-publish
```

Results are written to `evals/results/`, which is gitignored. `--no-publish` keeps the HTML report local instead of publishing it to claude.ai.

### prompt.md

```markdown
---
name: "skill-name: short description of what this eval tests"
tags: ["skill-name", "relevant-tag"]
runs: 3
max_turns: 6
---

The user prompt that should trigger and exercise the skill.
```

A good eval prompt:
- Is a realistic thing a user would actually say
- Exercises a specific behavior the skill is supposed to produce
- Isn't so obvious that any response would pass

### graders

Each grader tests one specific criterion:

```markdown
---
type: llm
criteria: |
  What the agent should do:
  - Specific observable behavior 1
  - Specific observable behavior 2
  - What it should NOT do (negative criterion)
---
```

Each eval should have two graders: one for the primary behavior, one for a supporting behavior or negative criterion. Keep graders focused, one thing per grader, stated as a verifiable claim about the response.

## Pull Request Guidelines

- Search open and closed PRs before submitting to avoid duplicates.
- Keep changes focused: one skill or fix per PR.
- New skills must include at least two evals with two graders each.
- The trigger `description` in the frontmatter should be reviewed carefully. It's the hardest part to get right and has the most impact.
- PR title should be clear: "Add `py-types` skill" or "Improve `debug` eval coverage for async errors".
- Check spelling and grammar. Skill content is read by other developers.

Before merging any skill change, a maintainer will run the **Eval (PR)** workflow from the Actions tab. This runs model-graded evals against the changed skills and fails if any score below 1.0. It requires `ANTHROPIC_API_KEY` to be set as a repo secret. You don't need to run it yourself, but your PR must include passing evals for the workflow to succeed.

Separately, the **Eval (weekly)** workflow runs the full suite every Monday with `--ablation with-without`, comparing every skill against a no-plugin baseline. It doesn't gate anything; it publishes the with/without scores to [`evals/results/published/latest.md`](evals/results/published/latest.md) as a report on what each skill actually contributes.

If a maintainer asks for changes, update your branch and push new commits to the same PR.

Thank you for contributing!
