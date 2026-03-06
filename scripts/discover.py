#!/usr/bin/env python3
"""
discover.py — Query skill/plugin marketplaces for a given expertise and
create GitHub issues for each discovered resource.

Usage:
  python3 scripts/discover.py --expertise terraformer [--dry-run]

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
from typing import Any, Dict, List, Optional


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

def ensure_labels(expertise: str, dry_run: bool) -> None:
    """Create required GitHub labels if they don't exist yet."""
    labels = [
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
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/labels"
    existing_data = _get(url + "?per_page=100")
    existing = {lbl["name"] for lbl in (existing_data or [])}

    for lbl in labels:
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

def _github_code_body(item: Dict, expertise: str) -> str:
    return f"""## Discovery: `{item['name']}` from GitHub code search

**Expertise:** `{expertise}`
**Source:** GitHub code search
**Repository:** [{item['repo']}](https://github.com/{item['repo']})
**File:** [`{item['path']}`]({item['url']})

### Description
{item.get('description') or '_No description available._'}

### Raw URL
{item.get('raw_url', '_N/A_')}

---
_This issue was automatically created by the [discover-skills workflow](.github/workflows/01-discover-skills.yml)._
_Next step: Review this resource and label it `status/draft` to include it in the next compile run._
"""


def _github_repo_body(item: Dict, expertise: str) -> str:
    topics = ", ".join(f"`{t}`" for t in item.get("topics", []))
    return f"""## Discovery: `{item['name']}` repository

**Expertise:** `{expertise}`
**Source:** GitHub repository search
**Repository:** [{item['repo']}]({item['url']})
**Stars:** {item.get('stars', 0)}
**License:** {item.get('license') or '_Unknown_'}
**Topics:** {topics or '_None_'}

### Description
{item.get('description') or '_No description available._'}

---
_This issue was automatically created by the [discover-skills workflow](.github/workflows/01-discover-skills.yml)._
_Next step: Review this resource and label it `status/draft` to include it in the next compile run._
"""


def _awesome_body(item: Dict, expertise: str) -> str:
    return f"""## Discovery: awesome-copilot entry

**Expertise:** `{expertise}`
**Source:** [github/awesome-copilot](https://github.com/github/awesome-copilot)

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


def discover(expertise: str, dry_run: bool) -> int:
    if not GITHUB_TOKEN:
        print("[error] GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    print(f"[discover] Expertise: {expertise}  Repo: {GITHUB_REPOSITORY}  Dry-run: {dry_run}")
    print()

    # Ensure labels exist
    print("=== Ensuring labels ===")
    ensure_labels(expertise, dry_run)
    print()

    base_labels = [f"expertise/{expertise}", "status/discovered", "ai/discovery"]
    total_created = 0

    # --- GitHub code search ---
    print("=== GitHub code search ===")
    items = search_github_code(expertise)
    print(f"  Found {len(items)} code results")
    for item in items:
        title = f"[discovery] {expertise}: SKILL.md in {item['repo']}/{item['path']}"
        body = _github_code_body(item, expertise)
        labels = base_labels + ["type/skill"]
        n = create_issue(title, body, labels, dry_run)
        if n:
            total_created += 1
        time.sleep(0.5)
    print()

    # --- GitHub repo search ---
    print("=== GitHub repository search ===")
    repos = search_github_repos(expertise)
    print(f"  Found {len(repos)} repositories")
    for item in repos:
        title = f"[discovery] {expertise}: plugin repo {item['repo']}"
        body = _github_repo_body(item, expertise)
        labels = base_labels + ["type/plugin"]
        n = create_issue(title, body, labels, dry_run)
        if n:
            total_created += 1
        time.sleep(0.5)
    print()

    # --- awesome-copilot scan ---
    print("=== awesome-copilot scan ===")
    ac_items = fetch_awesome_copilot(expertise)
    print(f"  Found {len(ac_items)} matches")
    for item in ac_items:
        title = f"[discovery] {expertise}: awesome-copilot — {item['name'][:60]}"
        body = _awesome_body(item, expertise)
        labels = base_labels + ["type/skill"]
        n = create_issue(title, body, labels, dry_run)
        if n:
            total_created += 1
        time.sleep(0.5)
    print()

    print(f"[discover] Done. Issues created: {total_created}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover skills for a given expertise")
    parser.add_argument("--expertise", required=True, help="Expertise name (e.g. terraformer)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making API calls")
    args = parser.parse_args()
    sys.exit(discover(args.expertise, args.dry_run))


if __name__ == "__main__":
    main()
