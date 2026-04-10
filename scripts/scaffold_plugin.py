"""
scaffold_plugin.py

Scaffolds a new plugins/<name>/commons/ directory tree for a veiled-market plugin.
Generates plugin.base.json, hooks.json, a command stub, per-skill SKILL.md stubs,
and an empty references/ directory.

Usage (from veiled-market/):
    python3 scripts/scaffold_plugin.py \\
        --name <plugin-name> \\
        --description "..." \\
        --version 0.1.0 \\
        --command <verb> \\
        --skills skill1,skill2 \\
        [--author "..."] \\
        [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path


MARKETPLACE_ROOT = Path(__file__).resolve().parent.parent

_KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_kebab(name: str) -> bool:
    return bool(_KEBAB_RE.match(name))


def _title(slug: str) -> str:
    return slug.replace("-", " ").title()


# ---------------------------------------------------------------------------
# File content builders
# ---------------------------------------------------------------------------

def _plugin_base_json(name: str, version: str, description: str,
                      author: str, skills: list[str]) -> str:
    skills_entries = [{"path": f"skills/{s}", "user-invocable": False} for s in skills]
    data = {
        "name": name,
        "version": version,
        "description": description,
        "author": {"name": author},
        "license": "MIT",
        "keywords": [],
        "tags": [],
        "skills": skills_entries,
        "agents": [],
        "hooks": "hooks.json",
    }
    return json.dumps(data, indent=2) + "\n"


def _hooks_json() -> str:
    return json.dumps({"version": 1, "hooks": {}}, indent=2) + "\n"


def _command_md(name: str, command: str, description: str, skills: list[str]) -> str:
    desc_snippet = description[:60]
    rows = "\n".join(f"| {s} | `skills/{s}/SKILL.md` |" for s in skills)
    return f"""\
---
name: {command}
description: >
  {desc_snippet}. Trigger on: /{command}.
argument-hint: <action> [plugin] [args]
---

# /{command}

Route to the {name} skill.

## Arguments

The user provided: `$ARGUMENTS`

Parse first argument as **action** (required).

## Routing

| Action | Skill loaded |
|--------|-------------|
{rows}
"""


def _skill_md(plugin: str, skill: str) -> str:
    plugin_title = _title(plugin)
    skill_title = _title(skill)
    return f"""\
---
name: {plugin}-{skill}
description: >
  TODO: describe what this skill does (≤60 words).
user-invocable: false
---

# {plugin_title} — {skill_title}

TODO: Implement this skill.

## Steps

1. Step one
2. Step two
"""


# ---------------------------------------------------------------------------
# Core scaffolding logic
# ---------------------------------------------------------------------------

def scaffold_plugin(name: str, description: str, version: str, command: str,
                    skills: list[str], author: str, dry_run: bool) -> int:
    if not _is_kebab(name):
        print(
            f"[error] --name must be kebab-case (e.g. my-plugin). Got: {name!r}",
            file=sys.stderr,
        )
        return 1

    commons_dir = MARKETPLACE_ROOT / "plugins" / name / "commons"

    if commons_dir.exists():
        print(
            f"[error] {commons_dir.relative_to(MARKETPLACE_ROOT)} already exists. "
            "Aborting to prevent overwrite.",
            file=sys.stderr,
        )
        return 1

    created: list[tuple[str, str]] = []  # (rel_path, kind)

    def _write(rel: Path, content: str) -> None:
        full = commons_dir / rel
        rel_display = str(Path("plugins") / name / "commons" / rel)
        ext = rel.suffix.lstrip(".")
        kind = ext if ext else "dir"
        created.append((rel_display, kind))
        if not dry_run:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)

    def _touch(rel: Path) -> None:
        full = commons_dir / rel
        rel_display = str(Path("plugins") / name / "commons" / rel)
        created.append((rel_display, "gitkeep"))
        if not dry_run:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.touch()

    _write(Path("plugin.base.json"), _plugin_base_json(name, version, description, author, skills))
    _write(Path("hooks.json"), _hooks_json())
    _write(Path("commands") / f"{command}.md", _command_md(name, command, description, skills))

    for skill in skills:
        _write(Path("skills") / skill / "SKILL.md", _skill_md(name, skill))

    _touch(Path("references") / ".gitkeep")

    # Print results table
    prefix = "[dry-run] Would create" if dry_run else "Created"
    print(f"{prefix}: plugins/{name}/commons/\n")
    col_w = max(len(p) for p, _ in created) + 2
    print(f"  {'File':<{col_w}}  Type")
    print(f"  {'-' * col_w}  --------")
    for rel_path, kind in created:
        print(f"  {rel_path:<{col_w}}  {kind}")

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a new veiled-market plugin commons/ directory tree."
    )
    parser.add_argument("--name", required=True, help="Plugin name (kebab-case)")
    parser.add_argument("--description", required=True, help="Short plugin description")
    parser.add_argument("--version", default="0.1.0",
                        help="Initial version (default: 0.1.0)")
    parser.add_argument("--command", required=True,
                        help="Philosopher verb for the entry command (e.g. forge, probe)")
    parser.add_argument("--skills", required=True,
                        help="Comma-separated skill names (e.g. create,update,delete)")
    parser.add_argument("--author", default="veiled-market contributors",
                        help='Author name (default: "veiled-market contributors")')
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be created without writing any files")
    args = parser.parse_args()

    skills = [s.strip() for s in args.skills.split(",") if s.strip()]
    if not skills:
        print("[error] --skills must contain at least one skill name.", file=sys.stderr)
        sys.exit(1)

    rc = scaffold_plugin(
        name=args.name,
        description=args.description,
        version=args.version,
        command=args.command,
        skills=skills,
        author=args.author,
        dry_run=args.dry_run,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
