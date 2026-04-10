# Plugin Lifecycle — Authoritative Reference

This document is the shared specification for the Daedalus → Socrates → Aristotle plugin
management cycle. All three plugins reference this document directly. It defines the
`commons/` layout, build conventions, TODO schema, and inter-plugin handoff protocol.

---

## 1. The Plugin Management Cycle

```
  /forge create       ──────────────────────────────────────────┐
  /forge update       → build → /probe → /steward triage →     │
  /forge remediate ←──────────────────────────────────────────  │
        ↑                                                        │
        └─── /steward bump → (done) ←── /probe passes ─────────┘
```

### The three philosophers

| Plugin | Command | Role | Verb meaning |
|--------|---------|------|-------------|
| **daedalus** | `/forge` | Creates and executes all plugin work | To forge: craft, shape, build |
| **socrates** | `/probe` | Audits compliance, documents findings | To probe: question, examine, test |
| **aristotle** | `/steward` | Orchestrates lifecycle, manages versions | To steward: guard, manage, tend |

### Handoff protocol (explicit callouts)

Every terminal step in each plugin must surface the next action:

| Step completes | Plugin says |
|---------------|-------------|
| `/forge build` | "Validate with `/probe <plugin>`" |
| `/forge remediate` (+ build) | "Re-audit with `/probe <plugin>`" |
| `/probe` verdict written | "Triage fixes with `/steward triage <plugin>`" |
| `/steward triage` | "Apply auto-fixes with `/forge remediate <plugin>`" |
| `/steward audit` | "Triage per plugin with `/steward triage <plugin>`" |
| `/steward bump` | "Commit: `git add -A && git commit -m 'chore: bump <plugin> to vX.Y.Z'`" |

---

## 2. The `commons/` Layout

Every plugin's `commons/` directory is the single source of truth. Never edit `claude/` or
`copilot/` directly — they are generated outputs.

```
plugins/<name>/
├── commons/                            ← EDIT HERE ONLY
│   ├── plugin.base.json                ← shared metadata + skill visibility markers
│   ├── hooks.json                      ← hook configuration (required even if empty)
│   ├── commands/
│   │   └── <verb>.md                   ← entry command (name: <philosopher-verb>)
│   ├── skills/
│   │   └── <skill-name>/
│   │       └── SKILL.md               ← one skill per concern
│   ├── agents/
│   │   └── <name>.md                  ← workflow or domain expert agents
│   ├── references/
│   │   └── <name>.md                  ← shared step anchors and reference tables
│   ├── templates/
│   │   └── <path>/<name>.j2           ← Jinja2 file-generation templates
│   └── scripts/                        ← plugin-local scripts (use scripts/ if shared)
├── claude/                             ← GENERATED — do not edit
└── copilot/                            ← GENERATED — do not edit
```

### `plugin.base.json` schema

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "...",
  "author": { "name": "..." },
  "license": "MIT",
  "keywords": ["..."],
  "tags": ["..."],
  "skills": [
    { "path": "skills/<name>", "user-invocable": true },
    { "path": "skills/<hidden>", "user-invocable": false }
  ],
  "agents": [
    { "path": "agents/<name>.md" }
  ],
  "hooks": "hooks.json"
}
```

### `hooks.json` minimum (required even if no hooks)

```json
{"version": 1, "hooks": {}}
```

---

## 3. The 9 Resource Types

All resources live inside `commons/`. The build script transforms them per platform.

| Type | `commons/` path | Claude output | Copilot output |
|------|----------------|--------------|---------------|
| `plugin` | `plugin.base.json` | `plugin.json` | `plugin.json` |
| `skill` (user-invocable) | `skills/<n>/SKILL.md` | `skills/<n>/SKILL.md` | `skills/<n>/SKILL.md` |
| `skill` (hidden) | `skills/<n>/SKILL.md` + `user-invocable: false` | `skills/<n>/SKILL.md` | `skills/<n>/workflow.md` |
| `agent` | `agents/<n>.md` | `agents/<n>.md` | `agents/<n>.agent.md` |
| `command` | `commands/<verb>.md` | `commands/<verb>.md` | `commands/<verb>.md` |
| `hook` | `hooks.json` + script files | verbatim | adds `"version": 1` |
| `template` | `templates/<path>/<n>.j2` | verbatim copy | verbatim copy |
| `reference` | `references/<n>.md` | verbatim copy | verbatim copy |
| `script` | `scripts/<n>.py` (plugin-local) or `../../scripts/<n>.py` (shared) | verbatim | verbatim |
| `mcp` | `.mcp.json` | verbatim | verbatim |

### When to use shared `scripts/` vs `commons/scripts/`

- Script used by **1 plugin only** → `commons/scripts/`
- Script used by **2+ plugins** → `veiled-market/scripts/` (shared)
- Rule: `marketplace-patterns.md` Rule 10a applies here

---

## 4. Build Conventions

### Running the build

```bash
# Build one plugin
python3 scripts/build-platforms.py --plugin <name>

# Build all plugins
python3 scripts/build-platforms.py --all

# Dry run (see what would change)
python3 scripts/build-platforms.py --plugin <name> --dry-run
```

### After every build, update the registry

```bash
python3 scripts/finalize.py --step regen
```

This regenerates both `veiled-market/.github/plugin/marketplace.json` and
`veiled-market/.claude-plugin/marketplace.json` from `sources/plugins.json`.

### Scaffold a new plugin (new in this cycle)

```bash
python3 scripts/scaffold_plugin.py \
  --name <plugin-name> \
  --description "..." \
  --version 0.1.0 \
  --command <verb> \
  --skills <skill1>[,<skill2>,...] \
  --author "..."
```

Creates the full `commons/` directory tree. Then edit the generated SKILL.md stubs.

### Structural validation before building

```bash
python3 scripts/validate_commons.py --plugin <name>
```

Checks: required files present, `plugin.base.json` schema valid, frontmatter present in all
resources, `hooks.json` wired correctly, no orphaned scripts.

### Version bump (propagates everywhere)

```bash
python3 scripts/sync_versions.py --plugin <name> --bump patch|minor|major
```

Updates: `commons/plugin.base.json`, `claude/plugin.json`, `copilot/plugin.json`, and both
`marketplace.json` files. Reports: `<plugin>: 1.0.0 → 1.0.1`.

---

## 5. Socrates TODO Schema

Socrates writes finding files to `.todos/socrates/`. These files are the handoff artifact
between Socrates and Aristotle.

### File naming

```
.todos/socrates/<plugin-name>-YYYYMMDD.md
```

### File structure

```markdown
<!-- source: socrates -->
<!-- generated: <ISO 8601 timestamp> -->
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
**fix-type:** edit-content

---

### 🟡 Anti-patterns

#### <Finding title>
**Anti-pattern:** AP<N> — <name>
**File:** `<path>`
**Evidence:** <what was observed>
**Fix:** <concrete action>
**fix-type:** edit-structure

---

### 🔵 Improvements

#### <Finding title>
**File:** `<path>`
**Observation:** <what could be better>
**Suggestion:** <what to do>
**fix-type:** edit-content

---

### 🟢 Passed Checks
- <check>: OK
- ...

---
> Next: `/steward triage <plugin-name>`
```

### `fix-type` values

| Value | Meaning | Routed to |
|-------|---------|-----------|
| `edit-content` | Edit file body (instructions, descriptions, steps) | Daedalus auto-fix |
| `edit-structure` | Rename, move, or restructure files | Daedalus auto-fix |
| `add-file` | A required file is missing | Daedalus auto-fix |
| `delete-file` | File should not exist or is orphaned | Daedalus auto-fix |
| `config-change` | Edit JSON/YAML config (hooks.json, plugin.base.json) | Daedalus auto-fix |
| `manual` | Requires human design judgment | Human action, not routed |

---

## 6. Aristotle Triage Protocol

When Aristotle reads a Socrates TODO file, it:

1. Parses all unchecked `- [ ]` findings
2. Groups by `fix-type`:
   - All non-`manual` → **dispatch list** (can be given to `/forge remediate`)
   - `manual` → **human list** (documented separately, cannot be automated)
3. Prioritizes: 🔴 before 🟡 before 🔵
4. Outputs a dispatch plan:

```
## Aristotle Triage: <plugin-name>

Auto-fixable (N items) → Run `/forge remediate <plugin-name>`
  🔴 [edit-content] ...
  🟡 [add-file] ...
  🔵 [edit-content] ...

Manual review required (N items):
  🔴 [manual] <title> — <why human judgment needed>
  ...

Next: `/forge remediate <plugin-name>`
```

---

## 7. Inter-Plugin Reference Convention

Plugins reference this document and `docs/MARKETPLACE.md` by direct file path:

```
Read `docs/PLUGIN-LIFECYCLE.md` — it is the authoritative spec for this repo.
Read `docs/MARKETPLACE.md` §3 — the 22 rules you will apply.
```

No symlinks. No build-time copying. Skills instruct the AI to read these paths at runtime.

---

## 8. Plugin Registry Management

### `sources/plugins.json` entry format

```json
{
  "name": "<plugin-name>",
  "description": "...",
  "version": "x.y.z",
  "source": "./plugins/<name>/copilot",
  "platform_sources": {
    "claude": "./plugins/<name>/claude",
    "copilot": "./plugins/<name>/copilot"
  }
}
```

`platform_sources` is stripped from both `marketplace.json` outputs by `finalize.py`.
The `source` field in the manifest uses the platform-specific value.

### Adding a new plugin

1. `scripts/scaffold_plugin.py` generates `commons/`
2. `scripts/build-platforms.py` generates `claude/` and `copilot/`
3. Add entry to `sources/plugins.json` with `platform_sources`
4. `scripts/finalize.py --step regen` updates both marketplace manifests

### Warning: load-bearing typo

`$schema` in `sources/plugins.json` references `"./schemas/plugins.shema.json"` — the
misspelling (`shema` not `schema`) is frozen. Do not correct it without updating
`AGENTS.md` and `ci.yml` atomically.

---

## 9. Philosopher Command Verbs

| Plugin | Command | Verb meaning |
|--------|---------|-------------|
| `daedalus` | `/forge` | Forge: to craft, shape, build from raw material |
| `socrates` | `/probe` | Probe: to question, examine, test assumptions |
| `aristotle` | `/steward` | Steward: to manage, guard, tend to health |
| `atlas` | `/anchor` | Anchor: to ground, stabilize, set the base |
| `zeno` | `/bisect` | Bisect: to narrow down, step by step |

Commands are named after verbs, not plugin names — for memorability and UX.
