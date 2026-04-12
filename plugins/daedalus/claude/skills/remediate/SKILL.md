---
name: daedalus-remediate
description: 'Read a Socrates TODO file and apply all auto-fixable findings in priority order.
  Edits commons/ files, marks fixed items, then rebuilds. Trigger on: "apply fixes",
  "remediate findings", "fix socrates findings", "apply auto-fixes".'
user-invocable: false
---

# Remediate Workflow

Read a Socrates TODO file and apply every auto-fixable finding.
Always edit `commons/` only — never `claude/` or `copilot/`.

## Step 1 — Locate the TODO file

From `$ARGUMENTS`, extract the plugin name. Locate the most recent Socrates TODO file:

```
.todos/socrates/<plugin-name>-YYYYMMDD.md
```

If multiple files exist for the plugin, use the one with the most recent date.
If no file is found, tell the user and stop.

## Step 2 — Read the fix-type schema

Read `docs/PLUGIN-LIFECYCLE.md` §5 — understand all `fix-type` values:

| fix-type | Meaning | Action |
|---|---|---|
| `edit-content` | Edit file body | Apply |
| `edit-structure` | Rename, move, restructure | Apply |
| `add-file` | Required file is missing | Apply |
| `delete-file` | File should not exist | Apply |
| `config-change` | Edit JSON/YAML config | Apply |
| `manual` | Requires human judgment | Skip |

## Step 3 — Parse unchecked findings

Collect all lines matching `- [ ]` that have a `fix-type` field. Ignore `- [x]` (already applied).

Exclude findings where `fix-type: manual` — count them separately.

## Step 4 — Sort by priority

Apply findings in this order:

1. 🔴 Rule Violations first
2. 🟡 Anti-patterns second
3. 🔵 Improvements last

## Step 5 — Apply each finding

For each finding (in priority order):

1. Identify the target file from the **File:** field
2. Apply the fix described in the **Fix:** field to the file in `commons/`
3. If the fix succeeds: mark the finding as `- [x]` in the TODO file
4. If the fix fails: leave as `- [ ]` and append ` ← FAILED: <reason>` to that line

Continue with the next finding regardless of failure.

## Step 6 — Rebuild

After all findings are processed, run:

```bash
python3 scripts/build-platforms.py --plugin <name>
```

Check the exit code. If non-zero, show the error.

## Step 7 — Report

Show a summary:

```
Remediation complete: <plugin-name>

Applied:  N findings
Failed:   N findings (see TODO file for details)
Skipped:  N findings (fix-type: manual — requires human review)
```

List any failed findings with their reasons.

Then say:

> **Next:** Re-audit with `/probe <plugin-name>`
