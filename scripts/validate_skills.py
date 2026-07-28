#!/usr/bin/env python3
"""Validate SKILL.md frontmatter across the repo.

Checks every skills/**/SKILL.md for:
  - present, properly terminated YAML frontmatter
  - `name` present and <= 64 characters
  - `description` present and <= 1024 characters (measured as a YAML
    parser would produce the scalar, i.e. after `>-` folding)

Stdlib-only on purpose: the frontmatter in this repo uses plain scalars
and `>-`/`|`-style block scalars, which a small hand-rolled parser
handles without a PyYAML dependency.

Usage: python3 scripts/validate_skills.py   (from the repo root)
Exit code 0 if all files pass, 1 otherwise.
"""

import re
import sys
from pathlib import Path

NAME_LIMIT = 64
DESCRIPTION_LIMIT = 1024

BLOCK_HEADER_RE = re.compile(r"^([>|])([+-]?)\s*(?:#.*)?$")
TOP_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")


def extract_frontmatter(text):
    """Return the frontmatter lines, or raise ValueError."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter missing (file does not start with ---)")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    raise ValueError("frontmatter unterminated (no closing ---)")


def fold_block_scalar(style, chomp, block_lines, warnings):
    """Produce the scalar value a YAML parser would for a block scalar.

    block_lines are the raw indented lines belonging to the block.
    For `>` (folded), single newlines between content lines become spaces.
    For `|` (literal), newlines are kept.
    Chomping: `-` strips the trailing newline, default keeps exactly one.
    """
    if not block_lines:
        return ""
    indents = [len(l) - len(l.lstrip(" ")) for l in block_lines if l.strip()]
    base_indent = min(indents) if indents else 0
    content = [l[base_indent:] if l.strip() else "" for l in block_lines]

    if any(not l for l in content):
        warnings.append(
            "block scalar contains blank line(s) (paragraph break); "
            "folded length may differ from simple line-joining"
        )
    if style == ">" and any(l.startswith(" ") for l in content if l):
        warnings.append(
            "folded scalar contains more-indented line(s); YAML keeps their "
            "newlines literally, so folded length may differ"
        )

    if style == "|":
        value = "\n".join(content)
    else:
        # Fold: join adjacent non-empty lines with a single space; blank
        # lines become paragraph breaks (\n).
        parts = []
        for line in content:
            if not line:
                parts.append("\n")
            elif parts and parts[-1] not in ("", "\n"):
                parts.append(" " + line)
            else:
                parts.append(line)
        value = "".join(parts)

    if chomp == "-":
        return value
    if chomp == "+":
        return value + "\n"
    return value + "\n"  # clip: single trailing newline


def parse_top_level_scalars(fm_lines, warnings):
    """Parse top-level string fields from frontmatter lines.

    Handles plain scalars, quoted scalars, and `>`/`|` block scalars.
    Nested mappings (e.g. metadata:) are skipped.
    """
    fields = {}
    i = 0
    n = len(fm_lines)
    while i < n:
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith(" "):  # nested content of a previous key
            i += 1
            continue
        m = TOP_KEY_RE.match(line)
        if not m:
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        block = BLOCK_HEADER_RE.match(rest) if rest else None
        if block:
            style, chomp = block.group(1), block.group(2)
            block_lines = []
            i += 1
            while i < n and (fm_lines[i].startswith(" ") or not fm_lines[i].strip()):
                block_lines.append(fm_lines[i])
                i += 1
            # trailing blank lines belong to chomping, not content
            while block_lines and not block_lines[-1].strip():
                block_lines.pop()
            fields[key] = fold_block_scalar(style, chomp, block_lines, warnings)
        else:
            value = rest
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
            i += 1
    return fields


def validate_file(path):
    """Return (errors, warnings, info) for one SKILL.md."""
    errors, warnings = [], []
    info = {"name_len": None, "desc_len": None}
    text = path.read_text(encoding="utf-8")
    try:
        fm_lines = extract_frontmatter(text)
    except ValueError as exc:
        return [str(exc)], warnings, info

    fields = parse_top_level_scalars(fm_lines, warnings)

    name = fields.get("name")
    if name is None or not name.strip():
        errors.append("`name` missing from frontmatter")
    else:
        info["name_len"] = len(name)
        if len(name) > NAME_LIMIT:
            errors.append(
                f"`name` is {len(name)} chars (limit {NAME_LIMIT})"
            )

    desc = fields.get("description")
    if desc is None or not desc.strip():
        errors.append("`description` missing from frontmatter")
    else:
        info["desc_len"] = len(desc)
        if len(desc) > DESCRIPTION_LIMIT:
            errors.append(
                f"`description` is {len(desc)} chars (limit {DESCRIPTION_LIMIT})"
            )

    return errors, warnings, info


def main():
    repo_root = Path(__file__).resolve().parent.parent
    skill_files = sorted((repo_root / "skills").glob("**/SKILL.md"))
    if not skill_files:
        print("FAIL: no skills/**/SKILL.md files found")
        return 1

    failed = 0
    for path in skill_files:
        rel = path.relative_to(repo_root)
        errors, warnings, info = validate_file(path)
        name_len = info["name_len"] if info["name_len"] is not None else "-"
        desc_len = info["desc_len"] if info["desc_len"] is not None else "-"
        status = "FAIL" if errors else "ok"
        print(f"{status:4}  name={name_len:>3}  description={desc_len:>4}  {rel}")
        for w in warnings:
            print(f"      warning: {w}")
        for e in errors:
            print(f"      error: {e}")
        if errors:
            failed += 1

    total = len(skill_files)
    if failed:
        print(f"FAIL: {failed} of {total} SKILL.md files invalid")
        return 1
    print(f"PASS: {total} SKILL.md files valid "
          f"(name <= {NAME_LIMIT}, description <= {DESCRIPTION_LIMIT})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
