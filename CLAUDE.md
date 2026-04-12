# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repo is

AI-curated plugin marketplace (`LederWorks/veiled-market`) that publishes dual-compatible plugins for both **GitHub Copilot CLI** and **Claude Code**. Plugins are hand-authored using the **commons build system** and published as dual-compatible packages.

---

## Plugin Roadmap

| Plugin | Command | Role | Status | Skills |
|--------|---------|------|--------|--------|
| `atlas` | `/anchor` | Project / workspace setup | ✅ Built | init, update, validate |
| `daedalus` | `/forge` | Plugin creation / scaffolding / remediation | ✅ Built | create, update, build, remediate |
| `socrates` | `/probe` | Plugin validation / compliance audit | ✅ Built | probe |
| `aristotle` | `/steward` | Plugin management / lifecycle orchestration | ✅ Built | triage, bump, audit, inventory, review |
| `zeno` | `/bisect` | Terraform code review | 🔲 Planned | — |

---

## Plugin Lifecycle

The three philosopher plugins form a management cycle:

```
/forge (create|update) → /forge build → /probe → /steward triage → /forge remediate → /forge build → /probe → /steward bump
```

See `docs/PLUGIN-LIFECYCLE.md` for the authoritative spec including:
- `commons/` layout and 9 resource types
- Socrates TODO schema (with fix-type field)
- Aristotle triage protocol
- Inter-plugin handoff callouts
- Build conventions and Python scripts reference

---

## Two ways to publish a plugin

### 1. Commons build (hand-authored)

Author source in `plugins/<name>/commons/`; the build script generates platform-specific outputs:

```bash
python3 scripts/build-platforms.py --plugin <name> [--dry-run]
```

Output layout:
```
plugins/<name>/
├── commons/          ← Edit this — source of truth
│   ├── plugin.base.json
│   ├── hooks.json
│   ├── commands/<name>.md
│   ├── skills/<skill>/SKILL.md
│   ├── agents/<agent>.md
│   ├── references/
│   │   ├── shared-steps.md
│   │   ├── managed-files.md
│   │   └── stubs/       ← Jinja2 instruction stubs
│   └── templates/       ← Jinja2 project file templates
├── claude/           ← AUTO-GENERATED — never hand-edit
└── copilot/          ← AUTO-GENERATED — never hand-edit
```

Then register and publish:
```bash
# Add entry with platform_sources to sources/plugins.json, then:
python3 scripts/finalize.py --step regen
```

---

## Running scripts locally

```bash
# Commons build
python3 scripts/build-platforms.py --plugin <name> [--dry-run]

# Scaffold a new commons/ directory tree
python3 scripts/scaffold_plugin.py --name <name> --description "..." --version 0.1.0 --command <verb> --skills <s1>[,<s2>,...] --author "..."

# Validate commons/ structure before building
python3 scripts/validate_commons.py --plugin <name>

# Semver bump + propagate to all versioned files + regen manifests
python3 scripts/sync_versions.py --plugin <name> --bump patch|minor|major

# Regenerate both marketplace.json files from sources/plugins.json
python3 scripts/finalize.py --step regen
```

### Commons scripts quick-reference

| Script | Purpose |
|--------|---------|
| `scripts/build-platforms.py` | `commons/` → `claude/` + `copilot/` |
| `scripts/finalize.py` | Regenerate both `marketplace.json` files |
| `scripts/scaffold_plugin.py` | Scaffold a new `commons/` directory tree |
| `scripts/validate_commons.py` | Structural validation of `commons/` |
| `scripts/sync_versions.py` | Semver bump + propagate to all versioned files |

---

## Key files

| File | Purpose |
|------|---------|
| `sources/plugins.json` | **Single source of truth** for all plugin metadata; feeds manifest generation |
| `schemas/plugins.shema.json` | Validates `sources/plugins.json` — **typo is load-bearing, never rename** |
| `schemas/plugin.base.schema.json` | Validates `plugins/*/commons/plugin.base.json` |
| `drafts/` | AI-managed WIP — do not edit manually |
| `docs/arch-veiled-market.md` | Full architecture reference |
| `docs/PLUGIN-LIFECYCLE.md` | Authoritative spec for the Daedalus → Socrates → Aristotle management cycle |

**Shared reference layer:** Skills reference `docs/MARKETPLACE.md` and `docs/PLUGIN-LIFECYCLE.md` by direct file path — no duplication, no drift.

**Never hand-edit these auto-generated files:**
- `.github/plugin/marketplace.json` — Copilot CLI manifest
- `.claude-plugin/marketplace.json` — Claude Code manifest
- `plugins/*/claude/` and `plugins/*/copilot/` — commons build outputs

---

## Commons build transforms

| `commons/` file | `claude/` output | `copilot/` output |
|---|---|---|
| `skills/<n>/SKILL.md` | `skills/<n>/SKILL.md` | `skills/<n>/workflow.md` (`user-invocable` stripped) |
| `agents/<n>.md` | `agents/<n>.md` | `agents/<n>.agent.md` |
| `hooks.json` | verbatim | adds `"version": 1` |
| `references/`, `templates/` | verbatim | verbatim |

---

## Atlas conventions (workspace setup plugin)

Atlas manages these files in user workspaces:
- **`.config/atlas.json`** — atlas state store (IDEs, platforms, languages, git mode). All plugin configs go in `.config/` — never create a plugin-named folder at root.
- **`CLAUDE.md`** — Claude Code project context (auto-section: `<!-- ATLAS:START -->…<!-- ATLAS:END -->`)
- **`.github/copilot-instructions.md`** — Copilot CLI context (same markers)
- Instruction stubs → `.github/instructions/*.instructions.md`

