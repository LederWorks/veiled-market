#!/usr/bin/env python3
"""
evaluate.py — Evaluate and score discovered skill/plugin issues using the
GitHub Models API, then compile a recommended set for the draft plugin.

Usage:
  python3 scripts/evaluate.py --plugin terraformer [--dry-run] [--output drafts/terraformer]

Environment variables:
  GITHUB_TOKEN        Required for GitHub REST API and gh CLI
  MODELS_TOKEN        Required for GitHub Models API (PAT with `models` permission).
                      Falls back to GITHUB_TOKEN if not set (works for user PATs, not App tokens).
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
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from registry import Registry, content_sha, extract_platform_tags_from_labels  # noqa: E402


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
# GitHub Models API requires a PAT with the `models` permission.
# GitHub App installation tokens (GITHUB_TOKEN in Actions) do NOT have this permission.
MODELS_TOKEN = os.environ.get("MODELS_TOKEN") or GITHUB_TOKEN
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "LederWorks/veiled-market")
GITHUB_API = "https://api.github.com"
MODELS_API = "https://models.inference.ai.azure.com"
DEFAULT_MODEL = "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Registry key parsing
# ---------------------------------------------------------------------------

_REGISTRY_KEY_RE = re.compile(r"<!--\s*veiled-market-registry:(\{.*?\})\s*-->", re.DOTALL)


def _parse_registry_key(issue_body: str) -> Optional[Tuple[str, str, str, str]]:
    """Extract the embedded registry key from an issue body.

    Returns ``(source, plugin_ref, skill_ref, sha)`` or ``None`` if no key is found.
    The key is embedded by ``discover.py`` as an HTML comment:
    ``<!-- veiled-market-registry:{"source":...} -->``.
    """
    m = _REGISTRY_KEY_RE.search(issue_body)
    if not m:
        return None
    try:
        key = json.loads(m.group(1))
        return (
            key.get("source", ""),
            key.get("plugin_ref", ""),
            key.get("skill_ref", ""),
            key.get("sha", ""),
        )
    except (json.JSONDecodeError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _gh_headers() -> Dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "veiled-market-evaluate/1.0",
    }


def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers=_gh_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  [warn] GET {url} → HTTP {exc.code}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"  [warn] GET {url} → {exc}", file=sys.stderr)
        return None


def _post(url: str, payload: Dict, headers: Optional[Dict] = None) -> Any:
    data = json.dumps(payload).encode()
    h = headers or _gh_headers()
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        print(f"  [warn] POST {url} → HTTP {exc.code}: {body[:300]}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"  [warn] POST {url} → {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# GitHub Models (AI)
# ---------------------------------------------------------------------------

def ai_complete(system: str, user: str, model: str = DEFAULT_MODEL) -> str:
    """Call GitHub Models chat completion. Returns the assistant message text."""
    url = f"{MODELS_API}/chat/completions"
    headers = {
        "Authorization": f"Bearer {MODELS_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "veiled-market-evaluate/1.0",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }
    result = _post(url, payload, headers=headers)
    if result and "choices" in result:
        return result["choices"][0]["message"]["content"].strip()
    return ""


def score_discovery_issue(issue_body: str, plugin: str) -> Dict[str, Any]:
    """Use AI to score a discovery issue for relevance and quality."""
    system = (
        "You are an expert evaluator for AI plugin marketplaces. "
        "You score discovered skill/plugin resources for relevance, quality, and completeness. "
        "Respond ONLY with a JSON object — no markdown fences, no explanation."
    )
    user = f"""Score the following discovered resource for the plugin '{plugin}'.

Issue body:
{issue_body[:3000]}

Return a JSON object with these fields:
- relevance: integer 1-10 (how relevant to the plugin)
- quality: integer 1-10 (quality of the content/description)
- completeness: integer 1-10 (how complete / actionable it is)
- platform_fit: integer 1-10 (how well it fits Copilot CLI / Claude Code plugin format)
- summary: string (one sentence describing what this resource offers)
- recommendation: "include" | "exclude" | "enrich"
- reason: string (brief justification for the recommendation)
"""
    raw = ai_complete(system, user)
    if not raw:
        return {
            "relevance": 5, "quality": 5, "completeness": 5, "platform_fit": 5,
            "summary": "Could not evaluate (AI unavailable)",
            "recommendation": "include",
            "reason": "Default — AI evaluation unavailable",
        }
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from within the text
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "relevance": 5, "quality": 5, "completeness": 5, "platform_fit": 5,
            "summary": raw[:200],
            "recommendation": "include",
            "reason": "Could not parse AI response as JSON",
        }


def compile_plugin_draft(
    plugin: str,
    evaluated_issues: List[Dict],
) -> Dict[str, Any]:
    """Use AI to synthesise a plugin draft from the top-scoring issues."""
    included = [e for e in evaluated_issues if e["score"]["recommendation"] in ("include", "enrich")]
    if not included:
        included = evaluated_issues[:5]

    summaries = "\n".join(
        f"- [{i+1}] {e['score'].get('summary', e['title'][:80])}"
        for i, e in enumerate(included)
    )

    system = (
        "You are an expert Terraform and AI plugin developer. "
        "You synthesise plugin components from multiple discovered sources into a cohesive plugin. "
        "Always follow the SKILL.md and plugin.json specifications for GitHub Copilot CLI and Claude Code plugins."
    )
    user = f"""Based on the following discovered resources for plugin '{plugin}':

{summaries}

Generate a JSON object describing an enriched plugin draft with these fields:
- name: string (kebab-case plugin name)
- description: string (concise description, max 200 chars)
- version: "0.1.0"
- keywords: array of strings
- category: string
- tags: array of strings
- skills: array of objects, each with:
    - name: string (kebab-case skill name)
    - description: string
    - instructions: string (markdown skill instructions, 3-5 bullet points)
- agents: array of objects, each with:
    - name: string
    - description: string
    - tools: array of tool names
    - system_prompt: string (concise agent system prompt)
- enrichment_notes: string (what was merged from multiple sources)

Respond ONLY with valid JSON — no markdown fences.
"""
    raw = ai_complete(system, user)
    if not raw:
        return {
            "name": plugin,
            "description": f"Auto-generated {plugin} plugin (AI unavailable)",
            "version": "0.1.0",
            "keywords": [plugin],
            "category": "automation",
            "tags": [plugin],
            "skills": [],
            "agents": [],
            "enrichment_notes": "AI evaluation was unavailable; manual enrichment required.",
        }
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"name": plugin, "description": raw[:200], "version": "0.1.0",
                "keywords": [], "category": "", "tags": [], "skills": [], "agents": [],
                "enrichment_notes": "Could not parse AI response"}


# ---------------------------------------------------------------------------
# GitHub issue fetching
# ---------------------------------------------------------------------------

def get_discovery_issues(plugin: str) -> List[Dict]:
    """Fetch all open issues labeled plugin/{plugin} + status/draft.

    Tries the REST API first; falls back to ``gh issue list`` when the token
    lacks direct API access (e.g. workflow_run context on org repos).
    """
    import subprocess

    label = urllib.parse.quote(f"plugin/{plugin}")
    status = urllib.parse.quote("status/draft")
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues?labels={label},{status}&state=open&per_page=100"

    def _parse_rest(issues_list: List) -> List[Dict]:
        return [
            {
                "number": i["number"],
                "title": i["title"],
                "body": i.get("body") or "",
                "url": i["html_url"],
                "labels": [lbl["name"] for lbl in i.get("labels", [])],
            }
            for i in issues_list
            if isinstance(i, dict)
        ]

    # --- REST API path ---
    first_page = _get(url)
    if first_page is not None:
        all_issues = list(first_page)
        page = 2
        while len(first_page) == 100:
            first_page = _get(f"{url}&page={page}") or []
            all_issues.extend(first_page)
            page += 1
        return _parse_rest(all_issues)

    # --- gh CLI fallback (handles workflow_run token restrictions on org repos) ---
    print("  [info] REST API returned no data — falling back to gh CLI", file=sys.stderr)
    result = subprocess.run(
        [
            "gh", "issue", "list",
            "--repo", GITHUB_REPOSITORY,
            "--label", f"plugin/{plugin}",
            "--label", "status/draft",
            "--state", "open",
            "--limit", "200",
            "--json", "number,title,body,url,labels",
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  [warn] gh issue list failed: {result.stderr[:200]}", file=sys.stderr)
        return []
    try:
        raw = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return []
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "body": i.get("body") or "",
            "url": i.get("url", ""),
            "labels": [lbl["name"] for lbl in i.get("labels", [])],
        }
        for i in raw
        if isinstance(i, dict)
    ]


def add_score_comment(issue_number: int, score: Dict, dry_run: bool) -> None:
    """Post a scoring comment on a discovery issue."""
    rec_emoji = {"include": "✅", "enrich": "🔧", "exclude": "❌"}.get(
        score.get("recommendation", ""), "ℹ️"
    )
    body = f"""## 🤖 AI Evaluation Score

| Dimension | Score |
|-----------|-------|
| Relevance | {score.get('relevance', '?')}/10 |
| Quality | {score.get('quality', '?')}/10 |
| Completeness | {score.get('completeness', '?')}/10 |
| Platform fit | {score.get('platform_fit', '?')}/10 |

**Recommendation:** {rec_emoji} `{score.get('recommendation', 'unknown')}`

**Summary:** {score.get('summary', '_n/a_')}

**Reason:** {score.get('reason', '_n/a_')}

---
_Evaluated by [evaluate-and-enrich workflow](.github/workflows/03-evaluate-enrich.yml)_
"""
    if dry_run:
        print(f"  [dry-run] Would comment on issue #{issue_number}")
        return
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/comments"
    _post(url, {"body": body})
    time.sleep(0.3)


def update_issue_label(issue_number: int, old_label: str, new_label: str, dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] Would relabel issue #{issue_number}: {old_label} → {new_label}")
        return
    # Remove old label (encode '/' so the path isn't treated as nested)
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/labels/{urllib.parse.quote(old_label, safe='')}"
    req = urllib.request.Request(url, headers=_gh_headers(), method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: BLE001
        pass
    # Add new label
    _post(
        f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/labels",
        {"labels": [new_label]},
    )
    time.sleep(0.3)


# ---------------------------------------------------------------------------
# Draft file generation
# ---------------------------------------------------------------------------

def write_draft_plugin(plugin: str, draft: Dict, output_dir: str) -> None:
    """Write plugin.json and skill stubs to the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    # plugin.json
    manifest = {
        "name": draft.get("name", plugin),
        "description": draft.get("description", f"{plugin} plugin"),
        "version": draft.get("version", "0.1.0"),
        "keywords": draft.get("keywords", []),
        "category": draft.get("category", ""),
        "tags": draft.get("tags", []),
        "agents": "agents/",
        "skills": "skills/",
    }
    with open(os.path.join(output_dir, "plugin.json"), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    # Skills
    for skill in draft.get("skills", []):
        skill_dir = os.path.join(output_dir, "skills", skill.get("name", "unnamed-skill"))
        os.makedirs(skill_dir, exist_ok=True)
        # Build platforms/languages frontmatter lines only when values are present
        platforms = skill.get("platforms", [])
        languages = skill.get("languages", [])
        extra_fm = "".join([
            f"platforms: {json.dumps(platforms)}\n" if platforms else "",
            f"languages: {json.dumps(languages)}\n" if languages else "",
        ])
        skill_md = (
            f"---\n"
            f"name: {skill.get('name', 'unnamed')}\n"
            f"description: {skill.get('description', '')}\n"
            f"{extra_fm}"
            f"---\n\n"
            f"{skill.get('instructions', '_Instructions to be added._')}\n"
        )
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write(skill_md)

    # Agents
    agents_dir = os.path.join(output_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)
    for agent in draft.get("agents", []):
        agent_name = agent.get("name", "agent")
        tools = json.dumps(agent.get("tools", ["bash", "view"]))
        platforms = agent.get("platforms", [])
        languages = agent.get("languages", [])
        extra_fm = "".join([
            f"platforms: {json.dumps(platforms)}\n" if platforms else "",
            f"languages: {json.dumps(languages)}\n" if languages else "",
        ])
        agent_md = (
            f"---\n"
            f"name: {agent_name}\n"
            f"description: {agent.get('description', '')}\n"
            f"tools: {tools}\n"
            f"{extra_fm}"
            f"---\n\n"
            f"{agent.get('system_prompt', '_System prompt to be added._')}\n"
        )
        with open(os.path.join(agents_dir, f"{agent_name}.agent.md"), "w") as f:
            f.write(agent_md)

    # Enrichment notes
    notes = draft.get("enrichment_notes", "")
    if notes:
        with open(os.path.join(output_dir, "ENRICHMENT_NOTES.md"), "w") as f:
            f.write(f"# Enrichment Notes\n\n{notes}\n")

    print(f"  Draft written to: {output_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def evaluate(plugin: str, dry_run: bool, output_dir: str) -> int:
    if not GITHUB_TOKEN:
        print("[error] GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    print(f"[evaluate] plugin: {plugin}  Repo: {GITHUB_REPOSITORY}  Dry-run: {dry_run}")
    print()

    # Load registry to check which issues have already been evaluated
    registry = Registry()

    print("=== Fetching discovery issues ===")
    issues = get_discovery_issues(plugin)
    print(f"  Found {len(issues)} discovery issues")
    if not issues:
        print("  No issues to evaluate. Run discover.py first.")
        return 0
    print()

    print("=== Scoring issues with AI ===")
    evaluated: List[Dict] = []
    skipped = 0
    for issue in issues:
        issue_body = issue.get("body", "")

        # Try to recover the exact registry key embedded by discover.py.
        # This aligns discover→evaluate on the same (source, plugin_ref, skill_ref, sha)
        # tuple so dedup works across both scripts.
        embedded_key = _parse_registry_key(issue_body)
        if embedded_key:
            reg_source, reg_plugin_ref, reg_skill_ref, reg_sha = embedded_key
        else:
            # Fallback: derive source from issue labels; use issue-number as skill_ref
            reg_source = "github-issues"
            for lbl in issue.get("labels", []):
                if lbl.startswith("source/"):
                    reg_source = lbl.replace("source/", "", 1)
                    break
            reg_plugin_ref = plugin
            reg_skill_ref = f"issue#{issue['number']}"
            # SHA of the issue body detects content changes when no embedded key
            reg_sha = content_sha(issue_body)

        if not registry.needs_evaluation(reg_source, reg_plugin_ref, reg_skill_ref, reg_sha):
            cached = registry.get_entry(reg_source, reg_plugin_ref, reg_skill_ref)
            print(
                f"  [skip] Issue #{issue['number']} already evaluated "
                f"(sha unchanged, rec={cached.get('recommendation','?')}): "
                f"{issue['title'][:50]}"
            )
            skipped += 1
            # Still include it in evaluated list using cached score
            cached_score = dict(cached.get("score", {}))
            cached_score.setdefault("recommendation", cached.get("recommendation", "include"))
            evaluated.append({**issue, "score": cached_score})
            continue

        print(f"  Scoring issue #{issue['number']}: {issue['title'][:60]}")
        score = score_discovery_issue(issue_body, plugin)
        overall = (
            score.get("relevance", 5)
            + score.get("quality", 5)
            + score.get("completeness", 5)
            + score.get("platform_fit", 5)
        ) / 4
        score["overall"] = round(overall, 1)
        print(f"    → {score['recommendation']} (overall {score['overall']}/10): {score.get('summary','')[:60]}")
        add_score_comment(issue["number"], score, dry_run)
        evaluated.append({**issue, "score": score})

        # Update the registry entry using the exact same key as discover.py
        lang_tags = [lbl.replace("lang/", "") for lbl in issue.get("labels", []) if lbl.startswith("lang/")]
        platform_tags = extract_platform_tags_from_labels(
            [lbl for lbl in issue.get("labels", []) if lbl.startswith("platform/")]
        )
        registry.mark_evaluated(
            source=reg_source,
            plugin_ref=reg_plugin_ref,
            skill_ref=reg_skill_ref,
            sha=reg_sha,
            plugin=plugin,
            score=score,
            recommendation=score.get("recommendation", "include"),
            lang_tags=lang_tags,
            platform_tags=platform_tags,
            issue_number=issue["number"],
            notes=score.get("summary", ""),
        )
        time.sleep(1)

    print(f"  Scored: {len(evaluated) - skipped}  Skipped (cached): {skipped}")
    print()

    # Update labels based on recommendation
    print("=== Updating labels ===")
    for e in evaluated:
        rec = e["score"].get("recommendation", "include")
        if rec in ("include", "enrich"):
            update_issue_label(e["number"], "status/discovered", "status/draft", dry_run)
        else:
            update_issue_label(e["number"], "status/discovered", "status/excluded", dry_run)
    print()

    # Sort by overall score (descending)
    evaluated.sort(key=lambda x: x["score"].get("overall", 0), reverse=True)

    print("=== Compiling plugin draft with AI ===")
    draft = compile_plugin_draft(plugin, evaluated)
    print(f"  Draft name: {draft.get('name')}  Skills: {len(draft.get('skills', []))}  Agents: {len(draft.get('agents', []))}")
    print()

    if output_dir:
        print("=== Writing draft plugin ===")
        write_draft_plugin(plugin, draft, output_dir)
        print()

    # Persist registry changes
    if not dry_run:
        registry.save()
        print("[evaluate] Registry updated.")

    print("[evaluate] Done.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and score discovered skill issues")
    parser.add_argument("--plugin", required=True, help="plugin name (e.g. terraformer)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making API calls")
    parser.add_argument("--output", default="", help="Directory to write the draft plugin (default: drafts/{plugin})")
    args = parser.parse_args()

    output_dir = args.output or os.path.join("drafts", args.plugin)
    sys.exit(evaluate(args.plugin, args.dry_run, output_dir))


if __name__ == "__main__":
    main()
