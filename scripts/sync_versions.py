"""
sync_versions.py

Bumps or sets the semver version for a veiled-market plugin. Propagates the new
version to all generated platform manifests and regenerates marketplace files.

Usage (from veiled-market/):
    python3 scripts/sync_versions.py --plugin <name> --bump patch|minor|major
    python3 scripts/sync_versions.py --plugin <name> --set 1.2.3
    python3 scripts/sync_versions.py --plugin <name> --bump patch --dry-run
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


MARKETPLACE_ROOT = Path(__file__).resolve().parent.parent

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


# ---------------------------------------------------------------------------
# Semver helpers
# ---------------------------------------------------------------------------

def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semver string into (major, minor, patch). Raises ValueError on bad input."""
    if not _SEMVER_RE.match(version):
        raise ValueError(f"Not a valid semver string: {version!r}")
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def _bump_version(version: str, bump: str) -> str:
    """Return the next semver string for the given bump type."""
    major, minor, patch = _parse_semver(version)
    if bump == "major":
        return f"{major + 1}.0.0"
    elif bump == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


# ---------------------------------------------------------------------------
# File updaters
# ---------------------------------------------------------------------------

def _update_json_version(path: Path, new_version: str, dry_run: bool) -> str:
    """Update the top-level 'version' field in a JSON file. Returns status string."""
    if not path.exists():
        return "not found (skipped)"
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return f"ERROR: invalid JSON — {exc}"
    old = data.get("version", "<unset>")
    if old == new_version:
        return f"already at {new_version} (skipped)"
    data["version"] = new_version
    if not dry_run:
        path.write_text(json.dumps(data, indent=2) + "\n")
    return f"{old} → {new_version}"


def _update_plugins_json(plugins_json: Path, plugin: str,
                         new_version: str, dry_run: bool) -> str:
    """Update the version for one plugin entry in sources/plugins.json."""
    try:
        registry = json.loads(plugins_json.read_text())
    except json.JSONDecodeError as exc:
        return f"ERROR: invalid JSON — {exc}"

    plugins_list = registry.get("plugins", [])
    for i, entry in enumerate(plugins_list):
        if entry.get("name") == plugin:
            old = entry.get("version", "<unset>")
            if old == new_version:
                return f"already at {new_version} (skipped)"
            plugins_list[i]["version"] = new_version
            registry["plugins"] = plugins_list
            if not dry_run:
                plugins_json.write_text(json.dumps(registry, indent=2) + "\n")
            return f"{old} → {new_version}"

    return f"ERROR: plugin {plugin!r} not found in plugins.json"


def _regen_marketplace(dry_run: bool) -> str:
    """Call finalize.py --step regen to regenerate both marketplace.json files."""
    if dry_run:
        return "(skipped in dry-run)"
    finalize = MARKETPLACE_ROOT / "scripts" / "finalize.py"
    result = subprocess.run(
        [sys.executable, str(finalize), "--step", "regen"],
        cwd=str(MARKETPLACE_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return f"ERROR: finalize.py exited {result.returncode} — {result.stderr.strip()}"
    return "regenerated"


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------

def sync_versions(plugin: str, new_version: str, old_version: str, dry_run: bool) -> int:
    """Propagate new_version to all plugin files. Returns exit code."""
    plugins_root = MARKETPLACE_ROOT / "plugins"
    plugin_dir = plugins_root / plugin

    updates: list[tuple[str, str]] = []

    # 1. commons/plugin.base.json
    base_path = plugin_dir / "commons" / "plugin.base.json"
    status = _update_json_version(base_path, new_version, dry_run)
    updates.append((f"plugins/{plugin}/commons/plugin.base.json", status))

    # 2. claude/plugin.json (optional)
    claude_path = plugin_dir / "claude" / "plugin.json"
    status = _update_json_version(claude_path, new_version, dry_run)
    updates.append((f"plugins/{plugin}/claude/plugin.json", status))

    # 3. copilot/plugin.json (optional)
    copilot_path = plugin_dir / "copilot" / "plugin.json"
    status = _update_json_version(copilot_path, new_version, dry_run)
    updates.append((f"plugins/{plugin}/copilot/plugin.json", status))

    # 4. sources/plugins.json
    plugins_json = MARKETPLACE_ROOT / "sources" / "plugins.json"
    status = _update_plugins_json(plugins_json, plugin, new_version, dry_run)
    updates.append(("sources/plugins.json", status))

    # 5. marketplace manifests via finalize.py --step regen
    status = _regen_marketplace(dry_run)
    updates.append(("marketplace manifests (finalize.py --step regen)", status))

    # Print summary
    marker = "[dry-run] " if dry_run else ""
    print(f"🔖 {plugin}: {old_version} → {new_version}\n")
    print(f"{marker}Updated:")
    any_error = False
    for path, s in updates:
        if s.startswith("ERROR"):
            icon = "❌"
            any_error = True
        elif "skipped" in s or "not found" in s or "dry-run" in s:
            icon = "⏭️ "
        else:
            icon = "✅"
        print(f"  {icon} {path} — {s}")

    return 1 if any_error else 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bump or set the version of a veiled-market plugin across all manifests."
    )
    parser.add_argument("--plugin", required=True, help="Plugin name (e.g. atlas)")
    bump_group = parser.add_mutually_exclusive_group(required=True)
    bump_group.add_argument("--bump", choices=["patch", "minor", "major"],
                            help="Semver bump type")
    bump_group.add_argument("--set", dest="set_version", metavar="VERSION",
                            help="Set an exact version (e.g. 1.2.3)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing any files")
    args = parser.parse_args()

    # Resolve plugin root
    plugin_dir = MARKETPLACE_ROOT / "plugins" / args.plugin
    if not plugin_dir.exists():
        print(f"[error] Plugin directory not found: plugins/{args.plugin}", file=sys.stderr)
        sys.exit(1)

    # Read current version from commons/plugin.base.json
    base_path = plugin_dir / "commons" / "plugin.base.json"
    if not base_path.exists():
        print(f"[error] plugin.base.json not found: {base_path.relative_to(MARKETPLACE_ROOT)}",
              file=sys.stderr)
        sys.exit(1)
    try:
        base = json.loads(base_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"[error] Invalid JSON in plugin.base.json: {exc}", file=sys.stderr)
        sys.exit(1)

    current_version = base.get("version", "")
    if not _SEMVER_RE.match(current_version):
        print(f"[error] Current version {current_version!r} is not valid semver.", file=sys.stderr)
        sys.exit(1)

    # Verify plugin exists in sources/plugins.json
    plugins_json = MARKETPLACE_ROOT / "sources" / "plugins.json"
    if not plugins_json.exists():
        print(f"[error] sources/plugins.json not found.", file=sys.stderr)
        sys.exit(1)
    try:
        registry = json.loads(plugins_json.read_text())
    except json.JSONDecodeError as exc:
        print(f"[error] Invalid JSON in sources/plugins.json: {exc}", file=sys.stderr)
        sys.exit(1)
    if not any(e.get("name") == args.plugin for e in registry.get("plugins", [])):
        print(f"[error] Plugin {args.plugin!r} not found in sources/plugins.json.", file=sys.stderr)
        sys.exit(1)

    # Compute new version
    if args.set_version:
        new_version = args.set_version
        if not _SEMVER_RE.match(new_version):
            print(f"[error] --set value {new_version!r} is not valid semver (x.y.z).",
                  file=sys.stderr)
            sys.exit(1)
    else:
        try:
            new_version = _bump_version(current_version, args.bump)
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)

    rc = sync_versions(
        plugin=args.plugin,
        new_version=new_version,
        old_version=current_version,
        dry_run=args.dry_run,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
