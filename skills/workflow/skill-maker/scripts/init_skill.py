#!/usr/bin/env python3
"""
Scaffold a new, spec-valid skill directory with versioned frontmatter.

Usage:
    python init_skill.py <skill-name> --path <parent-dir> [--description "..."]
                         [--author your-name] [--with-scripts] [--with-references]
                         [--with-assets]

Creates <parent-dir>/<skill-name>/SKILL.md with frontmatter that passes
quick_validate.py (name rules, description, metadata.author + metadata.version "1.0.0" (semver x.y.z)),
plus optional resource directories, then validates the result.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_TEMPLATE = """---
name: {name}
description: {description}
metadata:
  author: {author}
  version: "1.0.0"
---

# {title}

<!-- One-paragraph statement of what this skill helps the agent do and the
     outcome it produces. Judge every line below by whether it makes the
     agent's behavior more predictable. -->

## Instructions

<!-- Step-by-step procedure. Teach how to approach the class of problem, not
     the answer to one instance. Pick defaults, not menus. Match specificity
     to fragility: exact commands for fragile operations, freedom + a why for
     flexible ones. -->

1. ...
2. ...

## Gotchas

<!-- The highest-value section: concrete, environment-specific facts that
     defy reasonable assumptions. Add an entry every time the agent makes a
     mistake you have to correct. Delete this section only if truly empty. -->

- ...

<!-- Optional sections as needed:
## Output format   (give a concrete template — agents pattern-match well)
## Completion criteria   (checkable done-ness so the agent doesn't stop early)
References go in references/ with explicit load triggers ("read X when Y").
Deterministic, frequently-reinvented logic goes in scripts/. -->
"""


def validate_name(name: str) -> str | None:
    if not 1 <= len(name) <= 64:
        return f"name must be 1-64 characters (got {len(name)})"
    if not re.fullmatch(r"[a-z0-9-]+", name):
        return "name may only contain lowercase letters, digits, and hyphens"
    if name.startswith("-") or name.endswith("-"):
        return "name must not start or end with a hyphen"
    if "--" in name:
        return "name must not contain consecutive hyphens"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new skill directory")
    parser.add_argument("name", help="Skill name (kebab-case; becomes the directory name)")
    parser.add_argument("--path", type=Path, default=Path.home()/".claude/skills", help="Parent directory the skill folder is created in (default: ~/.claude/skills)")
    parser.add_argument("--description", default="TODO: what this skill does AND when to use it (this is the trigger — be pushy and specific).", help="Frontmatter description")
    parser.add_argument("--author", default="anonymous", help='metadata.author value (default: anonymous — set to your own name)')
    parser.add_argument("--with-scripts", action="store_true", help="Create scripts/ directory")
    parser.add_argument("--with-references", action="store_true", help="Create references/ directory")
    parser.add_argument("--with-assets", action="store_true", help="Create assets/ directory")
    args = parser.parse_args()

    err = validate_name(args.name)
    if err:
        print(f"Invalid skill name: {err}", file=sys.stderr)
        return 1

    skill_dir = args.path / args.name
    if skill_dir.exists():
        print(f"Refusing to overwrite existing directory: {skill_dir}", file=sys.stderr)
        return 1

    skill_dir.mkdir(parents=True)
    title = args.name.replace("-", " ").title()
    # json.dumps produces a valid YAML double-quoted scalar (handles colons/quotes)
    (skill_dir / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=args.name, description=json.dumps(args.description), author=args.author, title=title)
    )
    for flag, sub in [(args.with_scripts, "scripts"), (args.with_references, "references"), (args.with_assets, "assets")]:
        if flag:
            (skill_dir / sub).mkdir()

    print(f"Created {skill_dir}")

    # Validate what we just created so a broken template never ships silently
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from quick_validate import validate_skill  # type: ignore
        valid, message = validate_skill(skill_dir)
        print(f"Validation: {message}")
        return 0 if valid else 1
    except ImportError:
        print("Validation skipped (quick_validate.py not importable)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
