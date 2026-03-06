#!/usr/bin/env python3
"""
compose.py — Generate a filtered plugin.json for a plugin based on selected
language and platform tags.

This implements "dynamic plugin filling": only skills, agents, and hooks whose
frontmatter `languages:` / `platforms:` arrays overlap with the user's selections
are included. Components with **no** `languages` / `platforms` frontmatter are
treated as universal and always included.

Usage::

    # Include all components (no filtering)
    python3 scripts/compose.py --plugin plugins/terraformer --output /tmp/my-plugin

    # Only include skills that support AWS and use Bash or HCL
    python3 scripts/compose.py \\
        --plugin plugins/terraformer \\
        --platforms aws,azure \\
        --langs bash,hcl \\
        --output /tmp/my-plugin

    # Dry-run: list what would be included without writing
    python3 scripts/compose.py --plugin plugins/terraformer --platforms azure --dry-run

Output::

    /tmp/my-plugin/plugin.json  — filtered manifest pointing only to matching components
    /tmp/my-plugin/skills/      — symlinks or copies of matching skills
    /tmp/my-plugin/agents/      — symlinks or copies of matching agents
    (hooks.json and .mcp.json are always included unchanged)

Frontmatter convention in SKILL.md / .agent.md::

    ---
    name: terraform-plan
    description: ...
    platforms: [aws, azure, gcp, terraform-cloud]
    languages: [hcl, bash]
    ---

    Skill instructions...

The `platforms` field accepts values matching any of the `platform/csp/`,
`platform/ci/`, or `platform/saas/` label names (without the prefix).
The `languages` field accepts values matching `lang/` label names (without prefix).
"""

import argparse
import json
import os
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, os.path.dirname(__file__))
from registry import parse_tags  # noqa: E402


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def _parse_frontmatter(content: str) -> Dict[str, Any]:
    """Parse YAML-like frontmatter between --- delimiters.

    Only handles the scalar types used in SKILL.md/agent.md:
    - string scalars
    - bracket-style lists: [a, b, c]
    - dash-style lists:
        - a
        - b
    """
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    fm_block = content[3:end].strip()
    result: Dict[str, Any] = {}
    i = 0
    lines = fm_block.splitlines()
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\w[\w\-]*)\s*:\s*(.*)', line)
        if not m:
            i += 1
            continue
        key, raw_val = m.group(1), m.group(2).strip()
        # Bracket list: [a, b, c]
        if raw_val.startswith("["):
            inner = raw_val.strip("[]")
            result[key] = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
            i += 1
        elif raw_val == "" or raw_val == "|":
            # Possible dash-list on following lines
            items = []
            i += 1
            while i < len(lines) and re.match(r'^\s+-\s', lines[i]):
                items.append(re.sub(r'^[\s\-]+', '', lines[i]).strip().strip("\"'"))
                i += 1
            result[key] = items if items else raw_val
        else:
            result[key] = raw_val
            i += 1
    return result


def _body_after_frontmatter(content: str) -> str:
    """Return the content after the closing --- of the frontmatter block."""
    if not content.startswith("---"):
        return content
    end = content.find("\n---", 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip("\n")


# ---------------------------------------------------------------------------
# Component loading
# ---------------------------------------------------------------------------

def _tags_match(component_tags: List[str], selected: Set[str]) -> bool:
    """Return True if the component matches the selected filter.

    Rules:
    - If ``selected`` is empty (no filter), everything matches.
    - If the component has no tags (empty list), it is universal → always included.
    - Otherwise, the component matches if *any* of its tags is in ``selected``.
    """
    if not selected:
        return True
    if not component_tags:
        return True  # universal component
    return bool(set(component_tags) & selected)


def load_skills(plugin_dir: str, lang_filter: Set[str], platform_filter: Set[str]) -> List[Dict]:
    """Return metadata for all matching skills in {plugin_dir}/skills/."""
    skills_dir = os.path.join(plugin_dir, "skills")
    if not os.path.isdir(skills_dir):
        return []
    results = []
    for skill_name in sorted(os.listdir(skills_dir)):
        skill_path = os.path.join(skills_dir, skill_name)
        skill_md = os.path.join(skill_path, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md) as f:
            content = f.read()
        fm = _parse_frontmatter(content)
        langs: List[str] = fm.get("languages", []) or []
        platforms: List[str] = fm.get("platforms", []) or []

        lang_ok = _tags_match(langs, lang_filter)
        plat_ok = _tags_match(platforms, platform_filter)

        results.append({
            "name": fm.get("name", skill_name),
            "description": fm.get("description", ""),
            "languages": langs,
            "platforms": platforms,
            "path": os.path.relpath(skill_path, plugin_dir),
            "skill_md": skill_md,
            "included": lang_ok and plat_ok,
            "reason": _reason(langs, platforms, lang_filter, platform_filter),
        })
    return results


def load_agents(plugin_dir: str, lang_filter: Set[str], platform_filter: Set[str]) -> List[Dict]:
    """Return metadata for all matching agents in {plugin_dir}/agents/."""
    agents_dir = os.path.join(plugin_dir, "agents")
    if not os.path.isdir(agents_dir):
        return []
    results = []
    for fname in sorted(os.listdir(agents_dir)):
        if not fname.endswith(".agent.md"):
            continue
        agent_path = os.path.join(agents_dir, fname)
        with open(agent_path) as f:
            content = f.read()
        fm = _parse_frontmatter(content)
        langs: List[str] = fm.get("languages", []) or []
        platforms: List[str] = fm.get("platforms", []) or []

        lang_ok = _tags_match(langs, lang_filter)
        plat_ok = _tags_match(platforms, platform_filter)

        results.append({
            "name": fm.get("name", fname.replace(".agent.md", "")),
            "description": fm.get("description", ""),
            "languages": langs,
            "platforms": platforms,
            "path": os.path.relpath(agent_path, plugin_dir),
            "file": agent_path,
            "included": lang_ok and plat_ok,
            "reason": _reason(langs, platforms, lang_filter, platform_filter),
        })
    return results


def _reason(
    langs: List[str],
    platforms: List[str],
    lang_filter: Set[str],
    platform_filter: Set[str],
) -> str:
    if not lang_filter and not platform_filter:
        return "included (no filter active)"
    if not langs and not platforms:
        return "included (universal component)"
    parts = []
    if lang_filter:
        matched = set(langs) & lang_filter
        parts.append(f"lang match: {sorted(matched) or 'none'}")
    if platform_filter:
        matched = set(platforms) & platform_filter
        parts.append(f"platform match: {sorted(matched) or 'none'}")
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _write_output(
    plugin_dir: str,
    output_dir: str,
    skills: List[Dict],
    agents: List[Dict],
    base_manifest: Dict,
    lang_filter: Set[str],
    platform_filter: Set[str],
) -> None:
    """Copy matching components to output_dir and write a filtered plugin.json."""
    os.makedirs(output_dir, exist_ok=True)

    # Copy matching skills
    out_skills_dir = os.path.join(output_dir, "skills")
    for skill in skills:
        if not skill["included"]:
            continue
        src = os.path.join(plugin_dir, skill["path"])
        dst = os.path.join(out_skills_dir, os.path.basename(skill["path"]))
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    # Copy matching agents
    out_agents_dir = os.path.join(output_dir, "agents")
    for agent in agents:
        if not agent["included"]:
            continue
        src = agent["file"]
        os.makedirs(out_agents_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(out_agents_dir, os.path.basename(src)))

    # Copy hooks.json (always)
    hooks = os.path.join(plugin_dir, "hooks.json")
    if os.path.exists(hooks):
        shutil.copy2(hooks, os.path.join(output_dir, "hooks.json"))

    # Copy .mcp.json (always)
    mcp = os.path.join(plugin_dir, ".mcp.json")
    if os.path.exists(mcp):
        shutil.copy2(mcp, os.path.join(output_dir, ".mcp.json"))

    # Build filtered manifest
    manifest = dict(base_manifest)
    manifest["_composed"] = True
    manifest["_lang_filter"] = sorted(lang_filter)
    manifest["_platform_filter"] = sorted(platform_filter)
    manifest["_included_skills"] = [s["name"] for s in skills if s["included"]]
    manifest["_included_agents"] = [a["name"] for a in agents if a["included"]]

    if os.path.isdir(out_skills_dir):
        manifest["skills"] = "skills/"
    else:
        manifest.pop("skills", None)

    if os.path.isdir(out_agents_dir):
        manifest["agents"] = "agents/"
    else:
        manifest.pop("agents", None)

    manifest_path = os.path.join(output_dir, "plugin.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"Wrote {manifest_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def compose(
    plugin_dir: str,
    output_dir: Optional[str],
    lang_filter: Set[str],
    platform_filter: Set[str],
    dry_run: bool,
) -> int:
    if not os.path.isdir(plugin_dir):
        print(f"[error] Plugin directory not found: {plugin_dir}", file=sys.stderr)
        return 1

    manifest_path = os.path.join(plugin_dir, "plugin.json")
    if not os.path.exists(manifest_path):
        print(f"[error] plugin.json not found in {plugin_dir}", file=sys.stderr)
        return 1

    with open(manifest_path) as f:
        base_manifest: Dict[str, Any] = json.load(f)

    plugin_name = base_manifest.get("name", os.path.basename(plugin_dir))

    print(f"[compose] Plugin: {plugin_name}")
    if lang_filter:
        print(f"          Lang filter:     {sorted(lang_filter)}")
    if platform_filter:
        print(f"          Platform filter: {sorted(platform_filter)}")
    print()

    skills = load_skills(plugin_dir, lang_filter, platform_filter)
    agents = load_agents(plugin_dir, lang_filter, platform_filter)

    # Print selection summary
    included_skills = [s for s in skills if s["included"]]
    excluded_skills = [s for s in skills if not s["included"]]
    included_agents = [a for a in agents if a["included"]]
    excluded_agents = [a for a in agents if not a["included"]]

    print(f"Skills  ({len(included_skills)}/{len(skills)} included):")
    for s in skills:
        mark = "✅" if s["included"] else "⛔"
        print(f"  {mark} {s['name']:30s}  {s['reason']}")
    print()
    print(f"Agents  ({len(included_agents)}/{len(agents)} included):")
    for a in agents:
        mark = "✅" if a["included"] else "⛔"
        print(f"  {mark} {a['name']:30s}  {a['reason']}")
    print()

    if dry_run:
        print("[dry-run] No files written.")
        return 0

    if not output_dir:
        print("[error] --output is required unless --dry-run is set.", file=sys.stderr)
        return 1

    _write_output(plugin_dir, output_dir, skills, agents, base_manifest, lang_filter, platform_filter)
    print(f"[compose] Done. Composed plugin written to: {output_dir}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compose a filtered plugin from a plugin directory. "
            "Only components whose platforms/languages match the selected filters are included."
        )
    )
    parser.add_argument(
        "--plugin",
        required=True,
        help="Path to the plugin directory (e.g. plugins/terraformer)",
    )
    parser.add_argument(
        "--langs",
        default="",
        help="Comma-separated language tags to include (e.g. bash,hcl). Empty = all.",
    )
    parser.add_argument(
        "--platforms",
        default="",
        help="Comma-separated platform tags to include (e.g. aws,azure,github-actions). Empty = all.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for the composed plugin (required unless --dry-run).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be included without writing files.",
    )
    args = parser.parse_args()
    # Use shared parse_tags from registry for consistent normalisation
    lang_filter = parse_tags(args.langs)
    platform_filter = parse_tags(args.platforms)
    sys.exit(compose(args.plugin, args.output, lang_filter, platform_filter, args.dry_run))


if __name__ == "__main__":
    main()
