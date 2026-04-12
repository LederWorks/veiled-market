"""
build-platforms.py

Reads a plugin's commons/ directory and generates platform-specific output
directories for Claude Code (claude/) and Copilot CLI (copilot/).

Usage (from veiled-market/):
    python3 scripts/build-platforms.py --plugin <name> [--dry-run] [--commons-dir <path>]
"""

import argparse
import json
import pathlib
import re
import shutil
import sys


# ---------------------------------------------------------------------------
# Frontmatter helpers
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

    fm = {}
    i = 1
    while i < end:
        line = lines[i]
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val in (">-", ">", "|", "|-"):
                # Collect subsequent indented lines
                body_lines = []
                j = i + 1
                while j < end and (lines[j].startswith("  ") or lines[j].startswith("\t")):
                    body_lines.append(lines[j].strip())
                    j += 1
                if val in (">-", ">"):
                    fm[key] = " ".join(body_lines)
                else:
                    fm[key] = "\n".join(body_lines)
                i = j
                continue
            elif val.lower() == "true":
                fm[key] = True
            elif val.lower() == "false":
                fm[key] = False
            elif val.startswith("[") and val.endswith("]"):
                items = [x.strip() for x in val[1:-1].split(",") if x.strip()]
                fm[key] = items
            else:
                fm[key] = val
        i += 1
    return fm


def _body_after_frontmatter(content: str) -> str:
    """Return the content after the closing --- of the frontmatter block."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return content
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end == -1:
        return content
    return "\n".join(lines[end + 1:])


def _render_frontmatter(fm: dict) -> str:
    """Render a dict back to YAML frontmatter string."""
    lines = ["---"]
    for key, val in fm.items():
        if isinstance(val, list):
            items_str = ", ".join(str(v) for v in val)
            lines.append(f"{key}: [{items_str}]")
        elif isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Manifest writer
# ---------------------------------------------------------------------------

def _write_platform_manifest(base: dict, out_dir: pathlib.Path, platform: str, dry_run: bool = False):
    """Write plugin.json to out_dir, omitting $-prefixed keys from base."""
    manifest = {k: v for k, v in base.items() if not k.startswith("$")}
    if not dry_run:
        (out_dir / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"  [{platform}] plugin.json written")


# ---------------------------------------------------------------------------
# Platform builders
# ---------------------------------------------------------------------------

def _build_claude(commons_dir: pathlib.Path, out: pathlib.Path, base: dict, dry_run: bool):
    """Generate the claude/ output directory from commons/."""

    # 1. Skills
    skills_src = commons_dir / "skills"
    if skills_src.exists():
        for skill_dir in sorted(p for p in skills_src.iterdir() if p.is_dir()):
            dest = out / "skills" / skill_dir.name
            if not dry_run:
                shutil.copytree(skill_dir, dest, dirs_exist_ok=True)
            print(f"  [claude] skills/{skill_dir.name}: copied verbatim")
    else:
        print("  [claude] No commons/skills/ found, skipping skills.")

    # 2. Agents
    agents_src = commons_dir / "agents"
    if agents_src.exists():
        out_agents = out / "agents"
        if not dry_run:
            out_agents.mkdir(parents=True, exist_ok=True)
        for src in sorted(p for p in agents_src.iterdir() if p.is_file() and p.suffix == ".md"):
            if not dry_run:
                shutil.copy2(src, out_agents / src.name)
            print(f"  [claude] agents/{src.name}: copied")
    else:
        print("  [claude] No commons/agents/ found, skipping agents.")

    # 3. Commands
    commands_src = commons_dir / "commands"
    if commands_src.exists():
        out_commands = out / "commands"
        if not dry_run:
            out_commands.mkdir(parents=True, exist_ok=True)
        for src in sorted(p for p in commands_src.iterdir() if p.is_file()):
            if not dry_run:
                shutil.copy2(src, out_commands / src.name)
            print(f"  [claude] commands/{src.name}: copied verbatim")
    else:
        print("  [claude] No commons/commands/ found, skipping commands.")

    # 4. hooks.json
    hooks_src = commons_dir / "hooks.json"
    if hooks_src.exists():
        if not dry_run:
            shutil.copy2(hooks_src, out / "hooks.json")
        print("  [claude] hooks.json: copied verbatim")
    else:
        print("  [claude] No commons/hooks.json found, skipping.")

    # 5. .mcp.json
    mcp_src = commons_dir / ".mcp.json"
    if mcp_src.exists():
        if not dry_run:
            shutil.copy2(mcp_src, out / ".mcp.json")
        print("  [claude] .mcp.json: copied")
    else:
        print("  [claude] No commons/.mcp.json found, skipping.")

    # 6. references/
    refs_src = commons_dir / "references"
    if refs_src.exists():
        if not dry_run:
            shutil.copytree(refs_src, out / "references", dirs_exist_ok=True)
        print("  [claude] references/: copied recursively")
    else:
        print("  [claude] No commons/references/ found, skipping.")

    # 7. Manifest
    _write_platform_manifest(base, out, "claude", dry_run)


def _build_copilot(commons_dir: pathlib.Path, out: pathlib.Path, base: dict, dry_run: bool):
    """Generate the copilot/ output directory from commons/."""

    # 1. Skills
    skills_src = commons_dir / "skills"
    if skills_src.exists():
        for skill_dir in sorted(p for p in skills_src.iterdir() if p.is_dir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                print(f"  [copilot] WARNING: {skill_dir.name}/SKILL.md missing, skipping.")
                continue

            content = skill_md.read_text()
            fm = _parse_frontmatter(content)
            body = _body_after_frontmatter(content)

            out_skill = out / "skills" / skill_dir.name
            if not dry_run:
                out_skill.mkdir(parents=True, exist_ok=True)

            # Copy non-SKILL.md files
            for f in skill_dir.iterdir():
                if f.name != "SKILL.md" and f.is_file():
                    if not dry_run:
                        shutil.copy2(f, out_skill / f.name)
                elif f.is_dir():
                    if not dry_run:
                        shutil.copytree(f, out_skill / f.name, dirs_exist_ok=True)

            # Decide output filename based on user-invocable flag
            is_hidden = str(fm.get("user-invocable", "true")).lower() == "false"
            if is_hidden:
                fm_copy = {k: v for k, v in fm.items() if k != "user-invocable"}
                if not dry_run:
                    (out_skill / "workflow.md").write_text(_render_frontmatter(fm_copy) + body)
                print(f"  [copilot] {skill_dir.name}: SKILL.md → workflow.md (hidden skill)")
            else:
                if not dry_run:
                    shutil.copy2(skill_md, out_skill / "SKILL.md")
                print(f"  [copilot] {skill_dir.name}: SKILL.md → SKILL.md")
    else:
        print("  [copilot] No commons/skills/ found, skipping skills.")

    # 2. Agents (rename *.md → *.agent.md)
    agents_src = commons_dir / "agents"
    if agents_src.exists():
        out_agents = out / "agents"
        if not dry_run:
            out_agents.mkdir(parents=True, exist_ok=True)
        for src in sorted(p for p in agents_src.iterdir() if p.is_file() and p.suffix == ".md"):
            dest_name = src.stem + ".agent.md"
            if not dry_run:
                shutil.copy2(src, out_agents / dest_name)
            print(f"  [copilot] agents/{src.name} → agents/{dest_name}")
    else:
        print("  [copilot] No commons/agents/ found, skipping agents.")

    # 3. Commands (path transform: ${CLAUDE_PLUGIN_ROOT}/skills/<x>/SKILL.md → skills/<x>/workflow.md)
    commands_src = commons_dir / "commands"
    if commands_src.exists():
        out_commands = out / "commands"
        if not dry_run:
            out_commands.mkdir(parents=True, exist_ok=True)
        for src in sorted(p for p in commands_src.iterdir() if p.is_file()):
            content = src.read_text()
            content = re.sub(
                r'\$\{CLAUDE_PLUGIN_ROOT\}/skills/([^/]+)/SKILL\.md',
                r'skills/\1/workflow.md',
                content,
            )
            if not dry_run:
                (out_commands / src.name).write_text(content)
            print(f"  [copilot] commands/{src.name}: path transform applied")
    else:
        print("  [copilot] No commons/commands/ found, skipping commands.")

    # 4. hooks.json (normalize: ensure version:1)
    hooks_src = commons_dir / "hooks.json"
    if hooks_src.exists():
        hooks = json.loads(hooks_src.read_text())
        if "version" not in hooks:
            hooks = {"version": 1, **hooks}
        if not dry_run:
            (out / "hooks.json").write_text(json.dumps(hooks, indent=2) + "\n")
        print("  [copilot] hooks.json: normalized with version:1")
    else:
        print("  [copilot] No commons/hooks.json found, skipping.")

    # 5. .mcp.json
    mcp_src = commons_dir / ".mcp.json"
    if mcp_src.exists():
        if not dry_run:
            shutil.copy2(mcp_src, out / ".mcp.json")
        print("  [copilot] .mcp.json: copied")
    else:
        print("  [copilot] No commons/.mcp.json found, skipping.")

    # 6. references/
    refs_src = commons_dir / "references"
    if refs_src.exists():
        if not dry_run:
            shutil.copytree(refs_src, out / "references", dirs_exist_ok=True)
        print("  [copilot] references/: copied recursively")
    else:
        print("  [copilot] No commons/references/ found, skipping.")

    # 7. Manifest
    _write_platform_manifest(base, out, "copilot", dry_run)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_plugin(plugin: str, commons_dir: pathlib.Path = None, dry_run: bool = False):
    """Build claude/ and copilot/ output directories for the given plugin."""
    plugins_root = pathlib.Path("plugins")

    if commons_dir is None:
        commons_dir = plugins_root / plugin / "commons"

    # Step 1 & 2: Validate commons/ exists
    if not commons_dir.exists():
        print(f"[build] No commons/ for {plugin}, skipping.")
        return

    # Step 3: Validate plugin.base.json
    base_json = commons_dir / "plugin.base.json"
    if not base_json.exists():
        print(f"[build] ERROR: {base_json} is missing.", file=sys.stderr)
        sys.exit(1)

    # Step 4: Load base manifest
    base = json.loads(base_json.read_text())

    print(f"[build] Building plugin: {plugin}")

    for platform in ["claude", "copilot"]:
        out_dir = plugins_root / plugin / platform
        print(f"[build] Platform: {platform} → {out_dir}")

        if not dry_run:
            shutil.rmtree(out_dir, ignore_errors=True)
            out_dir.mkdir(parents=True, exist_ok=True)

        if platform == "claude":
            _build_claude(commons_dir, out_dir, base, dry_run)
        else:
            _build_copilot(commons_dir, out_dir, base, dry_run)

    print(f"[build] Done: {plugin}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build platform-specific plugin dirs from commons/")
    parser.add_argument("--plugin", required=True, help="Plugin name (e.g. socrates)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    parser.add_argument("--commons-dir", help="Override commons/ directory path")
    args = parser.parse_args()

    commons_dir = pathlib.Path(args.commons_dir) if args.commons_dir else None
    build_plugin(args.plugin, commons_dir=commons_dir, dry_run=args.dry_run)
