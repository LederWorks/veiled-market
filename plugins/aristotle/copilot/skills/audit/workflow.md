---
name: aristotle-audit
description: 'Aggregate plugin health across all (or one) veiled-market plugins by spawning the health-checker agent, then surface cross-plugin violations and per-plugin findings.'
---

# Audit Workflow

Run a lightweight compliance sweep across plugins and aggregate findings.

## Step 1 — Load rules

Read `docs/MARKETPLACE.md` — pay particular attention to Rules 9, 17, and 18 (cross-plugin
uniqueness and consistency requirements).

## Step 2 — Determine scope

Arguments passed: `$ARGUMENTS`

- **Plugin name given:** audit only that plugin.
- **No name given:** read `sources/plugins.json` and audit every listed plugin.

## Step 3 — Spawn health-checker per plugin

For each plugin in scope, invoke the **health-checker** agent with:
- `$PLUGIN_NAME` = plugin name
- `$MARKETPLACE_ROOT` = absolute path to the veiled-market root

Collect the structured JSON response from each agent call.

## Step 4 — Aggregate findings

From all collected responses:

**Cross-plugin violations (Rules 9/17/18):**
Identify cases where identical content (descriptions, skill names, agent names) appears in 2+
plugins. List each occurrence with the plugins involved.

**Per-plugin summary:**
| Plugin | Version | Built | 🔴 | 🟡 | 🔵 | Issues |
|--------|---------|-------|----|----|----|----|

Note: This audit runs a Socrates-style analysis at aggregate/lightweight level.
For full per-plugin Socratic dialogue run `/probe <plugin>`.

## Step 5 — Output

Print the aggregate table followed by any cross-plugin issues found.

## Step 6 — Handoff

For each plugin with findings, suggest: "Triage with `/steward triage <plugin>`"
