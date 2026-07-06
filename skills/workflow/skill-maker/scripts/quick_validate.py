#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import yaml
from pathlib import Path

def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Spec properties plus Claude Code frontmatter extensions seen in the wild.
    # Unknown keys are reported as a warning, not a failure — harnesses ignore
    # what they don't understand, and hard-failing here rejects valid skills.
    ALLOWED_PROPERTIES = {
        'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility',
        # Claude Code extensions
        'model', 'context', 'effort', 'user-invocable', 'disable-model-invocation',
        'argument-hint', 'homepage', 'when_to_use',
    }
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    warnings = []
    if unexpected_keys:
        warnings.append(f"non-standard frontmatter key(s): {', '.join(sorted(unexpected_keys))}")

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    # Spec: name must match the parent directory name
    dir_name = skill_path.resolve().name
    if name and dir_name != name:
        return False, f"Name '{name}' must match the skill directory name '{dir_name}' (agentskills.io spec)"

    # Toolkit policy: every skill carries metadata.author and metadata.version (semver "x.y.z").
    # Hard fail — an unversioned/mis-versioned skill can't ship (see SKILL.md "Versioning").
    metadata = frontmatter.get('metadata')
    if not isinstance(metadata, dict):
        return False, "Missing 'metadata' block in frontmatter. Required: metadata.author and metadata.version (e.g. version: \"1.0.0\")"
    version = metadata.get('version')
    if version is None:
        return False, "Missing 'metadata.version'. Every skill must be versioned semver x.y.z (e.g. \"1.0.0\") and bumped on update."
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        return False, f"metadata.version must be a quoted semver string x.y.z (MAJOR.MINOR.PATCH), e.g. \"1.0.0\" (got {version!r} — \"1.0\" is invalid; unquoted YAML also turns 1.0 into a float)"
    author = metadata.get('author')
    if not author or not isinstance(author, str):
        return False, "Missing 'metadata.author'. Every skill must declare its author (e.g. your-name)."
    # requires (optional): when present, must be a comma-separated string of tool names.
    requires = metadata.get('requires')
    if requires is not None and not isinstance(requires, str):
        return False, f"metadata.requires must be a comma-separated string of tool names (e.g. \"cmux, gh, git\"), got {requires!r}. Omit it entirely if the skill has no external deps."

    # Toolkit policy: skills must be portable and impersonal. No user-specific
    # absolute paths (use ~ instead), and the author's personal name stays in
    # metadata.author only — never in prose ("Jane's toolkit", "Jane's fork").
    body = content[match.end():]
    import re as _re
    abs_paths = sorted(set(_re.findall(r'/(?:Users|home)/[A-Za-z0-9_.-]+', content)))
    if abs_paths:
        return False, f"User-specific absolute path(s) in SKILL.md: {', '.join(abs_paths[:3])}. Use ~/ paths instead."
    # Occurrences of the full author slug (e.g. in versioning examples) are
    # legitimate metadata usage — strip them before hunting for prose mentions
    body_scrubbed = _re.sub(_re.escape(author), '', body, flags=_re.IGNORECASE)
    author_parts = [w for w in _re.split(r'[-_.]', author.lower()) if len(w) > 2]
    for part in author_parts:
        if _re.search(r'\b' + _re.escape(part) + r'\b', body_scrubbed, _re.IGNORECASE):
            warnings.append(f"author's personal name '{part}' appears in the skill body — keep names in metadata.author only")
            break

    if warnings:
        return True, "Skill is valid (warnings: " + "; ".join(warnings) + ")"
    return True, "Skill is valid!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)
    
    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)