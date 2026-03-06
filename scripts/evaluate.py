#!/usr/bin/env python3
"""
evaluate.py — Evaluate and score discovered skill/plugin issues using the
GitHub Models API, then compile a recommended set for the draft plugin.

Usage:
  python3 scripts/evaluate.py --expertise terraformer [--dry-run] [--output drafts/terraformer]

Environment variables:
  GITHUB_TOKEN        Required for GitHub API and GitHub Models API
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
MODELS_API = "https://models.inference.ai.azure.com"
DEFAULT_MODEL = "gpt-4o-mini"


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
        "Authorization": f"Bearer {GITHUB_TOKEN}",
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


def score_discovery_issue(issue_body: str, expertise: str) -> Dict[str, Any]:
    """Use AI to score a discovery issue for relevance and quality."""
    system = (
        "You are an expert evaluator for AI plugin marketplaces. "
        "You score discovered skill/plugin resources for relevance, quality, and completeness. "
        "Respond ONLY with a JSON object — no markdown fences, no explanation."
    )
    user = f"""Score the following discovered resource for the expertise '{expertise}'.

Issue body:
{issue_body[:3000]}

Return a JSON object with these fields:
- relevance: integer 1-10 (how relevant to the expertise)
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
    expertise: str,
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
    user = f"""Based on the following discovered resources for expertise '{expertise}':

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
            "name": expertise,
            "description": f"Auto-generated {expertise} plugin (AI unavailable)",
            "version": "0.1.0",
            "keywords": [expertise],
            "category": "automation",
            "tags": [expertise],
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
        return {"name": expertise, "description": raw[:200], "version": "0.1.0",
                "keywords": [], "category": "", "tags": [], "skills": [], "agents": [],
                "enrichment_notes": "Could not parse AI response"}


# ---------------------------------------------------------------------------
# GitHub issue fetching
# ---------------------------------------------------------------------------

def get_discovery_issues(expertise: str) -> List[Dict]:
    """Fetch all open issues labeled expertise/{expertise} + status/discovered."""
    label = urllib.parse.quote(f"expertise/{expertise}")
    status = urllib.parse.quote("status/discovered")
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues?labels={label},{status}&state=open&per_page=50"
    issues = _get(url)
    if not issues:
        return []
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "body": i.get("body") or "",
            "url": i["html_url"],
            "labels": [lbl["name"] for lbl in i.get("labels", [])],
        }
        for i in issues
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
    # Remove old label
    url = f"{GITHUB_API}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/labels/{urllib.parse.quote(old_label)}"
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

def write_draft_plugin(expertise: str, draft: Dict, output_dir: str) -> None:
    """Write plugin.json and skill stubs to the output directory."""
    os.makedirs(output_dir, exist_ok=True)

    # plugin.json
    manifest = {
        "name": draft.get("name", expertise),
        "description": draft.get("description", f"{expertise} plugin"),
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
        skill_md = f"""---
name: {skill.get('name', 'unnamed')}
description: {skill.get('description', '')}
---

{skill.get('instructions', '_Instructions to be added._')}
"""
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write(skill_md)

    # Agents
    agents_dir = os.path.join(output_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)
    for agent in draft.get("agents", []):
        agent_name = agent.get("name", "agent")
        tools = json.dumps(agent.get("tools", ["bash", "view"]))
        agent_md = f"""---
name: {agent_name}
description: {agent.get('description', '')}
tools: {tools}
---

{agent.get('system_prompt', '_System prompt to be added._')}
"""
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

def evaluate(expertise: str, dry_run: bool, output_dir: str) -> int:
    if not GITHUB_TOKEN:
        print("[error] GITHUB_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    print(f"[evaluate] Expertise: {expertise}  Repo: {GITHUB_REPOSITORY}  Dry-run: {dry_run}")
    print()

    print("=== Fetching discovery issues ===")
    issues = get_discovery_issues(expertise)
    print(f"  Found {len(issues)} discovery issues")
    if not issues:
        print("  No issues to evaluate. Run discover.py first.")
        return 0
    print()

    print("=== Scoring issues with AI ===")
    evaluated: List[Dict] = []
    for issue in issues:
        print(f"  Scoring issue #{issue['number']}: {issue['title'][:60]}")
        score = score_discovery_issue(issue["body"], expertise)
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
        time.sleep(1)
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
    draft = compile_plugin_draft(expertise, evaluated)
    print(f"  Draft name: {draft.get('name')}  Skills: {len(draft.get('skills', []))}  Agents: {len(draft.get('agents', []))}")
    print()

    if output_dir:
        print("=== Writing draft plugin ===")
        write_draft_plugin(expertise, draft, output_dir)
        print()

    print("[evaluate] Done.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and score discovered skill issues")
    parser.add_argument("--expertise", required=True, help="Expertise name (e.g. terraformer)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without making API calls")
    parser.add_argument("--output", default="", help="Directory to write the draft plugin (default: drafts/{expertise})")
    args = parser.parse_args()

    output_dir = args.output or os.path.join("drafts", args.expertise)
    sys.exit(evaluate(args.expertise, args.dry_run, output_dir))


if __name__ == "__main__":
    main()
