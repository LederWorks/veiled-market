# Design: Atlas + Apollo Release Plan
**Date:** 2026-04-10  
**Status:** Approved  
**Scope:** Full release of `atlas` (with scaffold) and `apollo` (merged trio) plugins, including trio deprecation and doc cleanup.

---

## Problem

The philosopher trio (daedalus/socrates/aristotle) has a distribution flaw: installed plugins only receive their `copilot/` or `claude/` subdirectory, so a user installing Daedalus does not get Socrates or Aristotle. Merging the trio into a single **Apollo** plugin solves this while keeping concerns separated from **Atlas** (workspace/project setup).

Additionally, Atlas is missing its `scaffold` capability (greenfield project creation) and has a `hooks.json` defect (missing `"version": 1`).

---

## Target Architecture

| Plugin | Command | Domain | Status |
|--------|---------|--------|--------|
| **Atlas** | `/anchor` | Workspace & project setup | Extend with scaffold |
| **Apollo** | `/forge`, `/probe`, `/steward` | Plugin lifecycle management | Create by merging trio |

Both use the `commons/` → `claude/` + `copilot/` build system.  
See `docs/implementation-plan.md` and `docs/plugin-inventory.md` for full file inventory.

---

## Release Definition

**Release-ready** means:
1. `commons/` content authored for both plugins
2. `build-platforms.py` run — `claude/` and `copilot/` outputs committed
3. `sources/plugins.json` updated with `platform_sources` entries for both
4. Both `marketplace.json` files regenerated and schema-valid
5. Trio plugins (daedalus/socrates/aristotle) deprecated — `commons/` replaced with deprecation notices
6. Docs updated to reflect Apollo as the current architecture

---

## Approach: Two Review Threads → Unified Plan → Parallel Tracks

### Phase 0: Parallel Review

Two agents run simultaneously:

**Doc Review Agent** — reads all 7 docs + CLAUDE.md + README.md. Checks for:
- Stale references to trio as the target architecture (PLUGIN-LIFECYCLE.md, arch-veiled-market.md)
- Old skill names in docs (create/update/build/remediate → forge/edit/assemble/fix etc.)
- Inconsistencies between `implementation-plan.md` and `plugin-inventory.md`
- MARKETPLACE.md rule violations in the plan (Rule 21: descriptions ≤60 words; Rule 2: commands ≤66 lines)
- Missing `render_template.py` tracking (listed as Tier-1 port but not yet in `veiled-market/scripts/`)

Produces: **Doc Findings Report**

**Engineering Review Agent** — audits the codebase. Checks:
- File delta: current `commons/` inventory vs `plugin-inventory.md` target state
- `build-platforms.py`: confirms missing copy logic for `scripts/`, `templates/`, `schemas/`
- Source file existence at porting locations (copilot monolith, plugin-dev)
- `sources/plugins.json` current entries vs required apollo entry
- Confirms `hooks.json` defect in atlas (missing `"version": 1`)

Produces: **Engineering Findings Report**

Findings merge into a corrected implementation checklist before any files are touched.

---

## Implementation Tracks

**Prerequisite (before both tracks):** Step 0a must complete first — it unblocks both build gates.

| Step | Action | Files |
|------|--------|-------|
| 0a | Extend `build-platforms.py` to copy `scripts/`, `templates/`, `schemas/` | 1 script edit |
| 0b | Port `render_template.py` to `veiled-market/scripts/` (Tier 1 — shared, not bundled) | 1 file |

Tracks A and B then run in parallel — they touch zero shared files. Track C gates on both.

### Track A — Atlas (independent)

| Step | Action | Files |
|------|--------|-------|
| 1a | Fix `hooks.json`: add `"version": 1` | 1 file |
| 1b | Add `scaffold` route to `commands/atlas.md` | 1 file edit |
| 1c | Create `skills/scaffold/SKILL.md` (≤200 lines, name: `atlas-scaffold`) | 1 file |
| 1d | Create `references/project-types.md` (~100 lines, 4 archetypes) | 1 file |
| 1e | Create 8 scaffold templates under `templates/scaffold/` | 8 files |
| 1f | Extend `templates/templates.json`, `references/managed-files.md`, `references/shared-steps.md` | 3 edits |
| 1g | Run `validate_commons.py --plugin atlas` + `build-platforms.py --plugin atlas` | build gate |

### Track B — Apollo (sequential within track)

**Phase 2 — Content Merge**

| Step | Action | Files |
|------|--------|-------|
| 2a | Create `apollo/commons/` directory tree + `plugin.base.json` | ~1 file |
| 2b | Create apollo skills from daedalus source (trio stays intact): create→forge, update→edit, build→assemble, remediate→fix; update frontmatter names to `apollo-*` | 4 files |
| 2c | Create apollo skill from socrates source: socrates→probe; update frontmatter name | 1 file |
| 2d | Create apollo skills from aristotle source: triage→classify, bump→increment, audit→survey, inventory→catalog, review→grade; update frontmatter names | 5 files |
| 2e | Create apollo agents from trio source (scaffolder, scanner, health-checker); update frontmatter names | 3 files |
| 2f | Create apollo references from trio source (resource-types, rules-compact, dialogue-templates, version-protocol) | 4 files |
| 2g | Create merged `references/shared-steps.md` (anchors from trio + copilot monolith pattern) | 1 file |
| 2h | Create commands: `forge.md`, `probe.md`, `steward.md` (adapted from trio, routes to apollo-* names) | 3 files |
| 2i | Create `hooks.json` with `"version": 1` and preToolUse guard wired | 1 file |

**Phase 3 — Tooling Port**

| Step | Action | Source |
|------|--------|--------|
| 3a | Port `run_eval.py`, `run_loop.py`, `improve_description.py` | `marketplace/plugins/copilot/scripts/` |
| 3b | Port + adapt `validate-agents.sh`, `validate-hooks-json.sh` | `claude-plugins-official/plugins/plugin-dev/skills/*/scripts/` |
| 3c | Create `guard-build-dirs.sh` + `guard-build-dirs.ps1` (NEW preToolUse hook scripts) | NEW |
| 3d | Port `hooks.schema.json`, `skill-frontmatter.schema.json`, `plugin.schema.json` | `marketplace/plugins/copilot/schemas/` |
| 3e | Port `templates/templates.json` + 9 resource `.j2` templates | `marketplace/plugins/copilot/templates/` |

**Phase 4 — Knowledge Skills + Agent**

| Step | Action | Source |
|------|--------|--------|
| 4a | Create `skills/author/SKILL.md` (≤150 lines, hook authoring knowledge) | plugin-dev `hook-development/` |
| 4b | Create `skills/integrate/SKILL.md` (≤150 lines, MCP integration knowledge) | plugin-dev `mcp-integration/` |
| 4c | Create `skills/configure/SKILL.md` (≤150 lines, plugin settings knowledge) | plugin-dev `plugin-settings/` |
| 4d | Create `agents/agent-creator.md` (≤150 lines) | plugin-dev `agents/agent-creator.md` |
| 4g | Run `validate_commons.py --plugin apollo` + `build-platforms.py --plugin apollo` | build gate |

### Track C — Closure (gates on A + B)

| Step | Action |
|------|--------|
| 5a | Replace daedalus/socrates/aristotle `commons/` with deprecation notices |
| 5b | Update `sources/plugins.json`: add `apollo` entry with `platform_sources`; update `atlas` entry if needed |
| 6a | Update `docs/PLUGIN-LIFECYCLE.md`: replace trio commands/skill names with Apollo equivalents |
| 6b | Update `docs/arch-veiled-market.md`: plugin table (trio → apollo) |
| 6c | Update `veiled-market/CLAUDE.md` plugin roadmap table |
| 6d | Run `finalize.py --step regen` — regenerate both `marketplace.json` files |
| 6e | Validate both `marketplace.json` files against schema |

---

## Acceptance Criteria

### Atlas release gate
- `validate_commons.py --plugin atlas` passes, zero errors
- `build-platforms.py --plugin atlas` completes without errors
- `atlas/commons/hooks.json` = `{"version": 1, "hooks": {}}`
- `atlas/commons/commands/atlas.md` routes scaffold / init / sync / validate
- `atlas/commons/skills/scaffold/SKILL.md` exists, ≤200 lines, name = `atlas-scaffold`
- `atlas/commons/references/project-types.md` exists with 4 archetypes
- All 8 scaffold templates exist under `templates/scaffold/`
- `templates/templates.json` includes scaffold-scope entries

### Apollo release gate
- `apollo/commons/` has 13 skills, 4 agents, 3 commands, 5 references, 7 scripts, 3 schemas, 11 templates
- All skill `name` frontmatter fields use `apollo-*` prefix
- `validate_commons.py --plugin apollo` passes, zero errors
- `build-platforms.py --plugin apollo` completes; `scripts/`, `templates/`, `schemas/` present in both `claude/` and `copilot/` outputs
- `hooks.json` has `"version": 1`; guard hook wired to `guard-build-dirs.sh` + `.ps1`

### Full release gate
- Trio `commons/` directories each contain only a deprecation notice (no functional files)
- `sources/plugins.json` contains `atlas` and `apollo` entries with valid `platform_sources`
- `.github/plugin/marketplace.json` and `.claude-plugin/marketplace.json` both valid against schema
- `docs/PLUGIN-LIFECYCLE.md` uses Apollo skill names and commands throughout
- `docs/arch-veiled-market.md` plugin table lists atlas + apollo (trio removed)
- `veiled-market/CLAUDE.md` roadmap reflects current plugin set

---

## Key Constraints

- `build-platforms.py` must be extended (Phase 0a) before Apollo can be built — Apollo is the first plugin to use `scripts/`, `templates/`, `schemas/`
- Knowledge skills (apollo-author, apollo-integrate, apollo-configure) must be ≤150 lines each — depth goes in `references/`, not inline
- All trio content moves to apollo with minimal changes — no refactoring during the merge
- `render_template.py` ports to `veiled-market/scripts/` (Tier 1, shared, step 0b) — NOT into apollo
- Trio plugins (daedalus/socrates/aristotle) are NOT touched until Phase 5 — Apollo is created independently in `plugins/apollo/commons/`
- Never hand-edit `claude/` or `copilot/` outputs — always edit `commons/` and rebuild
