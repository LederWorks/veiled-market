#!/usr/bin/env python3
"""
finalize.py — Finalization step for the finalize-plugin workflow.
Promotes a draft plugin from drafts/{plugin}/ to plugins/{plugin}/,
bumps the plugin version, generates a CHANGELOG entry, and updates
both marketplace.json files.

Usage:
  python3 scripts/finalize.py --plugin terraformer [--step version|promote|marketplace|all]

Environment variables:
  plugin             The plugin name (e.g. terraformer)
  GITHUB_REPOSITORY  Owner/repo (e.g. LederWorks/veiled-market)
  BUMP_TYPE          Version bump type: major | minor | patch (default: auto)
                     auto = MINOR when new skills/agents detected, else PATCH
"""

import argparse
import datetime
import json
import os
import pathlib
import shutil
import sys


GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "LederWorks/veiled-market")

PLUGINS_REGISTRY = "sources/plugins.json"
MARKETPLACE_PATHS = [
    ".github/plugin/marketplace.json",   # GitHub Copilot CLI
    ".claude-plugin/marketplace.json",   # Claude Code
]
# $schema references relative to each output marketplace file
_MARKETPLACE_SCHEMA = {
    ".github/plugin/marketplace.json":  "../../schemas/marketplace.schema.json",
    ".claude-plugin/marketplace.json":  "../schemas/marketplace.schema.json",
}


# ---------------------------------------------------------------------------
# Version bump helpers
# ---------------------------------------------------------------------------

def _parse_semver(version: str) -> tuple[int, int, int]:
    parts = version.lstrip("v").split(".")
    if len(parts) != 3:
        raise ValueError(f"Not a valid semver string: {version!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def bump_version(version: str, bump_type: str) -> str:
    """Return the next semver string for the given bump type."""
    major, minor, patch = _parse_semver(version)
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def _collect_component_names(base_dir: str, subdir: str) -> set[str]:
    """Return the set of immediate child directory names under base_dir/subdir."""
    target = os.path.join(base_dir, subdir)
    if not os.path.isdir(target):
        return set()
    return {
        entry.name
        for entry in os.scandir(target)
        if entry.is_dir()
    }


def _detect_changelog_diff(plugin: str) -> dict:
    """Compare drafts/{plugin}/ against the current plugins/{plugin}/ and
    return a dict with keys 'added', 'changed', 'removed' — each a list
    of human-readable strings."""
    draft_dir   = f"drafts/{plugin}"
    current_dir = f"plugins/{plugin}"

    added:   list[str] = []
    changed: list[str] = []
    removed: list[str] = []

    if not os.path.isdir(current_dir):
        # First-time release — everything in the draft is "added"
        for subdir in ("skills", "agents"):
            for name in sorted(_collect_component_names(draft_dir, subdir)):
                added.append(f"`{name}` {subdir[:-1]}")
        if not added:
            added.append("Initial release")
        return {"added": added, "changed": changed, "removed": removed}

    for subdir in ("skills", "agents"):
        draft_items   = _collect_component_names(draft_dir, subdir)
        current_items = _collect_component_names(current_dir, subdir)

        for name in sorted(draft_items - current_items):
            added.append(f"`{name}` {subdir[:-1]}")

        for name in sorted(current_items - draft_items):
            removed.append(f"`{name}` {subdir[:-1]}")

        for name in sorted(draft_items & current_items):
            # Compare every file under the skill/agent directory
            draft_sub   = pathlib.Path(draft_dir,   subdir, name)
            current_sub = pathlib.Path(current_dir, subdir, name)
            draft_files = {p.relative_to(draft_sub)   for p in draft_sub.rglob("*")   if p.is_file()}
            cur_files   = {p.relative_to(current_sub) for p in current_sub.rglob("*") if p.is_file()}
            for rel in sorted(draft_files & cur_files):
                if (draft_sub / rel).read_bytes() != (current_sub / rel).read_bytes():
                    changed.append(f"`{name}` {subdir[:-1]}")
                    break

    return {"added": added, "changed": changed, "removed": removed}


def _auto_bump_type(diff: dict) -> str:
    """Determine bump type: MINOR if there are added components, else PATCH."""
    if diff.get("added"):
        return "minor"
    return "patch"


def _format_changelog_entry(version: str, diff: dict) -> str:
    today = datetime.date.today().isoformat()
    lines = [f"## [{version}] - {today}", ""]

    for section, items in (("Added", diff["added"]), ("Changed", diff["changed"]), ("Removed", diff["removed"])):
        if items:
            lines.append(f"### {section}")
            lines.extend(f"- {item}" for item in items)
            lines.append("")

    return "\n".join(lines)


def version_and_changelog(plugin: str) -> str:
    """Bump version in drafts/{plugin}/plugin.json and prepend a
    CHANGELOG.md entry.  Returns the new version string."""
    draft_dir = f"drafts/{plugin}"
    if not os.path.isdir(draft_dir):
        print(f"[error] Draft directory not found: {draft_dir}", file=sys.stderr)
        sys.exit(1)

    draft_manifest_path = os.path.join(draft_dir, "plugin.json")
    if not os.path.exists(draft_manifest_path):
        print(f"[error] Draft manifest not found: {draft_manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(draft_manifest_path) as f:
        manifest = json.load(f)

    current_version = manifest.get("version", "0.1.0")
    bump_type = os.environ.get("BUMP_TYPE", "auto").lower()

    # Determine effective bump type
    diff = _detect_changelog_diff(plugin)
    if bump_type == "auto":
        bump_type = _auto_bump_type(diff)

    # First-time release: keep initial 0.1.0; don't bump to 0.2.0
    current_dir = f"plugins/{plugin}"
    if not os.path.isdir(current_dir) and current_version == "0.1.0" and bump_type != "major":
        new_version = "0.1.0"
    else:
        new_version = bump_version(current_version, bump_type)

    print(f"Version: {current_version} → {new_version}  (bump={bump_type})")

    # Write bumped version to draft manifest
    manifest["version"] = new_version
    with open(draft_manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"Updated {draft_manifest_path}")

    # Write/prepend CHANGELOG.md in the draft directory
    changelog_path = os.path.join(draft_dir, "CHANGELOG.md")
    entry = _format_changelog_entry(new_version, diff)

    if os.path.exists(changelog_path):
        existing = open(changelog_path).read()
        # Prepend after the title line if present, otherwise at the top
        if existing.startswith("# Changelog"):
            header, _, rest = existing.partition("\n\n")
            new_content = f"{header}\n\n{entry}\n{rest}"
        else:
            new_content = f"{entry}\n{existing}"
    else:
        new_content = f"# Changelog\n\nAll notable changes to the `{plugin}` plugin are documented here.\n\n{entry}\n"

    with open(changelog_path, "w") as f:
        f.write(new_content)
    print(f"Updated {changelog_path}")

    return new_version


def promote_draft(plugin: str) -> None:
    """Move drafts/{plugin}/ to plugins/{plugin}/."""
    src = f"drafts/{plugin}"
    dst = f"plugins/{plugin}"

    if not os.path.isdir(src):
        print(f"[error] Draft directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"Promoted {src} → {dst}")

    # Ensure plugin.json has required fields
    manifest_path = os.path.join(dst, "plugin.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        manifest.setdefault("name", plugin)
        manifest.setdefault("version", "0.1.0")
        manifest.setdefault("license", "MIT")
        manifest["repository"] = f"https://github.com/{GITHUB_REPOSITORY}"
        # Remove internal/workflow fields not suitable for plugin.json
        manifest.pop("enrichment_notes", None)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        print(f"Updated {manifest_path}")


def update_marketplace(plugin: str) -> None:
    """Update sources/plugins.json with the finalized plugin entry then
    regenerate both marketplace.json output files from the central registry."""
    repo_url = f"https://github.com/{GITHUB_REPOSITORY}"
    plugin_dir = f"plugins/{plugin}"

    # Read the authoritative plugin manifest from the promoted directory.
    manifest_path = os.path.join(plugin_dir, "plugin.json")
    if not os.path.exists(manifest_path):
        print(f"[error] Plugin manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)
    with open(manifest_path) as f:
        manifest = json.load(f)

    entry = {
        "name": manifest.get("name", plugin),
        "description": manifest.get("description", f"{plugin} plugin"),
        "version": manifest.get("version", "0.1.0"),
        "source": plugin_dir,
        "author": manifest.get("author", {"name": "veiled-market contributors", "url": repo_url}),
        "homepage": manifest.get("homepage", f"{repo_url}/tree/main/{plugin_dir}"),
        "repository": repo_url,
        "license": manifest.get("license", "MIT"),
        "keywords": manifest.get("keywords", []),
        "category": manifest.get("category", ""),
        "tags": manifest.get("tags", []),
    }

    # Upsert into the central plugins registry (sources/plugins.json).
    if not os.path.exists(PLUGINS_REGISTRY):
        print(f"[error] Plugins registry not found: {PLUGINS_REGISTRY}", file=sys.stderr)
        sys.exit(1)
    with open(PLUGINS_REGISTRY) as f:
        registry = json.load(f)
    plugins_list = registry.setdefault("plugins", [])
    replaced = False
    for i, p in enumerate(plugins_list):
        if p.get("name") == plugin:
            plugins_list[i] = entry
            replaced = True
            break
    if not replaced:
        plugins_list.append(entry)
    with open(PLUGINS_REGISTRY, "w") as f:
        json.dump(registry, f, indent=2)
        f.write("\n")
    print(f"Updated {PLUGINS_REGISTRY}")

    # Regenerate both marketplace output files from the updated central registry.
    _write_marketplace_files(registry)


def _write_marketplace_files(registry: dict) -> None:
    """Regenerate both marketplace.json files from sources/plugins.json.

    The output schema is identical for both files; only the $schema relative
    path differs because the files sit at different depths in the tree.
    """
    mp_info = registry.get("marketplace", {})
    plugins_list = registry.get("plugins", [])

    for mp_path in MARKETPLACE_PATHS:
        output: dict = {}
        if mp_path in _MARKETPLACE_SCHEMA:
            output["$schema"] = _MARKETPLACE_SCHEMA[mp_path]
        output["name"] = mp_info.get("name", "veiled-market")
        output["owner"] = mp_info.get("owner", {})
        if "metadata" in mp_info:
            output["metadata"] = mp_info["metadata"]
        output["plugins"] = plugins_list

        os.makedirs(os.path.dirname(mp_path), exist_ok=True)
        with open(mp_path, "w") as f:
            json.dump(output, f, indent=2)
            f.write("\n")
        print(f"Updated {mp_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize a plugin from drafts/ to plugins/")
    parser.add_argument("--plugin", default=os.environ.get("plugin", ""),
                        help="plugin name (e.g. terraformer)")
    parser.add_argument("--step", choices=["version", "promote", "marketplace", "all"],
                        default="all",
                        help="Which step to run (default: all)")
    args = parser.parse_args()

    if not args.plugin:
        print("[error] --plugin or plugin env var is required.", file=sys.stderr)
        sys.exit(1)

    if args.step in ("version", "all"):
        version_and_changelog(args.plugin)

    if args.step in ("promote", "all"):
        promote_draft(args.plugin)

    if args.step in ("marketplace", "all"):
        update_marketplace(args.plugin)


if __name__ == "__main__":
    main()
