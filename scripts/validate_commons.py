"""
validate_commons.py

Structural validator for a veiled-market plugin's commons/ directory.
Checks file presence, plugin.base.json schema, frontmatter fields, skills/agents
wiring, and description word counts.

Usage (from veiled-market/):
    python3 scripts/validate_commons.py --plugin <name>
    python3 scripts/validate_commons.py --all
    python3 scripts/validate_commons.py --plugin <name> --json
"""

import argparse
import json
import re
import sys
from pathlib import Path


MARKETPLACE_ROOT = Path(__file__).resolve().parent.parent

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# Frontmatter parser (stdlib-only, mirrors build-platforms.py)
# ---------------------------------------------------------------------------

def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter between --- delimiters (stdlib only)."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end == -1:
        return {}

    fm: dict = {}
    i = 1
    while i < end:
        line = lines[i]
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val in (">-", ">", "|", "|-"):
                body_lines = []
                j = i + 1
                while j < end and (lines[j].startswith("  ") or lines[j].startswith("\t")):
                    body_lines.append(lines[j].strip())
                    j += 1
                fm[key] = " ".join(body_lines) if val in (">-", ">") else "\n".join(body_lines)
                i = j
                continue
            elif val.lower() == "true":
                fm[key] = True
            elif val.lower() == "false":
                fm[key] = False
            elif val.startswith("[") and val.endswith("]"):
                fm[key] = [x.strip() for x in val[1:-1].split(",") if x.strip()]
            else:
                fm[key] = val
        i += 1
    return fm


def _word_count(text: str) -> int:
    """Count words in a description, stripping surrounding quotes."""
    cleaned = text.strip().strip("'\"")
    return len(cleaned.split()) if cleaned else 0


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def validate_plugin(plugin: str) -> dict:
    """Run all structural checks for plugins/<plugin>/commons/. Returns result dict."""
    commons_dir = MARKETPLACE_ROOT / "plugins" / plugin / "commons"

    errors: list[dict] = []
    warnings: list[dict] = []
    passed = 0

    def _err(code: str, path: str, message: str) -> None:
        errors.append({"code": code, "path": path, "message": message})

    def _warn(code: str, path: str, message: str) -> None:
        warnings.append({"code": code, "path": path, "message": message})

    def _pass() -> None:
        nonlocal passed
        passed += 1

    # Check 1: commons/ exists
    if not commons_dir.exists():
        _err("MISSING_DIR", f"plugins/{plugin}/commons", "commons/ directory not found")
        return {"plugin": plugin, "errors": errors, "warnings": warnings, "passed": passed}
    _pass()

    # Check 2: plugin.base.json exists and is valid JSON
    base_path = commons_dir / "plugin.base.json"
    base: dict = {}
    if not base_path.exists():
        _err("MISSING_FILE", "plugin.base.json", "plugin.base.json not found in commons/")
    else:
        try:
            base = json.loads(base_path.read_text())
            _pass()
        except json.JSONDecodeError as exc:
            _err("INVALID_JSON", "plugin.base.json", f"Invalid JSON: {exc}")

    # Check 3: required fields (name, version, description, skills non-empty)
    if base:
        missing_fields = []
        for field in ("name", "version", "description"):
            if not base.get(field):
                missing_fields.append(field)
        skills_val = base.get("skills")
        skills_empty = (
            skills_val is None
            or (isinstance(skills_val, list) and len(skills_val) == 0)
            or (isinstance(skills_val, str) and not skills_val.strip())
        )
        if skills_empty:
            missing_fields.append("skills (must be non-empty)")
        if missing_fields:
            _err("MISSING_FIELDS", "plugin.base.json",
                 f"Missing or empty required fields: {', '.join(missing_fields)}")
        else:
            _pass()

    # Check 4: name matches folder
    if base and base.get("name") and base["name"] != plugin:
        _err("NAME_MISMATCH", "plugin.base.json",
             f"name field {base['name']!r} does not match folder name {plugin!r}")
    elif base and base.get("name"):
        _pass()

    # Check 5: hooks.json exists
    hooks_path = commons_dir / "hooks.json"
    hooks: dict = {}
    if not hooks_path.exists():
        _err("MISSING_FILE", "hooks.json", "hooks.json not found in commons/")
    else:
        _pass()
        # Check 6: hooks.json valid JSON with "hooks" key
        try:
            hooks = json.loads(hooks_path.read_text())
            if "hooks" not in hooks:
                _err("INVALID_HOOKS", "hooks.json",
                     'hooks.json is missing required "hooks" key')
            else:
                _pass()
        except json.JSONDecodeError as exc:
            _err("INVALID_JSON", "hooks.json", f"Invalid JSON: {exc}")

    # Check 7: commands/ has at least one .md file
    commands_dir = commons_dir / "commands"
    if not commands_dir.exists() or not list(commands_dir.glob("*.md")):
        _err("MISSING_COMMANDS", "commands/",
             "commands/ must contain at least one .md file")
    else:
        _pass()

    # Resolve skill paths from plugin.base.json (handles both array and string formats)
    skill_paths: list[str] = []  # relative to commons/
    skills_val = base.get("skills") if base else None
    if isinstance(skills_val, list):
        for item in skills_val:
            if isinstance(item, dict) and item.get("path"):
                skill_paths.append(item["path"])
            elif isinstance(item, str):
                skill_paths.append(item)
    elif isinstance(skills_val, str) and skills_val.strip():
        # Legacy string format: enumerate subdirectories
        skills_dir = commons_dir / skills_val.rstrip("/")
        if skills_dir.exists():
            skill_paths = [
                f"{skills_val.rstrip('/')}/{d.name}"
                for d in sorted(skills_dir.iterdir())
                if d.is_dir()
            ]

    # Check 8: each declared skill has a SKILL.md
    missing_skills = []
    present_skills = []
    for sp in skill_paths:
        skill_md = commons_dir / sp / "SKILL.md"
        if not skill_md.exists():
            missing_skills.append(sp)
        else:
            present_skills.append(skill_md)
    if missing_skills:
        for sp in missing_skills:
            _err("MISSING_FILE", f"{sp}/SKILL.md",
                 f"SKILL.md not found (declared in plugin.base.json)")
    elif skill_paths:
        _pass()

    # Resolve agent paths
    agent_paths: list[str] = []
    agents_val = base.get("agents") if base else None
    if isinstance(agents_val, list):
        for item in agents_val:
            if isinstance(item, dict) and item.get("path"):
                agent_paths.append(item["path"])
            elif isinstance(item, str):
                agent_paths.append(item)
    elif isinstance(agents_val, str) and agents_val.strip():
        # Legacy string format: just check the directory exists
        agent_paths = [agents_val.rstrip("/")]

    # Check 9: each declared agent path exists
    if agent_paths:
        missing_agents = []
        for ap in agent_paths:
            target = commons_dir / ap
            if not target.exists():
                missing_agents.append(ap)
        if missing_agents:
            for ap in missing_agents:
                _err("MISSING_FILE", ap, "agent path not found (declared in plugin.base.json)")
        else:
            _pass()

    # Check 10 & 11: each SKILL.md has frontmatter with name + description; description ≤60 words
    for skill_md in present_skills:
        rel = skill_md.relative_to(commons_dir)
        content = skill_md.read_text()
        fm = _parse_frontmatter(content)
        if not fm:
            _err("MISSING_FRONTMATTER", str(rel),
                 "SKILL.md has no YAML frontmatter (expected --- delimiters)")
            continue
        has_fm_error = False
        for field in ("name", "description"):
            if field not in fm:
                _err("MISSING_FM_FIELD", str(rel),
                     f"SKILL.md frontmatter missing required field: {field!r}")
                has_fm_error = True
        if not has_fm_error:
            _pass()
            # Check 11: description word count
            desc = str(fm.get("description", ""))
            wc = _word_count(desc)
            if wc > 60:
                _warn("DESCRIPTION_TOO_LONG", str(rel),
                      f"description is {wc} words (limit: 60)")

    # Check 12: command files have frontmatter with name + description
    if commands_dir.exists():
        for cmd_file in sorted(commands_dir.glob("*.md")):
            rel = cmd_file.relative_to(commons_dir)
            content = cmd_file.read_text()
            fm = _parse_frontmatter(content)
            if not fm:
                _err("MISSING_FRONTMATTER", str(rel),
                     "command file has no YAML frontmatter")
                continue
            for field in ("name", "description"):
                if field not in fm:
                    _err("MISSING_FM_FIELD", str(rel),
                         f"command frontmatter missing required field: {field!r}")
                else:
                    _pass()

    return {"plugin": plugin, "errors": errors, "warnings": warnings, "passed": passed}


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _print_human(result: dict) -> None:
    plugin = result["plugin"]
    errors = result["errors"]
    warnings = result["warnings"]
    passed = result["passed"]

    print(f"Validating: {plugin}/commons/\n")

    # Print all passing checks implicitly via the passed count; show issues explicitly
    for item in errors:
        print(f"❌ {item['path']} — {item['message']}")
    for item in warnings:
        print(f"⚠️  {item['path']} — {item['message']}")

    # Show a brief passing summary if nothing went wrong
    if not errors and not warnings:
        print(f"✅ All {passed} checks passed")
    elif passed > 0:
        print(f"✅ {passed} check(s) passed")

    ne = len(errors)
    nw = len(warnings)
    errs_str = f"{ne} error{'s' if ne != 1 else ''}"
    warn_str = f"{nw} warning{'s' if nw != 1 else ''}"
    print(f"\nResult: {errs_str}, {warn_str}, {passed} passed")
    if ne:
        print("Exit code: 1 (errors found)")
    else:
        print("Exit code: 0 (clean)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the commons/ directory structure of a veiled-market plugin."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plugin", help="Plugin name to validate")
    group.add_argument("--all", action="store_true", help="Validate all plugins")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Output results as JSON")
    args = parser.parse_args()

    plugins_dir = MARKETPLACE_ROOT / "plugins"
    if not plugins_dir.exists():
        print(f"[error] plugins/ directory not found at {MARKETPLACE_ROOT}", file=sys.stderr)
        sys.exit(1)

    if args.all:
        plugin_names = sorted(d.name for d in plugins_dir.iterdir() if d.is_dir())
    else:
        plugin_names = [args.plugin]

    results = [validate_plugin(p) for p in plugin_names]
    total_errors = sum(len(r["errors"]) for r in results)

    if args.json_out:
        if len(results) == 1:
            print(json.dumps(results[0], indent=2))
        else:
            print(json.dumps(results, indent=2))
    else:
        for i, result in enumerate(results):
            if i > 0:
                print()
            _print_human(result)

    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
