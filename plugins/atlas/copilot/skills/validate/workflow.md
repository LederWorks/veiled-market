---
name: atlas-validate
description: 'Health check for atlas-managed files: verify presence, check ATLAS markers, detect drift, and write a dated TODO report.'
---

# Validate Workflow

Perform a full health check across all atlas-managed files and write a structured, dated TODO report. This skill is read-only except for the TODO file it writes.

If called with an `[owner/repo]` argument, use `mcp__github__*` tools to read files from the remote repository; write the TODO report locally (not to remote).

## Shared Prerequisites

Load `../../references/shared-steps.md` and execute these anchors in order before the skill-specific steps below:

1. **[find-config]** — load `.config/atlas.json`. If not found, record a 🔴 critical issue (`[MISSING]` — atlas not initialised). Continue validation even without config, using an empty default config.
2. **[analyse]** — re-scan the tech stack (needed to detect language/tool drift against what `[find-config]` recorded).

For the managed files reference and severity codes, see `../../references/managed-files.md`.

## Step 1 — Validate managed files

Execute **[validate-managed]** from `../../references/shared-steps.md`.

For each managed file applicable to the current config, run these checks concurrently:

| Check | Healthy | Issue |
|---|---|---|
| **Presence** | File exists on disk | Missing required file → 🔴 `[MISSING]`; missing optional file given current config → 🟡 `[OPTIONAL_MISSING]` |
| **Markers** | `<!-- ATLAS:START -->` and `<!-- ATLAS:END -->` present in AI context files | Absent → 🟡 `[NO_MARKER]` |
| **Content drift** | Auto-generated section matches what atlas would write today | Significant difference → 🟡 `[DRIFT]` (include a brief summary of what changed) |
| **Config consistency** | Present files match `enabled_ides` and `enabled_platforms` in `.config/atlas.json` | Mismatch (e.g., `.vscode/mcp.json` exists but `vscode` not in `enabled_ides`) → 🟡 `[CONFIG_MISMATCH]` |
| **Stub completeness** | All stubs for detected languages present in `.github/instructions/` | Missing stub → 🟡 `[MISSING_STUB]`; stub present but marketplace version newer → 🟡 `[STALE_STUB]` |

Collect all issues into a flat list. Each issue entry must include:
- Severity (🔴 / 🟡 / 🟢)
- Issue code (e.g., `[MISSING]`, `[DRIFT]`)
- File path affected
- One-line description and remediation hint

## Step 2 — Display results

Print a structured report grouped by severity:

```
🔴 Critical (N issues)
  - [MISSING] .config/atlas.json — atlas not initialised; run /atlas init

🟡 Warnings (N issues)
  - [DRIFT] CLAUDE.md — auto-generated section is stale; run /atlas update
  - [MISSING_STUB] .github/instructions/go.instructions.md — Go detected, stub absent

🟢 Healthy (N checks passed)
  - [HEALTHY] .github/copilot-instructions.md
  - [HEALTHY] .vscode/extensions.json
```

If no issues are found across all checks, print: `🟢 All managed files are healthy`.

## Step 3 — Write TODO report

Write results to `.todos/atlas/validate-YYYYMMDD.md` (ISO date, e.g. `validate-20260319.md`):

```markdown
<!-- source: atlas-validate -->
<!-- generated: <ISO 8601 timestamp> -->
<!-- scope: <absolute project path> -->

## Atlas Validation TODO — <project name or repo path>

### 🔴 Critical (blocking — run /atlas init or resolve before update proceeds)
- [ ] [MISSING] `.config/atlas.json` — atlas not initialised; run `/atlas init`

### 🟡 Warnings (non-blocking — /atlas update applies these automatically)
- [ ] [DRIFT] `CLAUDE.md` — auto-generated section is stale; run `/atlas update`
- [ ] [MISSING_STUB] `.github/instructions/go.instructions.md` — Go detected, stub absent; run `/atlas update`

### 🟢 Healthy (no action needed)
- [x] [HEALTHY] `.github/copilot-instructions.md` — present, markers found, content current
- [x] [HEALTHY] `.vscode/extensions.json` — present and valid JSON

### Suggested fixes
- For drift or missing stubs: run `/atlas update`
- For missing setup: run `/atlas init`
```

Create `.todos/atlas/` if it does not exist.

## Step 4 — Exit message

Print the path to the TODO file and a one-line summary:

```
Wrote: .todos/atlas/validate-20260319.md
Result: 1 critical, 2 warnings, 4 healthy
```

---

See **Guidelines** in `../../references/shared-steps.md`.
