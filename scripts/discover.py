#!/usr/bin/env python3
"""
discover.py — Query skill/plugin marketplaces for a given plugin and
create GitHub issues for each discovered resource.

Usage:
  python3 scripts/discover.py --plugin terraformer [--dry-run]
  python3 scripts/discover.py --plugin terraformer --langs bash,hcl --platforms aws,azure

Environment variables:
  GITHUB_TOKEN        Required for GitHub API calls and issue creation
  GITHUB_REPOSITORY   Owner/repo (e.g. LederWorks/veiled-market)
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Set

# Registry for deduplication
sys.path.insert(0, os.path.dirname(__file__))
from registry import Registry, content_sha, parse_tags, platform_label  # noqa: E402


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "LederWorks/veiled-market")
GITHUB_API = "https://api.github.com"

# ---------------------------------------------------------------------------
# Resource type configuration
# ---------------------------------------------------------------------------

# File path patterns (re.search) that identify each resource type in a repo tree.
RESOURCE_PATTERNS: Dict[str, List[str]] = {
    "agents":       [r"(?:^|/)([\w.-]+)\.agent\.md$"],
    "commands":     [r"(?:^|/)([\w.-]+)\.command\.md$"],
    "hooks":        [r"(?:^|/)hooks\.json$"],
    "instructions": [r"(?:^|/)([\w.-]+)\.instructions\.md$", r"(?:^|/)([\w.-]+)\.prompt\.md$"],
    "mcp":          [r"(?:^|/)\.mcp\.json$"],
    "plugins":      [r"(?:^|/)plugin\.json$"],
    "skills":       [r"(?:^|/)SKILL\.md$"],
    "workflows":    [r"(?:^|/)([\w.-]+)\.workflow\.md$"],
}

# Maps resource type to the GitHub label applied to its discovery issues.
RESOURCE_TYPE_LABEL: Dict[str, str] = {
    "agents":       "type/agent",
    "commands":     "type/instruction",
    "hooks":        "type/hook",
    "instructions": "type/instruction",
    "mcp":          "type/mcp",
    "plugins":      "type/plugin",
    "skills":       "type/skill",
    "workflows":    "type/instruction",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "veiled-market-discover/1.0",
    }
    if extra:
        h.update(extra)
    return h


def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  [warn] GET {url} → HTTP {exc.code}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"  [warn] GET {url} → {exc}", file=sys.stderr)
        return None


def _post(url: str, payload: Dict) -> Any:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"  [warn] POST {url} → HTTP {exc.code}: {body[:200]}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"  [warn] POST {url} → {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Repo resource fetcher (GitHub Trees API — no search rate limits)
# ---------------------------------------------------------------------------

def _repo_default_branch(repo: str) -> Optional[str]:
    data = _get(f"{GITHUB_API}/repos/{repo}")
    return data.get("default_branch", "main") if data else None


def fetch_repo_resources(source: Dict, keywords: str, resource_type: str) -> List[Dict]:
    """Walk the full file tree of a repo and return files matching the resource type.

    Uses the Git Trees API (``?recursive=1``) which does not count against the
    code-search rate limit and returns every blob path in one request.

    When ``resource_type`` is ``"plugins"``, each found ``plugin.json`` is also
    *unwrapped*: the plugin's directory is scanned for agents, skills, hooks,
    mcp servers, commands, instructions and workflows, each returned as a
    separate item with its own ``resource_type`` set.  The items therefore
    appear in both the plugin registry entry **and** their respective type
    entries — no duplicate files, no separate registry files needed.
    """
    repo = source.get("repo", "")
    if not repo:
        return []

    repo_data = _get(f"{GITHUB_API}/repos/{repo}")
    if not repo_data:
        return []
    default_branch = repo_data.get("default_branch", "main")
    repo_desc = repo_data.get("description") or ""

    tree_data = _get(f"{GITHUB_API}/repos/{repo}/git/trees/{default_branch}?recursive=1")
    if not tree_data:
        return []

    patterns = RESOURCE_PATTERNS.get(resource_type, [])
    if not patterns:
        return []

    kw = keywords.lower()
    tree_items = tree_data.get("tree", [])

    def _make_item(path: str, sha_val: str, rtype: str) -> Dict:
        html_url = f"https://github.com/{repo}/blob/{default_branch}/{path}"
        raw_url = f"https://raw.githubusercontent.com/{repo}/{default_branch}/{path}"
        return {
            "source": source["id"],
            "name": path.split("/")[-1],
            "repo": repo,
            "path": path,
            "url": html_url,
            "raw_url": raw_url,
            "description": repo_desc,
            "sha": sha_val,
            "resource_type": rtype,
        }

    results = []
    for item in tree_items:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        # Must match at least one resource-type pattern
        if not any(re.search(pat, path, re.IGNORECASE) for pat in patterns):
            continue
        # Keyword must appear in the path, repo name, or repo description
        if kw and kw not in path.lower() and kw not in repo.lower() and kw not in repo_desc.lower():
            continue
        results.append(_make_item(path, item.get("sha", ""), resource_type))

    # ------------------------------------------------------------------
    # Plugin unwrapping: for every plugin.json discovered above, scan its
    # containing directory for all other resource types and emit them as
    # individual items.  This means one discovery run for "plugins" also
    # populates agents/skills/hooks/mcp/etc. — no separate scan needed,
    # and no separate registry files needed.
    # ------------------------------------------------------------------
    if resource_type == "plugins" and results:
        plugin_dirs = {
            os.path.dirname(r["path"])
            for r in results
            if r["path"].endswith("plugin.json")
        }
        seen_paths = {r["path"] for r in results}

        for pdir in plugin_dirs:
            prefix = (pdir + "/") if pdir else ""
            for comp_type, comp_patterns in RESOURCE_PATTERNS.items():
                if comp_type == "plugins":
                    continue
                for tree_item in tree_items:
                    if tree_item.get("type") != "blob":
                        continue
                    cpath = tree_item.get("path", "")
                    if prefix and not cpath.startswith(prefix):
                        continue
                    if cpath in seen_paths:
                        continue
                    if not any(re.search(pat, cpath, re.IGNORECASE) for pat in comp_patterns):
                        continue
                    # Keyword check — same rule as primary pass
                    if kw and kw not in cpath.lower() and kw not in repo.lower() and kw not in repo_desc.lower():
                        continue
                    seen_paths.add(cpath)
                    results.append(_make_item(cpath, tree_item.get("sha", ""), comp_type))

    return results


# ---------------------------------------------------------------------------
# Issue management
# ---------------------------------------------------------------------------

def ensure_labels(
    plugin: str,
    lang_tags: Set[str],
    platform_tags: Set[str],
    dry_run: bool,
) -> None:
    """Create required GitHub labels if they don't exist yet."""
    base_labels = [
        {"name": f"plugin/{plugin}", "color": "0075ca", "description": f"Plugin plugin: {plugin}"},
        {"name": "status/discovered", "color": "e4e669", "description": "Auto-discovered from a marketplace source"},
        {"name": "status/draft", "color": "fbca04", "description": "Draft plugin under compilation"},
        {"name": "status/candidate", "color": "0e8a16", "description": "Evaluated candidate ready for review"},
        {"name": "status/finalized", "color": "006b75", "description": "Finalized plugin merged to main"},
        {"name": "type/skill", "color": "d93f0b", "description": "Skill component"},
        {"name": "type/agent", "color": "b60205", "description": "Agent component"},
        {"name": "type/hook", "color": "e11d48", "description": "Hook component"},
        {"name": "type/plugin", "color": "6e40c9", "description": "Complete plugin"},
        {"name": "ai/discovery", "color": "c5def5", "description": "Created by the AI discovery workflow"},
        {"name": "ai/draft", "color": "bfdadc", "description": "Created by the AI draft workflow"},
        {"name": "ai/evaluation", "color": "d4c5f9", "description": "Created by the AI evaluation workflow"},
    ]

    # Add source labels for all entries in marketplaces.json
    source_color = "24292e"
    for src in load_sources():
        src_id = src.get("id", "")
        src_name = src.get("name", src_id)
        if src_id:
            base_labels.append({
                "name": f"source/{src_id}",
                "color": source_color,
                "description": f"Sourced from {src_name}",
            })
    lang_color = "28a745"
    for tag in sorted(lang_tags):
        base_labels.append({
            "name": f"lang/{tag}",
            "color": lang_color,
            "description": f"Language/technology: {tag}",
        })

    # Add platform labels for the requested tags (using correct sub-prefix)
    platform_color = "0078d4"
    for tag in sorted(platform_tags):
        base_labels.append({
            "name": platform_label(tag),
            "color": platform_color,
            "description": f"Platform: {tag}",
        })

    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/labels"
    existing_data = _get(url + "?per_page=100")
    existing = {lbl["name"] for lbl in (existing_data or [])}

    for lbl in base_labels:
        if lbl["name"] in existing:
            continue
        if dry_run:
            print(f"  [dry-run] Would create label: {lbl['name']}")
            continue
        result = _post(url, lbl)
        if result:
            print(f"  Created label: {lbl['name']}")
        time.sleep(0.2)


def issue_exists(title: str) -> bool:
    """Check whether an issue with this exact title already exists."""
    encoded = urllib.parse.quote(f'"{title}" repo:{GITHUB_REPOSITORY} is:issue')
    url = f"{GITHUB_API}/search/issues?q={encoded}&per_page=1"
    data = _get(url)
    return bool(data and data.get("total_count", 0) > 0)


def create_issue(title: str, body: str, labels: List[str], dry_run: bool) -> Optional[int]:
    """Create a GitHub issue and return its number."""
    if dry_run:
        print(f"  [dry-run] Would create issue: {title[:80]}")
        return None
    if issue_exists(title):
        print(f"  [skip] Issue already exists: {title[:80]}")
        return None
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues"
    payload = {"title": title, "body": body, "labels": labels}
    result = _post(url, payload)
    if result:
        number = result.get("number")
        print(f"  Created issue #{number}: {title[:80]}")
        return number
    return None


# ---------------------------------------------------------------------------
# Issue body builders
# ---------------------------------------------------------------------------

def _registry_key_comment(source: str, plugin_ref: str, skill_ref: str, sha: str) -> str:
    """Return an HTML comment embedding the registry key for this discovery.

    ``evaluate.py`` parses this comment to look up and update the exact same
    registry entry, avoiding a keying mismatch between the two scripts.
    """
    key = json.dumps({
        "source": source,
        "plugin_ref": plugin_ref,
        "skill_ref": skill_ref,
        "sha": sha,
    }, separators=(",", ":"))
    return f"<!-- veiled-market-registry:{key} -->"


def _resource_body(
    item: Dict,
    plugin: str,
    resource_type: str,
    source: Dict,
    lang_tags: Set[str],
    platform_tags: Set[str],
) -> str:
    lang_section = f"\n**Languages:** {', '.join(f'`{t}`' for t in sorted(lang_tags))}" if lang_tags else ""
    plat_section = f"\n**Platforms:** {', '.join(f'`{t}`' for t in sorted(platform_tags))}" if platform_tags else ""
    src_id = source.get("id", "")
    src_name = source.get("name", src_id)
    src_url = source.get("url", "")
    repo = item.get("repo", "")
    path = item.get("path", "")
    sha = item.get("sha") or content_sha(item.get("url", ""))
    skill_ref = f"{repo}/{path}"
    reg_comment = _registry_key_comment(src_id, repo, skill_ref, sha)
    return f"""## Discovery: `{path.split('/')[-1]}` ({resource_type})

**plugin:** `{plugin}`
**Resource type:** `{resource_type}`
**Source:** [{src_name}]({src_url})
**Repository:** [{repo}](https://github.com/{repo})
**File:** [`{path}`]({item.get('url', '')}){lang_section}{plat_section}

### Description
{item.get('description') or '_No description available._'}

### Raw URL
{item.get('raw_url', '_N/A_')}

---
_Auto-discovered by the [discover workflow](.github/workflows/01-discovery.yml)._
_This issue has been automatically labeled `status/draft` and will be picked up by the next evaluation run._

{reg_comment}
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_sources() -> List[Dict]:
    path = os.path.join(os.path.dirname(__file__), "..", "sources", "marketplaces.json")
    try:
        with open(path) as f:
            return json.load(f).get("sources", [])
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[warn] Could not load sources/marketplaces.json: {exc}", file=sys.stderr)
        return []


def discover(
    plugin: str,
    dry_run: bool,
    lang_tags: Set[str],
    platform_tags: Set[str],
    keywords: str = "",
    source_filter: str = "",
    resource_filter: str = "",
    registry_output: str = "",
) -> int:
    keywords = keywords.strip() or plugin
    if not GITHUB_TOKEN:
        print("[error] GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    print(f"[discover] plugin: {plugin}  Keywords: {keywords}  Repo: {GITHUB_REPOSITORY}  Dry-run: {dry_run}")
    if source_filter:
        print(f"           Source filter:    {source_filter}")
    if resource_filter:
        print(f"           Resource filter:  {resource_filter}")
    if lang_tags:
        print(f"           Lang filter:      {sorted(lang_tags)}")
    if platform_tags:
        print(f"           Platform filter:  {sorted(platform_tags)}")
    print()

    print("=== Ensuring labels ===")
    ensure_labels(plugin, lang_tags, platform_tags, dry_run)
    print()

    registry = Registry()

    base_labels = [f"plugin/{plugin}", "status/discovered", "status/draft", "ai/discovery"]
    lang_labels = [f"lang/{t}" for t in sorted(lang_tags)]
    platform_labels_list = [platform_label(t) for t in sorted(platform_tags)]
    filter_labels = lang_labels + platform_labels_list

    total_created = 0
    total_skipped = 0
    # Pending entries written to registry_output instead of saved in-process
    pending_entries: List[Dict] = []

    for src in load_sources():
        src_id = src.get("id", "")
        if source_filter and src_id != source_filter:
            continue

        for resource_type in src.get("resources", []):
            if resource_filter and resource_type != resource_filter:
                continue

            print(f"=== {src.get('name', src_id)} / {resource_type} ===")
            items = fetch_repo_resources(src, keywords, resource_type)
            print(f"  Found {len(items)} results")

            for item in items:
                sha = item.get("sha") or content_sha(item.get("url", ""))
                skill_ref = f"{item['repo']}/{item['path']}"
                # Use the resource type stored on the item (plugins unwrapping may
                # produce component items whose type differs from the outer loop var).
                effective_type = item.get("resource_type", resource_type)
                if not registry.needs_evaluation(src_id, item["repo"], skill_ref, sha):
                    print(f"  [skip] Already evaluated (unchanged): {skill_ref[:70]}")
                    total_skipped += 1
                    continue

                title = f"[discovery] {plugin}/{effective_type}: {skill_ref[:80]}"
                body = _resource_body(item, plugin, effective_type, src, lang_tags, platform_tags)
                type_label = RESOURCE_TYPE_LABEL.get(effective_type, "type/skill")
                labels = base_labels + [type_label, f"source/{src_id}"] + filter_labels
                n = create_issue(title, body, labels, dry_run)
                if n:
                    total_created += 1
                    entry = dict(
                        source=src_id,
                        plugin_ref=item["repo"],
                        skill_ref=skill_ref,
                        sha=sha,
                        plugin=plugin,
                        resource_type=effective_type,
                        recommendation="pending",
                        lang_tags=list(lang_tags),
                        platform_tags=list(platform_tags),
                        issue_number=n,
                        notes=f"Discovered from {src.get('name', src_id)} ({effective_type}); awaiting evaluation.",
                    )
                    if registry_output:
                        pending_entries.append(entry)
                    else:
                        registry.mark_evaluated(**entry)
                time.sleep(0.5)
            print()

    if registry_output:
        patch = {
            "source_filter": source_filter,
            "resource_filter": resource_filter,
            "entries": pending_entries,
        }
        with open(registry_output, "w") as f:
            json.dump(patch, f, indent=2)
        print(f"[discover] Registry patch written to {registry_output} ({len(pending_entries)} entries)")
    elif not dry_run and total_created > 0:
        registry.save()
        print("[discover] Registry updated.")

    print(f"[discover] Done. Created: {total_created}  Skipped: {total_skipped}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover resources for a given plugin")
    parser.add_argument("--plugin", required=True, help="plugin name (e.g. terraformer)")
    parser.add_argument(
        "--keywords",
        default="",
        help="Search term for marketplace queries (defaults to plugin; e.g. --keywords terraform)",
    )
    parser.add_argument("--source", default="", help="Limit discovery to a single source ID")
    parser.add_argument("--resource", default="", help="Limit discovery to a single resource type (e.g. skills, agents)")
    parser.add_argument(
        "--registry-output",
        default="",
        metavar="PATH",
        help="Write registry changes to this JSON patch file instead of saving in-place (used by matrix workflow jobs)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making API calls")
    parser.add_argument("--langs", default="", help="Comma-separated language tags (e.g. bash,hcl)")
    parser.add_argument("--platforms", default="", help="Comma-separated platform tags (e.g. aws,azure)")
    args = parser.parse_args()
    sys.exit(discover(
        args.plugin,
        args.dry_run,
        parse_tags(args.langs),
        parse_tags(args.platforms),
        args.keywords,
        args.source,
        args.resource,
        args.registry_output,
    ))


if __name__ == "__main__":
    main()
