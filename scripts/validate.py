#!/usr/bin/env python3
"""Validate skills in skills/ and their eval suites in evals/."""

import os
import re
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT_DIR, "skills")
EVALS_DIR = os.path.join(ROOT_DIR, "evals")

# Output directory written by `claude plugin eval`; not a skill's eval suite.
EVAL_RESULTS_DIR = "results"

SKILL_FRONTMATTER_REQUIRED = {"name", "description"}
PROMPT_FRONTMATTER_REQUIRED = {"name", "tags", "runs", "max_turns"}
GRADER_TYPE_REQUIRED = {
    "llm": {"type", "criteria"},
    "regex": {"type", "pattern", "match", "target"},
    "tool_used": {"type", "tool", "input_match"},
}

MIN_EVALS = 2
MIN_GRADERS = 2


def parse_frontmatter(path):
    """Return the set of keys present in a file's YAML frontmatter block."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    if not content.startswith("---"):
        return set()

    end = content.find("---", 3)
    if end == -1:
        return set()

    block = content[3:end]
    keys = set()
    for line in block.splitlines():
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:", line)
        if m:
            keys.add(m.group(1))
    return keys


def _read_frontmatter_value(path, key):
    """Return the scalar value for a given key from a file's YAML frontmatter."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    for line in content[3:end].splitlines():
        m = re.match(rf"^{re.escape(key)}\s*:\s*(.+)", line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def validate():
    errors = []

    if not os.path.isdir(SKILLS_DIR):
        print(f"ERROR: skills/ directory not found at {SKILLS_DIR}")
        sys.exit(1)

    skill_names = sorted(
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
    )

    if os.path.isdir(EVALS_DIR):
        for d in sorted(os.listdir(EVALS_DIR)):
            if d == EVAL_RESULTS_DIR or not os.path.isdir(os.path.join(EVALS_DIR, d)):
                continue
            if d not in skill_names:
                errors.append(f"evals/{d}: no matching skill in skills/")

    for skill in skill_names:
        skill_dir = os.path.join(SKILLS_DIR, skill)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        evals_dir = os.path.join(EVALS_DIR, skill)

        if os.path.isdir(os.path.join(skill_dir, "evals")):
            errors.append(f"skills/{skill}/evals: evals must live in evals/{skill}/, not inside the skill")

        if not os.path.isfile(skill_md):
            errors.append(f"{skill}: missing SKILL.md")
        else:
            keys = parse_frontmatter(skill_md)
            if keys is None:
                errors.append(f"{skill}/SKILL.md: could not read file")
            else:
                missing = SKILL_FRONTMATTER_REQUIRED - keys
                if missing:
                    errors.append(f"{skill}/SKILL.md: missing frontmatter fields: {', '.join(sorted(missing))}")

        if not os.path.isdir(evals_dir):
            errors.append(f"{skill}: missing evals/{skill}/ directory")
            continue

        eval_names = sorted(
            d for d in os.listdir(evals_dir)
            if os.path.isdir(os.path.join(evals_dir, d))
        )

        if len(eval_names) < MIN_EVALS:
            errors.append(f"{skill}: has {len(eval_names)} eval(s), need at least {MIN_EVALS}")

        for eval_name in eval_names:
            eval_dir = os.path.join(evals_dir, eval_name)
            prompt_md = os.path.join(eval_dir, "prompt.md")
            graders_dir = os.path.join(eval_dir, "graders")

            if not os.path.isfile(prompt_md):
                errors.append(f"evals/{skill}/{eval_name}: missing prompt.md")
            else:
                keys = parse_frontmatter(prompt_md)
                if keys is None:
                    errors.append(f"evals/{skill}/{eval_name}/prompt.md: could not read file")
                else:
                    missing = PROMPT_FRONTMATTER_REQUIRED - keys
                    if missing:
                        errors.append(
                            f"evals/{skill}/{eval_name}/prompt.md: missing frontmatter fields: {', '.join(sorted(missing))}"
                        )

            if not os.path.isdir(graders_dir):
                errors.append(f"evals/{skill}/{eval_name}: missing graders/ directory")
                continue

            grader_files = sorted(
                f for f in os.listdir(graders_dir)
                if f.endswith(".md")
            )

            if len(grader_files) < MIN_GRADERS:
                errors.append(
                    f"evals/{skill}/{eval_name}: has {len(grader_files)} grader(s), need at least {MIN_GRADERS}"
                )

            for grader_file in grader_files:
                grader_path = os.path.join(graders_dir, grader_file)
                keys = parse_frontmatter(grader_path)
                if keys is None:
                    errors.append(f"evals/{skill}/{eval_name}/graders/{grader_file}: could not read file")
                elif "type" not in keys:
                    errors.append(f"evals/{skill}/{eval_name}/graders/{grader_file}: missing frontmatter field: type")
                else:
                    grader_type = _read_frontmatter_value(grader_path, "type")
                    required = GRADER_TYPE_REQUIRED.get(grader_type)
                    if required is None:
                        errors.append(
                            f"evals/{skill}/{eval_name}/graders/{grader_file}: unknown grader type '{grader_type}'"
                        )
                    else:
                        missing = required - keys
                        if missing:
                            errors.append(
                                f"evals/{skill}/{eval_name}/graders/{grader_file}: missing frontmatter fields: {', '.join(sorted(missing))}"
                            )

    if errors:
        print(f"Found {len(errors)} error(s):\n")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"All {len(skill_names)} skills passed validation.")


if __name__ == "__main__":
    validate()
