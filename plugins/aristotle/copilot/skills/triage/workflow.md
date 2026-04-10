---
name: aristotle-triage
description: 'Read a Socrates TODO file, split findings into auto-fixable and manual groups, prioritise by severity, and output a dispatch plan for /forge remediate.'
---

# Triage Workflow

Parse a Socrates finding file and produce a prioritised dispatch plan for Daedalus.

## Step 1 — Load spec

Read `docs/PLUGIN-LIFECYCLE.md` §5 (TODO schema and fix-type values) and §6 (triage protocol
and output format).

## Step 2 — Locate TODO file

Arguments passed: `$ARGUMENTS` (first token = plugin name, if any).

- **Plugin name given:** look for `.todos/socrates/<plugin>-*.md`. If multiple files match,
  use the one with the most recent date in the filename (YYYYMMDD sort, descending).
- **No name given:** list all files in `.todos/socrates/` and ask the user which to triage.

## Step 3 — Parse findings

Scan the file for all unchecked items (`- [ ]`). For each finding extract:
- Severity emoji (🔴 / 🟡 / 🔵)
- Title
- `fix-type:` value

## Step 4 — Split by fix-type

| Group | fix-type values |
|-------|----------------|
| **Auto-fixable** | `edit-content`, `edit-structure`, `add-file`, `delete-file`, `config-change` |
| **Manual** | `manual` |

## Step 5 — Sort auto-fixable

Order within auto-fixable group: 🔴 first, then 🟡, then 🔵.

## Step 6 — Output triage report

```
## Aristotle Triage: <plugin-name>

Auto-fixable (N items) → Run `/forge remediate <plugin-name>`
  🔴 [edit-content] <title>
  🟡 [add-file] <title>
  🔵 [edit-content] <title>

Manual review required (N items):
  🔴 [manual] <title> — <why human judgment needed>
```

## Step 7 — Handoff

End with: "Apply auto-fixes with `/forge remediate <plugin-name>`"
