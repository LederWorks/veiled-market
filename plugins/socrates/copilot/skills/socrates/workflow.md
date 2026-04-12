---
name: socrates
description: Validates a plugin against marketplace-patterns rules using Socratic dialogue. Spawns a scanner, asks targeted questions only where design intent is ambiguous, then writes a structured TODO file and inline summary. Use when auditing any marketplace plugin for rule compliance, structural issues, or anti-patterns. Trigger on: /socrates, "validate this plugin", "audit plugin", "check plugin rules".
---

# Socrates — Plugin Validator

Socrates validates plugins through dialogue, not decree. The scanner finds the facts.
You surface the intent. Together, you reach a verdict.

**The rule:** Ask questions only when the answer changes the classification. Never
interrogate the user about violations that are already clear from the evidence.

---

## Phase 1 — Scan

Parse the plugin identifier from the user's invocation. Accept either:
- A bare plugin name (e.g. `socrates`) → resolve to `plugins/<name>/commons/`
- A partial path (e.g. `plugins/socrates/`) → resolve to `plugins/<name>/commons/`
- A full path (e.g. `plugins/socrates/commons/`) → use as-is

If no identifier was given, ask for one.

Spawn the **scanner** agent:

```
Read agents/scanner.md in the Socrates skill directory and follow its instructions.
Plugin path: plugins/<name>/commons/
```

Wait for the scanner report before proceeding.

---

## Phase 2 — Socratic Dialogue

Work through the `AMBIGUOUS FINDINGS` section of the scanner report. For each item,
use the matching template from `references/dialogue-templates.md`. Group related
questions into one exchange when possible — don't ask one question per message if
three items share a theme.

If the scanner's `AMBIGUOUS FINDINGS` section is empty, skip Phase 2 entirely.

---

## Phase 3 — Verdict

Read `docs/MARKETPLACE.md` §3 (the 22 rules) and §7 (anti-patterns) now. These are the
authoritative sources for verdict decisions. Use `references/rules-compact.md` as a
quick-reference supplement for fast lookup only.

Combine:
- All `CLEAR VIOLATIONS` from the scanner report → classify directly (no dialogue)
- All ambiguous findings → classify based on the user's answers from Phase 2

Assign each finding one of:
- 🔴 `RULE_VIOLATION` — hard rule breach, must fix
- 🟡 `ANTI_PATTERN` — documented pattern violation, should fix
- 🔵 `IMPROVEMENT` — optional improvement
- 🟢 `OK` — check passed

---

## Phase 4 — Output

### Write the TODO file

Write to: `.todos/socrates/<plugin-name>-YYYYMMDD.md`

Use this exact structure:

```markdown
<!-- source: socrates -->
<!-- generated: <ISO timestamp> -->
<!-- scope: <plugin-name> -->
<!-- plugin-path: plugins/<name>/commons -->

# Socrates Validation: <plugin-name>

## Summary
| Severity | Count |
|---|---|
| 🔴 RULE_VIOLATION | N |
| 🟡 ANTI_PATTERN | N |
| 🔵 IMPROVEMENT | N |
| 🟢 OK | N |

## Findings

### 🔴 Rule Violations

#### <Finding title>
**Rule:** Rule N — <rule name>
**File:** `<path>` (line N)
**Evidence:** <what the scanner found>
**Fix:** <concrete action to resolve>
**fix-type:** <value>

---

### 🟡 Anti-patterns

#### <Finding title>
**Anti-pattern:** AP<N> — <name>
**File:** `<path>`
**Evidence:** <what was observed>
**Fix:** <concrete action>
**fix-type:** <value>

---

### 🔵 Improvements

#### <Finding title>
**File:** `<path>`
**Observation:** <what could be better>
**Suggestion:** <what to do>
**fix-type:** <value>

---

### 🟢 Passed Checks
- <check>: OK
- ...

---
> Next: `/steward triage <plugin-name>`
```

### `fix-type` assignment rules

| Value | When to use |
|---|---|
| `edit-content` | Line limit violations, description too long, wrong content in file body |
| `edit-structure` | File needs renaming or moving (e.g. `workflow.md` rename) |
| `add-file` | A required file is missing entirely |
| `delete-file` | Orphaned or prohibited file that should be removed |
| `config-change` | `hooks.json` or `plugin.base.json` needs editing |
| `manual` | Complex architectural decision (split a skill, extract to shared reference) |

### Show inline summary

After writing the file, show:

```
## Socrates — Validation Complete

Plugin: <plugin-name>
TODO file: .todos/socrates/<plugin-name>-YYYYMMDD.md

| 🔴 Violations | 🟡 Anti-patterns | 🔵 Improvements | 🟢 Passed |
|---|---|---|---|
| N | N | N | N |

**Top finding:** <the single most important issue, one sentence>
```

If there are zero violations and zero anti-patterns, add:
> This plugin is compliant with all checked marketplace-patterns rules.

> Next: `/steward triage <plugin-name>`
