#!/usr/bin/env python3
"""
discover.py — Query skill/plugin marketplaces for a given expertise and
create GitHub issues for each discovered resource.

Usage:
  python3 scripts/discover.py --expertise terraformer [--dry-run]
  python3 scripts/discover.py --expertise terraformer --langs bash,hcl --platforms aws,azure

Environment variables:
  GITHUB_TOKEN        Required for GitHub API calls and issue creation
  GITHUB_REPOSITORY   Owner/repo (e.g. LederWorks/veiled-market)
"""

import argparse
import json
import os
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
# GitHub search
# ---------------------------------------------------------------------------

def search_github_code(expertise: str) -> List[Dict]:
    """Search GitHub code for SKILL.md files referencing the expertise."""
    results = []
    queries = [
        f"{expertise} SKILL.md in:path",
        f"{expertise} filename:SKILL.md",
        f"{expertise} filename:plugin.json iac OR terraform OR infrastructure",
    ]
    seen: set = set()
    for q in queries:
        encoded = urllib.parse.quote(q)
        url = f"{GITHUB_API}/search/code?q={encoded}&per_page=20"
        data = _get(url)
        if not data or "items" not in data:
            continue
        for item in data.get("items", []):
            key = item.get("html_url", "")
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "source": "github-search",
                "name": item.get("name", ""),
                "repo": item.get("repository", {}).get("full_name", ""),
                "path": item.get("path", ""),
                "url": item.get("html_url", ""),
                "description": item.get("repository", {}).get("description") or "",
                "raw_url": item.get("download_url") or item.get("html_url", ""),
            })
        time.sleep(1)  # be polite to the search API
    return results


def search_github_repos(expertise: str) -> List[Dict]:
    """Search GitHub repositories for plugins matching the expertise."""
    results = []
    queries = [
        f"{expertise} topic:terraform-plugin",
        f"{expertise} copilot-plugin",
        f"{expertise} claude-plugin in:name,description,topics",
    ]
    seen: set = set()
    for q in queries:
        encoded = urllib.parse.quote(q)
        url = f"{GITHUB_API}/search/repositories?q={encoded}&sort=stars&order=desc&per_page=10"
        data = _get(url)
        if not data or "items" not in data:
            continue
        for repo in data.get("items", []):
            key = repo.get("html_url", "")
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "source": "github-repos",
                "name": repo.get("name", ""),
                "repo": repo.get("full_name", ""),
                "path": "",
                "url": repo.get("html_url", ""),
                "description": repo.get("description") or "",
                "stars": repo.get("stargazers_count", 0),
                "license": (repo.get("license") or {}).get("spdx_id", ""),
                "topics": repo.get("topics", []),
            })
        time.sleep(1)
    return results


def fetch_awesome_copilot(expertise: str) -> List[Dict]:
    """Scan the awesome-copilot repo README for relevant entries."""
    url = f"{GITHUB_API}/repos/github/awesome-copilot/readme"
    data = _get(url)
    if not data:
        return []
    import base64
    try:
        content = base64.b64decode(data.get("content", "")).decode(errors="replace")
    except (ValueError, UnicodeDecodeError):
        return []
    results = []
    for line in content.splitlines():
        if expertise.lower() in line.lower():
            results.append({
                "source": "awesome-copilot",
                "name": line.strip()[:120],
                "url": "https://github.com/github/awesome-copilot",
                "description": line.strip()[:500],
                "raw_content": line.strip(),
            })
    return results[:10]


# ---------------------------------------------------------------------------
# Issue management
# ---------------------------------------------------------------------------

def ensure_labels(
    expertise: str,
    lang_tags: Set[str],
    platform_tags: Set[str],
    dry_run: bool,
) -> None:
    """Create required GitHub labels if they don't exist yet."""
    base_labels = [
        {"name": f"expertise/{expertise}", "color": "0075ca", "description": f"Plugin expertise: {expertise}"},
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

    # Add lang labels for the requested tags
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

def _github_code_body(item: Dict, expertise: str, lang_tags: Set[str], platform_tags: Set[str]) -> str:
    lang_section = f"\n**Languages:** {', '.join(f'`{t}`' for t in sorted(lang_tags))}" if lang_tags else ""
    plat_section = f"\n**Platforms:** {', '.join(f'`{t}`' for t in sorted(platform_tags))}" if platform_tags else ""
    return f"""## Discovery: `{item['name']}` from GitHub code search

**Expertise:** `{expertise}`
**Source:** GitHub code search
**Repository:** [{item['repo']}](https://github.com/{item['repo']})
**File:** [`{item['path']}`]({item['url']}){lang_section}{plat_section}

### Description
{item.get('description') or '_No description available._'}

### Raw URL
{item.get('raw_url', '_N/A_')}

---
_This issue was automatically created by the [discover-skills workflow](.github/workflows/01-discover-skills.yml)._
_Next step: Review this resource and label it `status/draft` to include it in the next compile run._
"""


def _github_repo_body(item: Dict, expertise: str, lang_tags: Set[str], platform_tags: Set[str]) -> str:
    topics = ", ".join(f"`{t}`" for t in item.get("topics", []))
    lang_section = f"\n**Languages:** {', '.join(f'`{t}`' for t in sorted(lang_tags))}" if lang_tags else ""
    plat_section = f"\n**Platforms:** {', '.join(f'`{t}`' for t in sorted(platform_tags))}" if platform_tags else ""
    return f"""## Discovery: `{item['name']}` repository

**Expertise:** `{expertise}`
**Source:** GitHub repository search
**Repository:** [{item['repo']}]({item['url']})
**Stars:** {item.get('stars', 0)}
**License:** {item.get('license') or '_Unknown_'}
**Topics:** {topics or '_None_'}{lang_section}{plat_section}

### Description
{item.get('description') or '_No description available._'}

---
_This issue was automatically created by the [discover-skills workflow](.github/workflows/01-discover-skills.yml)._
_Next step: Review this resource and label it `status/draft` to include it in the next compile run._
"""


def _awesome_body(item: Dict, expertise: str, lang_tags: Set[str], platform_tags: Set[str]) -> str:
    lang_section = f"\n**Languages:** {', '.join(f'`{t}`' for t in sorted(lang_tags))}" if lang_tags else ""
    plat_section = f"\n**Platforms:** {', '.join(f'`{t}`' for t in sorted(platform_tags))}" if platform_tags else ""
    return f"""## Discovery: awesome-copilot entry

**Expertise:** `{expertise}`
**Source:** [github/awesome-copilot](https://github.com/github/awesome-copilot){lang_section}{plat_section}

### Matched line
```
{item.get('raw_content', '')}
```

---
_This issue was automatically created by the [discover-skills workflow](.github/workflows/01-discover-skills.yml)._
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


def discover(expertise: str, dry_run: bool, lang_tags: Set[str], platform_tags: Set[str]) -> int:
    if not GITHUB_TOKEN:
        print("[error] GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    print(f"[discover] Expertise: {expertise}  Repo: {GITHUB_REPOSITORY}  Dry-run: {dry_run}")
    if lang_tags:
        print(f"           Lang filter:     {sorted(lang_tags)}")
    if platform_tags:
        print(f"           Platform filter: {sorted(platform_tags)}")
    print()

    # Ensure labels exist (including any lang/platform labels used in this run)
    print("=== Ensuring labels ===")
    ensure_labels(expertise, lang_tags, platform_tags, dry_run)
    print()

    # Load registry to skip already-evaluated unchanged skills
    registry = Registry()

    # Build issue labels list (base + lang/platform with correct sub-prefixes)
    base_labels = [f"expertise/{expertise}", "status/discovered", "ai/discovery"]
    lang_labels = [f"lang/{t}" for t in sorted(lang_tags)]
    platform_labels_list = [platform_label(t) for t in sorted(platform_tags)]
    filter_labels = lang_labels + platform_labels_list

    total_created = 0
    total_skipped = 0

    # --- GitHub code search ---
    print("=== GitHub code search ===")
    items = search_github_code(expertise)
    print(f"  Found {len(items)} code results")
    for item in items:
        skill_ref = f"{item['repo']}/{item['path']}"
        sha = content_sha(item.get("url", skill_ref))
        if not registry.needs_evaluation("github-search", item["repo"], skill_ref, sha):
            print(f"  [skip] Already evaluated (unchanged): {skill_ref[:80]}")
            total_skipped += 1
            continue
        title = f"[discovery] {expertise}: SKILL.md in {item['repo']}/{item['path']}"
        body = _github_code_body(item, expertise, lang_tags, platform_tags)
        labels = base_labels + ["type/skill"] + filter_labels
        n = create_issue(title, body, labels, dry_run)
        if n:
            total_created += 1
            # Record as pending evaluation (no score yet)
            registry.mark_evaluated(
                source="github-search",
                plugin_ref=item["repo"],
                skill_ref=skill_ref,
                sha=sha,
                expertise=expertise,
                recommendation="pending",
                lang_tags=list(lang_tags),
                platform_tags=list(platform_tags),
                issue_number=n,
                notes="Discovered; awaiting AI evaluation.",
            )
        time.sleep(0.5)
    print()

    # --- GitHub repo search ---
    print("=== GitHub repository search ===")
    repos = search_github_repos(expertise)
    print(f"  Found {len(repos)} repositories")
    for item in repos:
        skill_ref = item["repo"]
        sha = content_sha(f"{skill_ref}:stars={item.get('stars', 0)}")
        if not registry.needs_evaluation("github-repos", item["repo"], skill_ref, sha):
            print(f"  [skip] Already evaluated (unchanged): {skill_ref[:80]}")
            total_skipped += 1
            continue
        title = f"[discovery] {expertise}: plugin repo {item['repo']}"
        body = _github_repo_body(item, expertise, lang_tags, platform_tags)
        labels = base_labels + ["type/plugin"] + filter_labels
        n = create_issue(title, body, labels, dry_run)
        if n:
            total_created += 1
            registry.mark_evaluated(
                source="github-repos",
                plugin_ref=item["repo"],
                skill_ref=skill_ref,
                sha=sha,
                expertise=expertise,
                recommendation="pending",
                lang_tags=list(lang_tags),
                platform_tags=list(platform_tags),
                issue_number=n,
                notes="Repo discovered; awaiting AI evaluation.",
            )
        time.sleep(0.5)
    print()

    # --- awesome-copilot scan ---
    print("=== awesome-copilot scan ===")
    ac_items = fetch_awesome_copilot(expertise)
    print(f"  Found {len(ac_items)} matches")
    for item in ac_items:
        raw = item.get("raw_content", item.get("name", ""))
        sha = content_sha(raw)
        skill_ref = raw[:80]
        if not registry.needs_evaluation("awesome-copilot", "github/awesome-copilot", skill_ref, sha):
            print(f"  [skip] Already evaluated (unchanged): {skill_ref[:60]}")
            total_skipped += 1
            continue
        title = f"[discovery] {expertise}: awesome-copilot — {item['name'][:60]}"
        body = _awesome_body(item, expertise, lang_tags, platform_tags)
        labels = base_labels + ["type/skill", "source/awesome-copilot"] + filter_labels
        n = create_issue(title, body, labels, dry_run)
        if n:
            total_created += 1
            registry.mark_evaluated(
                source="awesome-copilot",
                plugin_ref="github/awesome-copilot",
                skill_ref=skill_ref,
                sha=sha,
                expertise=expertise,
                recommendation="pending",
                lang_tags=list(lang_tags),
                platform_tags=list(platform_tags),
                issue_number=n,
                notes="Awesome-copilot entry; awaiting AI evaluation.",
            )
        time.sleep(0.5)
    print()

    # Persist updated registry
    if not dry_run and (total_created > 0):
        registry.save()
        print("[discover] Registry updated.")

    print(f"[discover] Done. Issues created: {total_created}  Skipped (already evaluated): {total_skipped}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover skills for a given expertise")
    parser.add_argument("--expertise", required=True, help="Expertise name (e.g. terraformer)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making API calls")
    parser.add_argument(
        "--langs",
        default="",
        help="Comma-separated language tags to filter/label (e.g. bash,hcl)",
    )
    parser.add_argument(
        "--platforms",
        default="",
        help="Comma-separated platform tags to filter/label (e.g. aws,azure,github-actions)",
    )
    args = parser.parse_args()
    sys.exit(discover(args.expertise, args.dry_run, parse_tags(args.langs), parse_tags(args.platforms)))


if __name__ == "__main__":
    main()
