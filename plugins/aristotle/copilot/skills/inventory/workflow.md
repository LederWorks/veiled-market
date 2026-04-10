---
name: aristotle-inventory
description: 'Read sources/plugins.json and display a dashboard table of every plugin: version, build status, last Socrates probe date, and open finding counts by severity.'
---

# Inventory Workflow

Produce a dashboard of all registered veiled-market plugins.

## Step 1 — Load plugin registry

Read `sources/plugins.json`. Collect every entry's name.

## Step 2 — Gather per-plugin data

For each plugin in the registry:

| Data point | Source |
|------------|--------|
| Name, version, description | `plugins/<name>/commons/plugin.base.json` |
| `claude/` built? | Check `plugins/<name>/claude/` exists and is non-empty |
| `copilot/` built? | Check `plugins/<name>/copilot/` exists and is non-empty |
| Last probed date | Most recent `.todos/socrates/<name>-YYYYMMDD.md` filename date |
| 🔴 / 🟡 / 🔵 counts | Count severity markers in that TODO file (if present) |

Built status = ✅ if both `claude/` and `copilot/` exist, else ❌.

## Step 3 — Output dashboard

```
## Plugin Inventory — veiled-market

| Plugin | Version | Built | Last Probed | 🔴 | 🟡 | 🔵 | Action |
|--------|---------|-------|-------------|----|----|----|----|
| atlas | 1.0.0 | ✅ | 2026-04-10 | 0 | 2 | 3 | /steward triage atlas |
| daedalus | 1.0.0 | ✅ | — | — | — | — | /probe daedalus |
```

Fill each row from data gathered in Step 2. Use `—` for unknown/missing values.
Action column: `/steward triage <name>` if TODO file present, else `/probe <name>`.

## Step 4 — Summary

Below the table print:
- Total: N plugins, N built, N never probed
- Recommended next action (e.g., "Run `/probe <name>` for all never-probed plugins")
