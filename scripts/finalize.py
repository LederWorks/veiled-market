#!/usr/bin/env python3
"""
finalize.py — Finalization step for the finalize-plugin workflow.
Promotes a draft plugin from drafts/{expertise}/ to plugins/{expertise}/
and updates both marketplace.json files.

Usage:
  python3 scripts/finalize.py --expertise terraformer [--step promote|marketplace]

Environment variables:
  EXPERTISE          The expertise name (e.g. terraformer)
  GITHUB_REPOSITORY  Owner/repo (e.g. LederWorks/veiled-market)
"""

import argparse
import json
import os
import shutil
import sys


GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "LederWorks/veiled-market")


def promote_draft(expertise: str) -> None:
    """Move drafts/{expertise}/ to plugins/{expertise}/."""
    src = f"drafts/{expertise}"
    dst = f"plugins/{expertise}"

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
        manifest.setdefault("name", expertise)
        manifest.setdefault("version", "0.1.0")
        manifest.setdefault("license", "MIT")
        manifest["repository"] = f"https://github.com/{GITHUB_REPOSITORY}"
        # Remove internal/workflow fields not suitable for plugin.json
        manifest.pop("enrichment_notes", None)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        print(f"Updated {manifest_path}")


def update_marketplace(expertise: str) -> None:
    """Update both marketplace.json files with the finalized plugin entry."""
    repo_url = f"https://github.com/{GITHUB_REPOSITORY}"
    plugin_dir = f"plugins/{expertise}"

    manifest_path = os.path.join(plugin_dir, "plugin.json")
    if not os.path.exists(manifest_path):
        print(f"[error] Plugin manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    entry = {
        "name": manifest.get("name", expertise),
        "description": manifest.get("description", f"{expertise} plugin"),
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

    for mp_path in [".github/plugin/marketplace.json", ".claude-plugin/marketplace.json"]:
        if not os.path.exists(mp_path):
            print(f"[skip] Marketplace not found: {mp_path}")
            continue
        with open(mp_path) as f:
            marketplace = json.load(f)
        plugins = marketplace.setdefault("plugins", [])
        replaced = False
        for i, p in enumerate(plugins):
            if p.get("name") == expertise:
                plugins[i] = entry
                replaced = True
                break
        if not replaced:
            plugins.append(entry)
        with open(mp_path, "w") as f:
            json.dump(marketplace, f, indent=2)
            f.write("\n")
        print(f"Updated {mp_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize a plugin from drafts/ to plugins/")
    parser.add_argument("--expertise", default=os.environ.get("EXPERTISE", ""),
                        help="Expertise name (e.g. terraformer)")
    parser.add_argument("--step", choices=["promote", "marketplace", "all"],
                        default="all",
                        help="Which step to run (default: all)")
    args = parser.parse_args()

    if not args.expertise:
        print("[error] --expertise or EXPERTISE env var is required.", file=sys.stderr)
        sys.exit(1)

    if args.step in ("promote", "all"):
        promote_draft(args.expertise)

    if args.step in ("marketplace", "all"):
        update_marketplace(args.expertise)


if __name__ == "__main__":
    main()
