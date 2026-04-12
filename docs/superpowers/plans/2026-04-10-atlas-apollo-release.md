# Atlas + Apollo Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release `atlas` (with scaffold capability) and `apollo` (merged daedalus+socrates+aristotle) to the veiled-market marketplace — fully built, marketplace-registered, with the trio deprecated.

**Architecture:** Two parallel review agents produce findings first; a build-system prerequisite runs next; then Atlas (Track A) and Apollo (Track B) build in parallel; Track C closes with trio deprecation and manifest regeneration.

**Tech Stack:** Python 3 stdlib (build/validate scripts), Jinja2 (templates, AI-rendered at runtime), Markdown+YAML (plugin files), Bash + PowerShell (hook scripts), JSON Schema (validation)

---

## Execution Order

```
Dispatch Group 0 (parallel): Task 1 (Doc Review) ‖ Task 2 (Engineering Review)
                  ↓
Dispatch Group 1 (sequential): Task 3 (build-platforms.py) → Task 4 (render_template.py)
                  ↓
Dispatch Group 2 (parallel): Tasks 5-11 (Track A: Atlas) ‖ Tasks 12-27 (Track B: Apollo)
                  ↓
Dispatch Group 3 (sequential): Tasks 28-31 (Track C: Closure)
```

**Key constraint:** Task 3 (build-platforms.py extension) must complete before build gates in Task 11 (Atlas) and Task 27 (Apollo).

---

## File Map

### New files — Atlas
| File | Purpose |
|------|---------|
| `plugins/atlas/commons/skills/scaffold/SKILL.md` | New procedural skill: greenfield project creation |
| `plugins/atlas/commons/references/project-types.md` | 4 project archetypes with directory layouts |
| `plugins/atlas/commons/templates/scaffold/pyproject.toml.j2` | Python project template |
| `plugins/atlas/commons/templates/scaffold/package.json.j2` | TypeScript/JS project template |
| `plugins/atlas/commons/templates/scaffold/go.mod.j2` | Go module template |
| `plugins/atlas/commons/templates/scaffold/Makefile.j2` | Generic build template |
| `plugins/atlas/commons/templates/scaffold/.editorconfig.j2` | Editor config template |
| `plugins/atlas/commons/templates/scaffold/CONTRIBUTING.md.j2` | Contribution guide template |
| `plugins/atlas/commons/templates/scaffold/ci/github-actions.yml.j2` | GitHub Actions CI template |
| `plugins/atlas/commons/templates/scaffold/ci/azure-pipelines.yml.j2` | Azure Pipelines CI template |

### Modified files — Atlas
| File | Change |
|------|--------|
| `plugins/atlas/commons/hooks.json` | Add `"version": 1` |
| `plugins/atlas/commons/commands/atlas.md` | Add scaffold route |
| `plugins/atlas/commons/templates/templates.json` | Add scaffold-scope entries |
| `plugins/atlas/commons/references/managed-files.md` | Add scaffold-managed file entries |
| `plugins/atlas/commons/references/shared-steps.md` | Add `[scaffold-structure]` anchor |

### New files — Apollo (entire plugin is new)
| File | Source |
|------|--------|
| `plugins/apollo/commons/plugin.base.json` | NEW |
| `plugins/apollo/commons/hooks.json` | NEW |
| `plugins/apollo/commons/commands/forge.md` | Adapted from daedalus.md |
| `plugins/apollo/commons/commands/probe.md` | Adapted from socrates.md |
| `plugins/apollo/commons/commands/steward.md` | Adapted from aristotle.md |
| `plugins/apollo/commons/skills/forge/SKILL.md` | From daedalus create/ (name→apollo-forge) |
| `plugins/apollo/commons/skills/edit/SKILL.md` | From daedalus update/ (name→apollo-edit) |
| `plugins/apollo/commons/skills/assemble/SKILL.md` | From daedalus build/ (name→apollo-assemble) |
| `plugins/apollo/commons/skills/fix/SKILL.md` | From daedalus remediate/ (name→apollo-fix) |
| `plugins/apollo/commons/skills/probe/SKILL.md` | From socrates socrates/ (name→apollo-probe) |
| `plugins/apollo/commons/skills/classify/SKILL.md` | From aristotle triage/ (name→apollo-classify) |
| `plugins/apollo/commons/skills/increment/SKILL.md` | From aristotle bump/ (name→apollo-increment) |
| `plugins/apollo/commons/skills/survey/SKILL.md` | From aristotle audit/ (name→apollo-survey) |
| `plugins/apollo/commons/skills/catalog/SKILL.md` | From aristotle inventory/ (name→apollo-catalog) |
| `plugins/apollo/commons/skills/grade/SKILL.md` | From aristotle review/ (name→apollo-grade) |
| `plugins/apollo/commons/skills/author/SKILL.md` | NEW knowledge skill (from plugin-dev hook-development) |
| `plugins/apollo/commons/skills/integrate/SKILL.md` | NEW knowledge skill (from plugin-dev mcp-integration) |
| `plugins/apollo/commons/skills/configure/SKILL.md` | NEW knowledge skill (from plugin-dev plugin-settings) |
| `plugins/apollo/commons/agents/scaffolder.md` | From daedalus agents/ |
| `plugins/apollo/commons/agents/scanner.md` | From socrates agents/ |
| `plugins/apollo/commons/agents/health-checker.md` | From aristotle agents/ |
| `plugins/apollo/commons/agents/agent-creator.md` | NEW (adapted from plugin-dev agents/agent-creator.md) |
| `plugins/apollo/commons/references/resource-types.md` | From daedalus references/ |
| `plugins/apollo/commons/references/rules-compact.md` | From socrates references/ |
| `plugins/apollo/commons/references/dialogue-templates.md` | From socrates references/ |
| `plugins/apollo/commons/references/version-protocol.md` | From aristotle references/ |
| `plugins/apollo/commons/references/shared-steps.md` | NEW merged |
| `plugins/apollo/commons/scripts/run_eval.py` | Ported from marketplace/plugins/copilot/scripts/ |
| `plugins/apollo/commons/scripts/run_loop.py` | Ported from marketplace/plugins/copilot/scripts/ |
| `plugins/apollo/commons/scripts/improve_description.py` | Ported from marketplace/plugins/copilot/scripts/ |
| `plugins/apollo/commons/scripts/validate-agents.sh` | Adapted from plugin-dev agent-development/scripts/ |
| `plugins/apollo/commons/scripts/validate-hooks-json.sh` | Adapted from plugin-dev hook-development/scripts/ |
| `plugins/apollo/commons/scripts/guard-build-dirs.sh` | NEW preToolUse hook guard |
| `plugins/apollo/commons/scripts/guard-build-dirs.ps1` | NEW PowerShell pair |
| `plugins/apollo/commons/schemas/hooks.schema.json` | Ported from marketplace/plugins/copilot/schemas/ |
| `plugins/apollo/commons/schemas/skill-frontmatter.schema.json` | Ported from marketplace/plugins/copilot/schemas/ |
| `plugins/apollo/commons/schemas/plugin.schema.json` | Ported from marketplace/plugins/copilot/schemas/ |
| `plugins/apollo/commons/templates/templates.json` | Ported + adapted from marketplace/plugins/copilot/templates/ |
| `plugins/apollo/commons/templates/resources/SKILL.md.j2` | Ported from marketplace/plugins/copilot/templates/resources/ |
| `plugins/apollo/commons/templates/resources/agent.md.j2` | Ported |
| `plugins/apollo/commons/templates/resources/command.md.j2` | Ported |
| `plugins/apollo/commons/templates/resources/plugin.json.j2` | Ported |
| `plugins/apollo/commons/templates/resources/hooks.json.j2` | Ported |
| `plugins/apollo/commons/templates/resources/hook.sh.j2` | Ported |
| `plugins/apollo/commons/templates/resources/hook.ps1.j2` | Ported |
| `plugins/apollo/commons/templates/resources/mcp.json.j2` | Ported |
| `plugins/apollo/commons/templates/resources/README.md.j2` | Ported |

### Modified files — Closure
| File | Change |
|------|--------|
| `scripts/build-platforms.py` | Add scripts/templates/schemas to copy list |
| `scripts/render_template.py` | Port from copilot monolith (new file in veiled-market/scripts/) |
| `sources/plugins.json` | Add apollo entry with platform_sources |
| `plugins/daedalus/commons/plugin.base.json` | Mark deprecated |
| `plugins/socrates/commons/plugin.base.json` | Mark deprecated |
| `plugins/aristotle/commons/plugin.base.json` | Mark deprecated |
| `docs/PLUGIN-LIFECYCLE.md` | Update skill names and plugin table |
| `docs/arch-veiled-market.md` | Update plugin table (trio → apollo) |
| `veiled-market/CLAUDE.md` | Update plugin roadmap table |

---

## Dispatch Group 0: Review Agents (run in parallel)

### Task 1: Doc Review

**Working directory:** `veiled-market/`
**Produces:** `docs/superpowers/findings/doc-review-findings.md`

- [ ] Read `docs/implementation-plan.md`
- [ ] Read `docs/plugin-inventory.md`
- [ ] Read `docs/MARKETPLACE.md` §3 (Standard Rules) and §4 (Anti-Patterns)
- [ ] Read `docs/PLUGIN-LIFECYCLE.md`
- [ ] Read `docs/arch-veiled-market.md`
- [ ] Read `docs/arch-commons-build.md`
- [ ] Read `docs/plugin-dev-comparison.md`
- [ ] Read `../CLAUDE.md` (workspace root)
- [ ] Read `README.md`
- [ ] Check `docs/PLUGIN-LIFECYCLE.md`: list every occurrence of old skill names — `create`, `update`, `build`, `remediate`, `triage`, `bump`, `audit`, `inventory`, `review` — that should become Apollo names
- [ ] Check `docs/arch-veiled-market.md` plugin status table: does it still list daedalus/socrates/aristotle as active? Note the exact table.
- [ ] Check `CLAUDE.md` plugin roadmap: does it show the trio or atlas+apollo?
- [ ] Check `implementation-plan.md` vs `plugin-inventory.md`: flag any file listed in one but absent from the other; flag line count discrepancies >20 lines
- [ ] Check all proposed skill descriptions (from implementation-plan.md) for Rule 21 compliance (≤60 words each)
- [ ] Check: is `render_template.py` referenced in any doc as already existing in `veiled-market/scripts/`? It should not be — it's pending port.
- [ ] Write structured findings to `docs/superpowers/findings/doc-review-findings.md`:

```markdown
# Doc Review Findings

## Stale references (by file)
...

## Rule violations in plan
...

## implementation-plan.md vs plugin-inventory.md gaps
...

## Recommended doc edits (Task 30)
...
```

- [ ] Commit: `git add docs/superpowers/findings/doc-review-findings.md && git commit -m "docs: add doc-review findings"`

---

### Task 2: Engineering Review

**Working directory:** `veiled-market/`
**Produces:** `docs/superpowers/findings/engineering-review-findings.md`

- [ ] Run `python3 scripts/validate_commons.py --plugin atlas 2>&1` — record full output
- [ ] Run `python3 scripts/validate_commons.py --plugin daedalus 2>&1` — record full output
- [ ] Run `python3 scripts/validate_commons.py --plugin socrates 2>&1` — record full output
- [ ] Run `python3 scripts/validate_commons.py --plugin aristotle 2>&1` — record full output
- [ ] Read `scripts/build-platforms.py` — identify the exact list of subdirectories currently copied; confirm `scripts/`, `templates/`, `schemas/` are absent from the copy logic
- [ ] Run `ls marketplace/plugins/copilot/scripts/` — confirm run_eval.py, run_loop.py, improve_description.py, render_template.py exist
- [ ] Run `ls marketplace/plugins/copilot/schemas/` — confirm 3 schema files exist
- [ ] Run `ls marketplace/plugins/copilot/templates/` and `ls marketplace/plugins/copilot/templates/resources/` — confirm templates.json and 9 .j2 files
- [ ] Run `ls claude-plugins-official/plugins/plugin-dev/skills/` — confirm hook-development, mcp-integration, plugin-settings, agent-development directories
- [ ] Run `ls claude-plugins-official/plugins/plugin-dev/agents/` — confirm agent-creator.md exists
- [ ] Read `sources/plugins.json` — list all current plugin entries; confirm atlas entry exists with platform_sources; confirm no apollo entry
- [ ] Confirm `plugins/atlas/commons/hooks.json` content = `{"hooks": {}}` (missing version:1)
- [ ] Check `plugins/daedalus/commons/hooks.json`, `plugins/socrates/commons/hooks.json`, `plugins/aristotle/commons/hooks.json` — record contents
- [ ] Write findings to `docs/superpowers/findings/engineering-review-findings.md`:

```markdown
# Engineering Review Findings

## validate_commons.py results (current state)
...

## build-platforms.py: directories currently copied
...

## Source file inventory confirmed
...

## sources/plugins.json current entries
...

## Defects confirmed
- atlas hooks.json: missing version:1 ✓
- ...
```

- [ ] Commit: `git add docs/superpowers/findings/engineering-review-findings.md && git commit -m "docs: add engineering-review findings"`

---

## Dispatch Group 1: Prerequisites (sequential)

### Task 3: Extend build-platforms.py

**Files:**
- Modify: `veiled-market/scripts/build-platforms.py`

- [ ] Read `veiled-market/scripts/build-platforms.py` — locate the section that iterates over subdirectories to copy into claude/ and copilot/ outputs
- [ ] Identify the current list of copied directories (expected: skills/, agents/, commands/, references/)
- [ ] Add `scripts/`, `templates/`, `schemas/` to the copy logic. Copy each only if it exists in the plugin's commons/ (graceful skip for plugins that don't have them):

```python
OPTIONAL_DIRS = ['scripts', 'templates', 'schemas']
for d in OPTIONAL_DIRS:
    src = commons_dir / d
    if src.exists():
        shutil.copytree(src, output_dir / d, dirs_exist_ok=True)
```

(Adapt to match the actual style used in the script — the above is the intent, not verbatim code)

- [ ] Run `python3 scripts/build-platforms.py --plugin atlas --dry-run` — expected: no errors; templates/ should appear in the dry-run output
- [ ] Run `python3 scripts/build-platforms.py --plugin daedalus --dry-run` — expected: no errors
- [ ] Commit: `git commit -m "feat(build): copy scripts/ templates/ schemas/ in build-platforms.py"`

---

### Task 4: Port render_template.py

**Files:**
- Read: `marketplace/plugins/copilot/scripts/render_template.py`
- Create: `veiled-market/scripts/render_template.py`

- [ ] Read `marketplace/plugins/copilot/scripts/render_template.py`
- [ ] Copy to `veiled-market/scripts/render_template.py`
- [ ] Run `python3 veiled-market/scripts/render_template.py --help` — verify it prints usage without import errors
- [ ] Commit: `git commit -m "feat(scripts): port render_template.py from copilot monolith"`

---

## Track A: Atlas (Dispatch Group 2a — parallel with Track B)

### Task 5: Fix atlas hooks.json

**Files:**
- Modify: `veiled-market/plugins/atlas/commons/hooks.json`

- [ ] Confirm current content: `cat plugins/atlas/commons/hooks.json` — expect `{"hooks": {}}`
- [ ] Write new content:

```json
{"version": 1, "hooks": {}}
```

- [ ] Run `python3 scripts/validate_commons.py --plugin atlas` — hooks.json check should now pass
- [ ] Commit: `git commit -m "fix(atlas): add version:1 to hooks.json"`

---

### Task 6: Add scaffold route to atlas command

**Files:**
- Read + Modify: `veiled-market/plugins/atlas/commons/commands/atlas.md`

- [ ] Read `plugins/atlas/commons/commands/atlas.md` — note current routes (init / sync / validate)
- [ ] Add `scaffold` as the first route: when the user types `/anchor scaffold`, invoke the `atlas-scaffold` skill
- [ ] Verify file is ≤66 lines: `wc -l plugins/atlas/commons/commands/atlas.md`
- [ ] Commit: `git commit -m "feat(atlas): add scaffold route to /anchor command"`

---

### Task 7: Create atlas-scaffold skill

**Files:**
- Read: `veiled-market/plugins/atlas/commons/skills/init/SKILL.md` (for delegation pattern)
- Read: `veiled-market/docs/implementation-plan.md` (scaffold workflow spec)
- Create: `veiled-market/plugins/atlas/commons/skills/scaffold/SKILL.md`

The skill must:
- Have frontmatter `name: atlas-scaffold`, `user-invocable: false`
- Description ≤60 words, triggers on "scaffold new project", "create project from scratch", "new project"
- Step 1: Ask project questions (name, language(s), type: library|app|service|cli, license, CI/CD platform)
- Step 2: Create directory structure per `references/project-types.md`
- Step 3: Render files from `templates/scaffold/` for the chosen language
- Step 4: Delegate to `atlas-init` skill for AI context files
- Step 5: Run `git init` + initial commit (unless git_mode: none)
- Step 6: Report all created files and next steps

- [ ] Read `plugins/atlas/commons/skills/init/SKILL.md` — note how it structures steps and references templates
- [ ] Read `docs/implementation-plan.md` §"New: `/anchor scaffold` workflow" steps 1-7
- [ ] Create `plugins/atlas/commons/skills/scaffold/SKILL.md` (≤200 lines)
- [ ] Verify: `wc -l plugins/atlas/commons/skills/scaffold/SKILL.md` — must be ≤200
- [ ] Run `python3 scripts/validate_commons.py --plugin atlas` — must pass
- [ ] Commit: `git commit -m "feat(atlas): add atlas-scaffold skill"`

---

### Task 8: Create project-types reference

**Files:**
- Read: `veiled-market/docs/implementation-plan.md` (project-types spec)
- Create: `veiled-market/plugins/atlas/commons/references/project-types.md`

Must cover 4 archetypes: library, app, service, cli — each with:
- Description
- Standard directory layout (language-specific where applicable)
- Standard files list

- [ ] Read `docs/implementation-plan.md` §"New: `project-types.md` reference"
- [ ] Create `plugins/atlas/commons/references/project-types.md` (~100 lines) covering all 4 archetypes with language-specific layouts (Python/Go/TypeScript variants for each)
- [ ] Commit: `git commit -m "feat(atlas): add project-types reference"`

---

### Task 9: Create 8 scaffold templates

**Files:**
- Read: `veiled-market/plugins/atlas/commons/templates/CLAUDE.md.j2` (for Jinja2 variable style)
- Read: `veiled-market/docs/plugin-inventory.md` §1.6 (template variables per file)
- Create: 8 template files under `plugins/atlas/commons/templates/scaffold/`

Variables per template (from plugin-inventory.md):
- `pyproject.toml.j2`: `project_name`, `version`, `description`, `author`, `license`, `python_version`
- `package.json.j2`: `project_name`, `version`, `description`, `author`, `license`
- `go.mod.j2`: `module_path`, `go_version`
- `Makefile.j2`: `project_name`, `language`, `project_type`
- `.editorconfig.j2`: (no variables — sensible defaults)
- `CONTRIBUTING.md.j2`: `project_name`
- `ci/github-actions.yml.j2`: `language`, `test_cmd`, `build_cmd`
- `ci/azure-pipelines.yml.j2`: `language`, `test_cmd`, `build_cmd`, `pool`

- [ ] Read `plugins/atlas/commons/templates/CLAUDE.md.j2` — note `{{ variable }}` style and conditional blocks
- [ ] Read `docs/plugin-inventory.md` §1.6 scaffold templates table
- [ ] Create `templates/scaffold/pyproject.toml.j2` (~50 lines)
- [ ] Create `templates/scaffold/package.json.j2` (~45 lines)
- [ ] Create `templates/scaffold/go.mod.j2` (~15 lines)
- [ ] Create `templates/scaffold/Makefile.j2` (~60 lines)
- [ ] Create `templates/scaffold/.editorconfig.j2` (~25 lines)
- [ ] Create `templates/scaffold/CONTRIBUTING.md.j2` (~50 lines)
- [ ] Create `templates/scaffold/ci/github-actions.yml.j2` (~45 lines)
- [ ] Create `templates/scaffold/ci/azure-pipelines.yml.j2` (~45 lines)
- [ ] Commit: `git commit -m "feat(atlas): add 8 scaffold templates"`

---

### Task 10: Extend templates.json, managed-files.md, shared-steps.md

**Files:**
- Read + Modify: `plugins/atlas/commons/templates/templates.json`
- Read + Modify: `plugins/atlas/commons/references/managed-files.md`
- Read + Modify: `plugins/atlas/commons/references/shared-steps.md`

- [ ] Read `plugins/atlas/commons/templates/templates.json` — note the entry schema (name, path, scope, variables, applyTo)
- [ ] Add scaffold-scope entries for all 8 new templates (use `"scope": "scaffold"` to distinguish from workspace templates)
- [ ] Read `plugins/atlas/commons/references/managed-files.md` — note entry format
- [ ] Add entries for scaffold-managed files: pyproject.toml, package.json, go.mod, Makefile, .editorconfig, CONTRIBUTING.md, .github/workflows/ci.yml, azure-pipelines.yml — with their template source and render conditions
- [ ] Read `plugins/atlas/commons/references/shared-steps.md` — note existing `## [anchor-name]` format
- [ ] Add `## [scaffold-structure]` anchor section documenting the directory creation sequence for each project type
- [ ] Commit: `git commit -m "feat(atlas): extend templates.json, managed-files, shared-steps for scaffold"`

---

### Task 11: Build and validate atlas

- [ ] Run `python3 scripts/validate_commons.py --plugin atlas` — must pass with zero errors; fix any errors before continuing
- [ ] Run `python3 scripts/build-platforms.py --plugin atlas`
- [ ] Verify `plugins/atlas/claude/skills/scaffold/SKILL.md` exists
- [ ] Verify `plugins/atlas/copilot/skills/scaffold/workflow.md` exists (scaffold has `user-invocable: false`)
- [ ] Verify `plugins/atlas/claude/hooks.json` — must contain `"version": 1`
- [ ] Verify `plugins/atlas/claude/templates/scaffold/` exists and contains 8 files
- [ ] Verify `plugins/atlas/copilot/templates/scaffold/` exists and contains 8 files
- [ ] Commit: `git commit -m "build(atlas): generate claude/ and copilot/ outputs for v1.0.0"`

---

## Track B: Apollo — Phase 2 Content Merge (Dispatch Group 2b — parallel with Track A)

### Task 12: Create apollo/commons/ structure

**Files:**
- Create: `veiled-market/plugins/apollo/commons/plugin.base.json`
- Create: `veiled-market/plugins/apollo/commons/hooks.json`

- [ ] Read `plugins/daedalus/commons/plugin.base.json` — note the structure
- [ ] Create `plugins/apollo/commons/plugin.base.json`:

```json
{
  "$schema": "../../schemas/plugin.base.schema.json",
  "name": "apollo",
  "version": "1.0.0",
  "description": "Plugin lifecycle management for veiled-market — forge, probe, fix, increment, survey, catalog, and grade marketplace plugins across Claude Code and Copilot CLI.",
  "author": { "name": "Ledermayer" },
  "license": "MIT",
  "keywords": ["plugin", "lifecycle", "forge", "probe", "steward", "marketplace"],
  "tags": ["plugins", "marketplace", "lifecycle"],
  "category": "AI Agents",
  "skills": [
    { "path": "skills/forge", "user-invocable": false },
    { "path": "skills/edit", "user-invocable": false },
    { "path": "skills/assemble", "user-invocable": false },
    { "path": "skills/fix", "user-invocable": false },
    { "path": "skills/probe", "user-invocable": false },
    { "path": "skills/classify", "user-invocable": false },
    { "path": "skills/increment", "user-invocable": false },
    { "path": "skills/survey", "user-invocable": false },
    { "path": "skills/catalog", "user-invocable": false },
    { "path": "skills/grade", "user-invocable": false },
    { "path": "skills/author", "user-invocable": false },
    { "path": "skills/integrate", "user-invocable": false },
    { "path": "skills/configure", "user-invocable": false }
  ],
  "agents": [
    { "path": "agents/scaffolder.md" },
    { "path": "agents/scanner.md" },
    { "path": "agents/health-checker.md" },
    { "path": "agents/agent-creator.md" }
  ],
  "hooks": "hooks.json"
}
```

- [ ] Create `plugins/apollo/commons/hooks.json`:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/guard-build-dirs.sh"
          }
        ]
      }
    ]
  }
}
```

Note: `guard-build-dirs.sh` is created in Task 20. The hook wiring is correct; the script is added in Phase 3.

- [ ] Commit: `git commit -m "feat(apollo): scaffold apollo/commons/ with plugin.base.json and hooks.json"`

---

### Task 13: Create apollo commands

**Files:**
- Read: `plugins/daedalus/commons/commands/daedalus.md`
- Read: `plugins/socrates/commons/commands/socrates.md`
- Read: `plugins/aristotle/commons/commands/aristotle.md`
- Create: `plugins/apollo/commons/commands/forge.md`
- Create: `plugins/apollo/commons/commands/probe.md`
- Create: `plugins/apollo/commons/commands/steward.md`

- [ ] Read all 3 trio commands
- [ ] Create `forge.md`: adapt daedalus.md — change command name to `forge`, update all skill references to `apollo-forge` / `apollo-edit` / `apollo-assemble` / `apollo-fix`, ≤66 lines
- [ ] Create `probe.md`: adapt socrates.md — change command name to `probe`, update skill reference to `apollo-probe`, ≤66 lines
- [ ] Create `steward.md`: adapt aristotle.md — change command name to `steward`, update all skill references to `apollo-classify` / `apollo-increment` / `apollo-survey` / `apollo-catalog` / `apollo-grade`, ≤66 lines
- [ ] Verify all three: `wc -l plugins/apollo/commons/commands/*.md` — each must be ≤66
- [ ] Commit: `git commit -m "feat(apollo): add forge/probe/steward commands"`

---

### Task 14: Create apollo forge skills (from daedalus)

**Files:**
- Read: `plugins/daedalus/commons/skills/create/SKILL.md` → Create: `plugins/apollo/commons/skills/forge/SKILL.md`
- Read: `plugins/daedalus/commons/skills/update/SKILL.md` → Create: `plugins/apollo/commons/skills/edit/SKILL.md`
- Read: `plugins/daedalus/commons/skills/build/SKILL.md` → Create: `plugins/apollo/commons/skills/assemble/SKILL.md`
- Read: `plugins/daedalus/commons/skills/remediate/SKILL.md` → Create: `plugins/apollo/commons/skills/fix/SKILL.md`

Trio stays intact — these are NEW files in apollo/. Do not delete daedalus skills.

- [ ] Read `skills/create/SKILL.md`; create `apollo/skills/forge/SKILL.md` — change frontmatter `name: apollo-forge`; update any internal references to `daedalus-create` → `apollo-forge`; update references to `/forge create` → `/forge`
- [ ] Read `skills/update/SKILL.md`; create `apollo/skills/edit/SKILL.md` — frontmatter `name: apollo-edit`
- [ ] Read `skills/build/SKILL.md`; create `apollo/skills/assemble/SKILL.md` — frontmatter `name: apollo-assemble`; update references from `/forge build` → `/forge assemble`
- [ ] Read `skills/remediate/SKILL.md`; create `apollo/skills/fix/SKILL.md` — frontmatter `name: apollo-fix`
- [ ] Verify each: `wc -l plugins/apollo/commons/skills/forge/SKILL.md` etc. — each ≤200 lines
- [ ] Commit: `git commit -m "feat(apollo): add forge/edit/assemble/fix skills from daedalus"`

---

### Task 15: Create apollo probe skill (from socrates)

**Files:**
- Read: `plugins/socrates/commons/skills/socrates/SKILL.md`
- Create: `plugins/apollo/commons/skills/probe/SKILL.md`

- [ ] Read `skills/socrates/SKILL.md`
- [ ] Create `apollo/skills/probe/SKILL.md` — frontmatter `name: apollo-probe`; update any internal self-references from `socrates` → `apollo-probe`
- [ ] Verify ≤200 lines
- [ ] Commit: `git commit -m "feat(apollo): add probe skill from socrates"`

---

### Task 16: Create apollo steward skills (from aristotle)

**Files:**
- Read + Create (5 pairs):
  - `aristotle/skills/triage/SKILL.md` → `apollo/skills/classify/SKILL.md` (name: apollo-classify)
  - `aristotle/skills/bump/SKILL.md` → `apollo/skills/increment/SKILL.md` (name: apollo-increment)
  - `aristotle/skills/audit/SKILL.md` → `apollo/skills/survey/SKILL.md` (name: apollo-survey)
  - `aristotle/skills/inventory/SKILL.md` → `apollo/skills/catalog/SKILL.md` (name: apollo-catalog)
  - `aristotle/skills/review/SKILL.md` → `apollo/skills/grade/SKILL.md` (name: apollo-grade)

- [ ] Read all 5 aristotle skills
- [ ] Create each apollo skill: copy content, update frontmatter name, update internal skill name references (e.g., `aristotle-triage` → `apollo-classify`)
- [ ] Verify each ≤200 lines
- [ ] Commit: `git commit -m "feat(apollo): add classify/increment/survey/catalog/grade skills from aristotle"`

---

### Task 17: Create apollo agents (from trio)

**Files:**
- Read: `plugins/daedalus/commons/agents/scaffolder.md` → Create: `plugins/apollo/commons/agents/scaffolder.md`
- Read: `plugins/socrates/commons/agents/scanner.md` → Create: `plugins/apollo/commons/agents/scanner.md`
- Read: `plugins/aristotle/commons/agents/health-checker.md` → Create: `plugins/apollo/commons/agents/health-checker.md`

- [ ] Read `daedalus/agents/scaffolder.md`; copy to `apollo/agents/scaffolder.md`; verify `## Inputs` section is present (MARKETPLACE.md Rule 7 — Workflow Agent must declare typed inputs); verify ≤200 lines
- [ ] Read `socrates/agents/scanner.md`; copy to `apollo/agents/scanner.md`; check if frontmatter is present — if missing, add minimal frontmatter (`name`, `description`); verify ≤200 lines
- [ ] Read `aristotle/agents/health-checker.md`; copy to `apollo/agents/health-checker.md`; verify `## Inputs` present; verify ≤200 lines
- [ ] Commit: `git commit -m "feat(apollo): copy agents from trio (scaffolder/scanner/health-checker)"`

---

### Task 18: Create apollo references (from trio + new merged)

**Files:**
- Read + Create: 4 references from trio, 1 new merged

- [ ] Copy `daedalus/references/resource-types.md` → `apollo/references/resource-types.md`
- [ ] Copy `socrates/references/rules-compact.md` → `apollo/references/rules-compact.md`
- [ ] Copy `socrates/references/dialogue-templates.md` → `apollo/references/dialogue-templates.md`
- [ ] Copy `aristotle/references/version-protocol.md` → `apollo/references/version-protocol.md`
- [ ] Create `apollo/references/shared-steps.md` — new merged reference with named anchors:
  - `## [read-manifest]` — steps to read and validate plugin.base.json
  - `## [check-names]` — steps to verify skill/agent name compliance (apollo-* prefix)
  - `## [resource-locations]` — table of expected commons/ paths per resource type
  - `## [version-bump-rules]` — semver rules from version-protocol condensed for quick reference
- [ ] Commit: `git commit -m "feat(apollo): add references from trio + merged shared-steps"`

---

## Track B: Apollo — Phase 3 Tooling Port

### Task 19: Port eval loop scripts

**Files:**
- Read + Create: 3 scripts from `marketplace/plugins/copilot/scripts/`

- [ ] Read `marketplace/plugins/copilot/scripts/run_eval.py`
- [ ] Copy to `plugins/apollo/commons/scripts/run_eval.py`; update any hardcoded paths referencing the copilot plugin directory (search for `plugins/copilot` or similar) to use `${CLAUDE_PLUGIN_ROOT}` or relative paths
- [ ] Read `marketplace/plugins/copilot/scripts/run_loop.py`
- [ ] Copy to `plugins/apollo/commons/scripts/run_loop.py`; same path adaptation
- [ ] Read `marketplace/plugins/copilot/scripts/improve_description.py`
- [ ] Copy to `plugins/apollo/commons/scripts/improve_description.py`; same path adaptation
- [ ] Run `python3 plugins/apollo/commons/scripts/run_eval.py --help` — verify no import errors
- [ ] Commit: `git commit -m "feat(apollo): port eval loop scripts from copilot monolith"`

---

### Task 20: Port + adapt bash validators; create guard hook scripts

**Files:**
- Read: `claude-plugins-official/plugins/plugin-dev/skills/agent-development/scripts/validate-agent.sh`
- Read: `claude-plugins-official/plugins/plugin-dev/skills/hook-development/scripts/validate-hook-schema.sh`
- Create: `plugins/apollo/commons/scripts/validate-agents.sh`
- Create: `plugins/apollo/commons/scripts/validate-hooks-json.sh`
- Create: `plugins/apollo/commons/scripts/guard-build-dirs.sh`
- Create: `plugins/apollo/commons/scripts/guard-build-dirs.ps1`

- [ ] Read `validate-agent.sh` (217 lines); adapt to dual-platform: handle both `.md` and `.agent.md` agent files; remove Claude-Code-only checks; target ≤150 lines; write to `apollo/commons/scripts/validate-agents.sh`
- [ ] Read `validate-hook-schema.sh` (159 lines); adapt event names to handle both platforms (PascalCase `PreToolUse` for Claude Code, camelCase `preToolUse` for Copilot); target ≤120 lines; write to `apollo/commons/scripts/validate-hooks-json.sh`
- [ ] Create `plugins/apollo/commons/scripts/guard-build-dirs.sh`:

```bash
#!/usr/bin/env bash
# guard-build-dirs.sh — preToolUse hook: block direct edits to build output dirs
set -euo pipefail
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
i = d.get('tool_input', {})
print(i.get('file_path', i.get('path', '')))
" 2>/dev/null || echo "")
if echo "$FILE" | grep -qE '/(claude|copilot)/'; then
  python3 -c "import json; print(json.dumps({'decision':'block','reason':'Direct edits to claude/ or copilot/ are not allowed. Edit commons/ and run build-platforms.py instead.'}))"
  exit 0
fi
python3 -c "import json; print(json.dumps({'decision':'approve'}))"
```

- [ ] Create `plugins/apollo/commons/scripts/guard-build-dirs.ps1`:

```powershell
# guard-build-dirs.ps1 — preToolUse hook (PowerShell pair for guard-build-dirs.sh)
$input_data = $input | ConvertFrom-Json -ErrorAction SilentlyContinue
$file = $input_data?.tool_input?.file_path ?? $input_data?.tool_input?.path ?? ""
if ($file -match '/(claude|copilot)/') {
    @{ decision = "block"; reason = "Direct edits to claude/ or copilot/ are not allowed. Edit commons/ and run build-platforms.py instead." } | ConvertTo-Json -Compress
    exit 0
}
@{ decision = "approve" } | ConvertTo-Json -Compress
```

- [ ] Make bash scripts executable: `chmod +x plugins/apollo/commons/scripts/*.sh`
- [ ] Commit: `git commit -m "feat(apollo): add bash validators and guard-build-dirs hook scripts"`

---

### Task 21: Port schemas

**Files:**
- Read + Create: 3 JSON schemas

- [ ] Read `marketplace/plugins/copilot/schemas/hooks.schema.json`; copy to `plugins/apollo/commons/schemas/hooks.schema.json`
- [ ] Read `marketplace/plugins/copilot/schemas/skill-frontmatter.schema.json`; copy to `plugins/apollo/commons/schemas/skill-frontmatter.schema.json`
- [ ] Read `marketplace/plugins/copilot/schemas/plugin.schema.json`; copy to `plugins/apollo/commons/schemas/plugin.schema.json`
- [ ] Quick validation: `python3 -c "import json; json.load(open('plugins/apollo/commons/schemas/hooks.schema.json'))"` — must parse without errors
- [ ] Commit: `git commit -m "feat(apollo): port JSON schemas from copilot monolith"`

---

### Task 22: Port resource templates

**Files:**
- Read + Create: templates.json + 9 .j2 files

- [ ] Read `marketplace/plugins/copilot/templates/templates.json`; copy to `plugins/apollo/commons/templates/templates.json`; update any paths that reference copilot-specific locations to use relative paths within apollo
- [ ] Read and copy all 9 files from `marketplace/plugins/copilot/templates/resources/` → `plugins/apollo/commons/templates/resources/`:
  - `SKILL.md.j2`, `agent.md.j2`, `command.md.j2`, `plugin.json.j2`, `hooks.json.j2`, `hook.sh.j2`, `hook.ps1.j2`, `mcp.json.j2`, `README.md.j2`
- [ ] Verify: `ls plugins/apollo/commons/templates/resources/ | wc -l` — expect 9
- [ ] Commit: `git commit -m "feat(apollo): port resource templates from copilot monolith"`

---

## Track B: Apollo — Phase 4 Knowledge Skills + Agent

### Task 23: Create apollo-author knowledge skill

**Files:**
- Read: `claude-plugins-official/plugins/plugin-dev/skills/hook-development/SKILL.md`
- Read: references/ in that skill directory (for deep content to extract)
- Create: `plugins/apollo/commons/skills/author/SKILL.md`

This is a **Knowledge Skill**: no numbered steps, no interactive prompts. Auto-triggers when description matches.

- [ ] Read plugin-dev hook-development SKILL.md and its references/ directory
- [ ] Distil into `apollo/commons/skills/author/SKILL.md`, ≤150 lines:
  - Frontmatter: `name: apollo-author`, `user-invocable: false`
  - Description (≤60 words): triggers on "add a hook", "create hook script", "preToolUse guard", "PostToolUse hook", "SessionStart injection"
  - Body: event type catalogue, stdin/stdout JSON contract, guard pattern examples, session context injection pattern, anti-patterns (orphaned scripts, missing version:1)
  - Push large tables to `references/` if needed to stay ≤150 lines (create `references/hook-patterns.md` if required)
- [ ] Verify no numbered steps exist in the body (Knowledge Skill rule)
- [ ] `wc -l plugins/apollo/commons/skills/author/SKILL.md` — must be ≤150
- [ ] Commit: `git commit -m "feat(apollo): add apollo-author knowledge skill"`

---

### Task 24: Create apollo-integrate knowledge skill

**Files:**
- Read: `claude-plugins-official/plugins/plugin-dev/skills/mcp-integration/SKILL.md`
- Create: `plugins/apollo/commons/skills/integrate/SKILL.md`

- [ ] Read plugin-dev mcp-integration SKILL.md and its references/
- [ ] Distil into `apollo/commons/skills/integrate/SKILL.md`, ≤150 lines:
  - Frontmatter: `name: apollo-integrate`, `user-invocable: false`
  - Description (≤60 words): triggers on "add MCP", "configure MCP server", "MCP integration", "stdio server", "http server"
  - Body: server types (stdio/local vs http), auth patterns, .mcp.json structure, Domain Expert Agent pairing pattern, env var injection
- [ ] Verify no numbered steps; no interactive prompts
- [ ] `wc -l` — must be ≤150
- [ ] Commit: `git commit -m "feat(apollo): add apollo-integrate knowledge skill"`

---

### Task 25: Create apollo-configure knowledge skill

**Files:**
- Read: `claude-plugins-official/plugins/plugin-dev/skills/plugin-settings/SKILL.md`
- Create: `plugins/apollo/commons/skills/configure/SKILL.md`

- [ ] Read plugin-dev plugin-settings SKILL.md and its references/
- [ ] Distil into `apollo/commons/skills/configure/SKILL.md`, ≤150 lines:
  - Frontmatter: `name: apollo-configure`, `user-invocable: false`
  - Description (≤60 words): triggers on "plugin settings", "configure permissions", "set model", "userConfig", "permissionMode"
  - Body: settings.json structure, permission levels, model selection, environment variables, scope hierarchy (user < project < plugin)
- [ ] Verify no numbered steps
- [ ] `wc -l` — must be ≤150
- [ ] Commit: `git commit -m "feat(apollo): add apollo-configure knowledge skill"`

---

### Task 26: Create agent-creator agent

**Files:**
- Read: `claude-plugins-official/plugins/plugin-dev/agents/agent-creator.md`
- Create: `plugins/apollo/commons/agents/agent-creator.md`

- [ ] Read plugin-dev agent-creator.md (176 lines)
- [ ] Adapt to `apollo/commons/agents/agent-creator.md`, ≤150 lines — dual-platform conventions (both Claude Code and Copilot CLI agent frontmatter formats)
- [ ] Must include `## Inputs` section with typed parameters (MARKETPLACE.md Rule 7)
- [ ] `wc -l` — must be ≤150
- [ ] Commit: `git commit -m "feat(apollo): add agent-creator agent (adapted from plugin-dev)"`

---

### Task 27: Build and validate apollo

- [ ] Run `python3 scripts/validate_commons.py --plugin apollo` — must pass with zero errors; fix any errors before continuing
- [ ] Run `python3 scripts/build-platforms.py --plugin apollo`
- [ ] Verify `plugins/apollo/claude/skills/forge/SKILL.md` exists
- [ ] Verify `plugins/apollo/copilot/skills/forge/workflow.md` exists (all apollo skills have `user-invocable: false`)
- [ ] Verify `plugins/apollo/claude/scripts/run_eval.py` exists (scripts/ copied by extended build script)
- [ ] Verify `plugins/apollo/claude/schemas/hooks.schema.json` exists
- [ ] Verify `plugins/apollo/claude/templates/resources/SKILL.md.j2` exists
- [ ] Verify `plugins/apollo/claude/hooks.json` contains `"version": 1`
- [ ] Commit: `git commit -m "build(apollo): generate claude/ and copilot/ outputs for v1.0.0"`

---

## Dispatch Group 3: Closure (after Track A + Track B)

### Task 28: Deprecate trio plugins

**Files:**
- Modify: `plugins/daedalus/commons/plugin.base.json`
- Modify: `plugins/socrates/commons/plugin.base.json`
- Modify: `plugins/aristotle/commons/plugin.base.json`
- Remove or replace: all skill/agent/command/reference files in each trio commons/

- [ ] For `daedalus/commons/plugin.base.json`: update `description` to `"DEPRECATED: functionality merged into the apollo plugin. Install apollo instead."`; update `version` to `"0.0.0-deprecated"`
- [ ] For `socrates/commons/plugin.base.json`: same deprecation pattern
- [ ] For `aristotle/commons/plugin.base.json`: same deprecation pattern
- [ ] Delete all files in each trio commons/ EXCEPT `plugin.base.json` and `hooks.json` — use `find plugins/<name>/commons -type f ! -name 'plugin.base.json' ! -name 'hooks.json' -delete` for each
- [ ] In each trio commons/, create a single `skills/deprecated/SKILL.md`:

```markdown
---
name: <plugin>-deprecated
description: 'DEPRECATED: this plugin has been merged into apollo. Install apollo instead.'
user-invocable: true
---

This plugin (daedalus/socrates/aristotle) has been merged into **apollo**.

Uninstall this plugin and install apollo to continue using plugin lifecycle management.
```

- [ ] Commit: `git commit -m "feat: deprecate daedalus/socrates/aristotle — merged into apollo"`

---

### Task 29: Update sources/plugins.json

**Files:**
- Modify: `veiled-market/sources/plugins.json`

- [ ] Read `sources/plugins.json`
- [ ] Add apollo entry (JSON object in the plugins array):

```json
{
  "name": "apollo",
  "description": "Plugin lifecycle management for veiled-market — forge, probe, fix, increment, survey, catalog, and grade marketplace plugins across Claude Code and Copilot CLI.",
  "version": "1.0.0",
  "source": "./plugins/apollo/copilot",
  "platform_sources": {
    "claude": "./plugins/apollo/claude",
    "copilot": "./plugins/apollo/copilot"
  }
}
```

- [ ] Verify atlas entry has `platform_sources` with `"claude": "./plugins/atlas/claude"` and `"copilot": "./plugins/atlas/copilot"`
- [ ] Validate JSON is well-formed: `python3 -c "import json; json.load(open('sources/plugins.json'))"`
- [ ] Commit: `git commit -m "feat: add apollo entry to sources/plugins.json"`

---

### Task 30: Update docs

**Files:**
- Read: `docs/superpowers/findings/doc-review-findings.md` (from Task 1)
- Modify: `docs/PLUGIN-LIFECYCLE.md`
- Modify: `docs/arch-veiled-market.md`
- Modify: `veiled-market/CLAUDE.md`

- [ ] Read `docs/superpowers/findings/doc-review-findings.md` — apply all flagged changes
- [ ] Update `docs/PLUGIN-LIFECYCLE.md`:
  - Replace plugin table: daedalus/socrates/aristotle → apollo (single entry, command `/forge` + `/probe` + `/steward`)
  - Replace all old skill names with Apollo names (create→forge, update→edit, build→assemble, remediate→fix, triage→classify, bump→increment, audit→survey, inventory→catalog, review→grade)
  - Update the handoff cycle diagram to reference apollo skills
- [ ] Update `docs/arch-veiled-market.md` plugin status table: remove daedalus/socrates/aristotle; add apollo
- [ ] Update `veiled-market/CLAUDE.md` plugin roadmap table: remove trio rows; add apollo row
- [ ] Commit: `git commit -m "docs: update PLUGIN-LIFECYCLE and arch docs to reflect apollo architecture"`

---

### Task 31: Regenerate manifests + final validation

- [ ] Run `python3 scripts/finalize.py --step regen`
- [ ] Verify `.github/plugin/marketplace.json` contains both `atlas` and `apollo` (and no longer solo trio entries)
- [ ] Verify `.claude-plugin/marketplace.json` contains both `atlas` and `apollo`
- [ ] Validate Copilot manifest: `python3 -c "import json, jsonschema; schema=json.load(open('schemas/marketplace.schema.json')); data=json.load(open('.github/plugin/marketplace.json')); jsonschema.validate(data, schema); print('Copilot manifest: VALID')"`
- [ ] Validate Claude manifest: `python3 -c "import json, jsonschema; schema=json.load(open('schemas/marketplace.schema.json')); data=json.load(open('.claude-plugin/marketplace.json')); jsonschema.validate(data, schema); print('Claude manifest: VALID')"`
- [ ] Final acceptance checklist — verify each item:
  - [ ] `plugins/atlas/claude/skills/scaffold/SKILL.md` exists
  - [ ] `plugins/atlas/commons/hooks.json` = `{"version": 1, "hooks": {}}`
  - [ ] `plugins/apollo/claude/skills/forge/SKILL.md` exists (and 12 other skills)
  - [ ] `plugins/apollo/claude/scripts/run_eval.py` exists
  - [ ] `plugins/apollo/claude/schemas/hooks.schema.json` exists
  - [ ] `plugins/apollo/claude/templates/resources/SKILL.md.j2` exists
  - [ ] `plugins/daedalus/commons/plugin.base.json` description contains "DEPRECATED"
  - [ ] Both `marketplace.json` files validated against schema
- [ ] Commit: `git commit -m "chore: regenerate marketplace manifests with atlas and apollo [skip ci]"`
