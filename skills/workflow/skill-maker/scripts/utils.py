"""Shared utilities for skill-creator scripts."""

from pathlib import Path



def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def replace_description(content: str, new_description: str) -> str:
    """Return `content` with its frontmatter `description:` field replaced by
    `new_description`, re-serialized as a YAML block scalar. Every other
    frontmatter field (name, metadata, compatibility, ...) and the skill body
    are left untouched, byte-for-byte."""
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    frontmatter = lines[1:end_idx]
    rest = lines[end_idx:]  # the closing '---' line and everything after it

    new_frontmatter: list[str] = []
    i = 0
    replaced = False
    while i < len(frontmatter):
        line = frontmatter[i]
        if line.startswith("description:"):
            replaced = True
            new_frontmatter.append("description: >-")
            for para_line in new_description.split("\n"):
                new_frontmatter.append(f"  {para_line}")
            i += 1
            # Skip the old value's continuation lines (indented lines that
            # followed a block-scalar description), so we don't leave stale
            # fragments of the previous description behind.
            while i < len(frontmatter) and (frontmatter[i].startswith("  ") or frontmatter[i].startswith("\t")):
                i += 1
            continue
        new_frontmatter.append(line)
        i += 1

    if not replaced:
        raise ValueError("SKILL.md frontmatter has no description: field to replace")

    return "\n".join(["---", *new_frontmatter, *rest])
