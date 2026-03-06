#!/usr/bin/env python3
"""
registry.py — Read/write the veiled-market skill evaluation registry.

The registry tracks every public skill/plugin resource that has been evaluated so
the discovery and evaluation workflows can skip unchanged content.

Hierarchy::

    marketplaces
      └── {source_id}               e.g. "github-search", "skillsmp"
            └── {plugin_ref}        e.g. "owner/repo" or "skillsmp/terraform-skills"
                  └── {skill_ref}   e.g. "path/SKILL.md" or the skill's canonical URL

Each leaf entry has::

    {
        "sha":            "<content SHA-256 or git blob SHA>",
        "last_evaluated": "<ISO-8601 UTC>",
        "expertise":      "terraformer",
        "lang_tags":      ["bash", "hcl"],
        "platform_tags":  ["aws", "azure", "gcp"],
        "score": {
            "relevance":    8,
            "quality":      7,
            "completeness": 6,
            "platform_fit": 8,
            "overall":      7.3
        },
        "recommendation": "include",   # include | exclude | enrich
        "issue_number":   42,          # linked GitHub issue (if any)
        "notes":          "..."
    }

Usage::

    from scripts.registry import Registry

    reg = Registry()
    if not reg.needs_evaluation("github-search", "owner/repo", "path/SKILL.md", sha="abc"):
        print("Already evaluated, skipping")
    else:
        score = ...
        reg.mark_evaluated(
            source="github-search",
            plugin_ref="owner/repo",
            skill_ref="path/SKILL.md",
            sha="abc",
            expertise="terraformer",
            score=score,
            recommendation="include",
            lang_tags=["bash"],
            platform_tags=["aws"],
            issue_number=42,
        )
        reg.save()
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "sources", "skill-registry.json")


class Registry:
    """Skill evaluation registry (single-writer, not thread-safe).

    Uses an atomic file-replace on save (write to ``*.tmp`` then ``os.replace``)
    which is safe for a single concurrent writer. Do not use from multiple
    threads or overlapping processes without external file-locking.
    """

    def __init__(self, path: str = _REGISTRY_PATH) -> None:
        self.path = os.path.realpath(path)
        self._data: Dict[str, Any] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.path) as f:
                data = json.load(f)
            if "marketplaces" not in data:
                data["marketplaces"] = {}
            return data
        except (OSError, json.JSONDecodeError):
            return {
                "_schema_version": "1",
                "_description": (
                    "Tracks evaluated skill/plugin resources to avoid redundant re-evaluation. "
                    "Hierarchy: marketplaces[source_id][plugin_ref][skill_ref]."
                ),
                "_hierarchy": "marketplaces[source_id][plugin_ref][skill_ref]",
                "marketplaces": {},
            }

    def save(self) -> None:
        """Persist the registry to disk (atomic write)."""
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, self.path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def needs_evaluation(
        self,
        source: str,
        plugin_ref: str,
        skill_ref: str,
        sha: str,
    ) -> bool:
        """Return True if this skill requires (re-)evaluation.

        Returns False when the skill has already been evaluated with the
        **same SHA**, meaning its content has not changed since last time.
        Returns True when:
        - The skill has never been evaluated, OR
        - The stored SHA differs from the current SHA (content changed).
        """
        entry = self._get_entry(source, plugin_ref, skill_ref)
        if entry is None:
            return True
        return entry.get("sha", "") != sha

    def get_entry(
        self,
        source: str,
        plugin_ref: str,
        skill_ref: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the stored entry for a skill, or None if not found."""
        return self._get_entry(source, plugin_ref, skill_ref)

    def mark_evaluated(
        self,
        source: str,
        plugin_ref: str,
        skill_ref: str,
        sha: str,
        expertise: str,
        score: Optional[Dict[str, Any]] = None,
        recommendation: str = "include",
        lang_tags: Optional[List[str]] = None,
        platform_tags: Optional[List[str]] = None,
        issue_number: Optional[int] = None,
        notes: str = "",
    ) -> None:
        """Record that a skill has been evaluated."""
        mp = self._data.setdefault("marketplaces", {})
        plugins = mp.setdefault(source, {})
        skills = plugins.setdefault(plugin_ref, {})
        skills[skill_ref] = {
            "sha": sha,
            "last_evaluated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expertise": expertise,
            "lang_tags": sorted(set(lang_tags or [])),
            "platform_tags": sorted(set(platform_tags or [])),
            "score": score or {},
            "recommendation": recommendation,
            "issue_number": issue_number,
            "notes": notes,
        }

    def list_evaluated(
        self,
        expertise: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return all evaluated entries, optionally filtered by expertise."""
        out = []
        for source, plugins in self._data.get("marketplaces", {}).items():
            for plugin_ref, skills in plugins.items():
                for skill_ref, entry in skills.items():
                    if expertise and entry.get("expertise") != expertise:
                        continue
                    out.append({
                        "source": source,
                        "plugin_ref": plugin_ref,
                        "skill_ref": skill_ref,
                        **entry,
                    })
        return out

    def stats(self, expertise: Optional[str] = None) -> Dict[str, Any]:
        """Return summary statistics for the registry."""
        entries = self.list_evaluated(expertise)
        recommendations: Dict[str, int] = {}
        sources: Dict[str, int] = {}
        for e in entries:
            rec = e.get("recommendation", "unknown")
            recommendations[rec] = recommendations.get(rec, 0) + 1
            src = e.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        return {
            "total": len(entries),
            "by_recommendation": recommendations,
            "by_source": sources,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_entry(
        self,
        source: str,
        plugin_ref: str,
        skill_ref: str,
    ) -> Optional[Dict[str, Any]]:
        return (
            self._data
            .get("marketplaces", {})
            .get(source, {})
            .get(plugin_ref, {})
            .get(skill_ref)
        )


# ---------------------------------------------------------------------------
# Standalone utilities
# ---------------------------------------------------------------------------

def content_sha(content: str) -> str:
    """Return a SHA-256 hex digest of UTF-8 encoded content (truncated to 40 chars)."""
    return hashlib.sha256(content.encode()).hexdigest()[:40]


def blob_sha(content: str) -> str:
    """Return a content hash for the given content string.

    Uses SHA-256 (truncated to 40 chars) for consistency with ``content_sha``
    and to avoid the SHA-1 collision vulnerability.
    """
    encoded = content.encode()
    return hashlib.sha256(encoded).hexdigest()[:40]


# Known platform sub-prefixes for correct label naming.
_CSP_PLATFORMS = {
    "aws", "azure", "gcp", "oci", "alicloud", "digitalocean", "hetzner", "vsphere",
}
_CI_PLATFORMS = {
    "github-actions", "azure-devops", "gitlab-ci", "jenkins",
    "circleci", "teamcity", "bitbucket",
}
_SAAS_PLATFORMS = {
    "terraform-cloud", "hcp-vault", "hcp-consul", "hcp-boundary",
    "datadog", "pagerduty", "grafana-cloud", "newrelic", "splunk",
    "snyk", "sonarcloud", "jira", "confluent", "cloudflare", "fastly",
}


def platform_label(tag: str) -> str:
    """Return the correct full GitHub label name for a platform tag.

    Examples::

        platform_label("aws")             → "platform/csp/aws"
        platform_label("github-actions")  → "platform/ci/github-actions"
        platform_label("terraform-cloud") → "platform/saas/terraform-cloud"
        platform_label("custom")          → "platform/custom"
    """
    t = tag.lower()
    if t in _CSP_PLATFORMS:
        return f"platform/csp/{t}"
    if t in _CI_PLATFORMS:
        return f"platform/ci/{t}"
    if t in _SAAS_PLATFORMS:
        return f"platform/saas/{t}"
    return f"platform/{t}"


def parse_tags(raw: str) -> set:
    """Parse a comma-separated tag string into a normalised lowercase set.

    Shared utility used by discover.py, evaluate.py, and compose.py to
    ensure consistent tag normalisation across all scripts.
    """
    if not raw:
        return set()
    return {t.strip().lower() for t in raw.split(",") if t.strip()}


def extract_platform_tags_from_labels(labels: List[str]) -> List[str]:
    """Extract bare platform tags from a list of GitHub label names.

    Strips ``platform/``, ``platform/csp/``, ``platform/ci/``, and
    ``platform/saas/`` prefixes, returning the raw tag values.

    Example::

        extract_platform_tags_from_labels(["platform/csp/aws", "platform/ci/github-actions"])
        # → ["aws", "github-actions"]
    """
    import re
    tags = []
    for lbl in labels:
        m = re.match(r"^platform/(?:csp/|ci/|saas/)?(.+)$", lbl)
        if m:
            tags.append(m.group(1))
    return tags


# ---------------------------------------------------------------------------
# CLI for inspection / debugging
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect the veiled-market skill registry")
    sub = parser.add_subparsers(dest="cmd")

    stats_p = sub.add_parser("stats", help="Print registry statistics")
    stats_p.add_argument("--expertise", default=None)

    list_p = sub.add_parser("list", help="List all evaluated entries")
    list_p.add_argument("--expertise", default=None)

    check_p = sub.add_parser("check", help="Check if a skill needs evaluation")
    check_p.add_argument("source")
    check_p.add_argument("plugin_ref")
    check_p.add_argument("skill_ref")
    check_p.add_argument("sha")

    args = parser.parse_args()
    reg = Registry()

    if args.cmd == "stats":
        s = reg.stats(args.expertise)
        print(json.dumps(s, indent=2))
    elif args.cmd == "list":
        entries = reg.list_evaluated(args.expertise)
        print(json.dumps(entries, indent=2))
    elif args.cmd == "check":
        needs = reg.needs_evaluation(args.source, args.plugin_ref, args.skill_ref, args.sha)
        print("needs_evaluation:", needs)
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
