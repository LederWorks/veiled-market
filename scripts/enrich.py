#!/usr/bin/env python3
"""
enrich.py — AI-powered enrichment step for the evaluate-and-enrich workflow.
Reads all draft plugin.json files from /tmp/all-drafts, calls GitHub Models API
to merge the best elements, and writes the enriched plugin.json to drafts/{expertise}/.

Usage:
  python3 scripts/enrich.py

Environment variables:
  GITHUB_TOKEN   For GitHub Models API
  EXPERTISE      The expertise name (e.g. terraformer)
"""

import json
import os
import sys
import urllib.error
import urllib.request

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
EXPERTISE = os.environ.get("EXPERTISE", "")
MODELS_API = "https://models.inference.ai.azure.com"
DRAFT_DIR = "/tmp/all-drafts"


def ai_complete(system: str, user: str) -> str:
    """Call GitHub Models API."""
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{MODELS_API}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "veiled-market/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, OSError) as exc:
        print(f"[warn] AI API call failed: {exc}", file=sys.stderr)
        return ""


def main() -> None:
    if not EXPERTISE:
        print("[error] EXPERTISE environment variable is required.", file=sys.stderr)
        sys.exit(1)

    # Load all draft plugin.json files
    drafts = []
    if os.path.isdir(DRAFT_DIR):
        for entry in sorted(os.listdir(DRAFT_DIR)):
            path = os.path.join(DRAFT_DIR, entry, "plugin.json")
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        drafts.append(json.load(f))
                except (OSError, json.JSONDecodeError):
                    pass

    if not drafts:
        print("No drafts found to enrich. Creating a placeholder.")
        out_dir = f"drafts/{EXPERTISE}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}/plugin.json", "w") as f:
            json.dump(
                {"name": EXPERTISE, "version": "0.1.0",
                 "description": f"{EXPERTISE} plugin (no drafts found)"},
                f, indent=2,
            )
            f.write("\n")
        return

    drafts_summary = json.dumps(drafts, indent=2)[:6000]

    system = (
        "You are an expert plugin architect. Given multiple draft plugins, "
        "select the best base and enrich it with unique features from the others. "
        "Respond ONLY with a valid JSON object — no markdown fences."
    )
    user = (
        f"Here are {len(drafts)} draft plugins for expertise '{EXPERTISE}':\n\n"
        f"{drafts_summary}\n\n"
        "Create an enriched plugin.json that:\n"
        "1. Uses the best base plugin as the starting point\n"
        "2. Merges unique keywords, tags, and categories from others\n"
        "3. Notes which features were merged from dropped drafts in a 'enrichment_notes' string field\n"
        "Return only the enriched plugin.json object."
    )

    raw = ai_complete(system, user)
    enriched = None

    if raw:
        # Strip markdown fences if present
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        try:
            enriched = json.loads(raw)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    enriched = json.loads(match.group())
                except json.JSONDecodeError:
                    pass

    if not enriched:
        print("[warn] AI enrichment failed or returned invalid JSON. Using best draft as-is.")
        enriched = drafts[0]
        enriched["enrichment_notes"] = "AI enrichment unavailable; best draft used as-is."

    out_dir = f"drafts/{EXPERTISE}"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/plugin.json", "w") as f:
        json.dump(enriched, f, indent=2)
        f.write("\n")
    print(f"Enriched plugin.json written for '{EXPERTISE}'")


if __name__ == "__main__":
    main()
