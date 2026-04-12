# Plan: Two-Plugin Foundation — Atlas (Earth) + Apollo (Star)

## Problem

We evaluated three approaches to plugin lifecycle management. The trio (Daedalus/Socrates/Aristotle) won architecturally, but a critical distribution flaw was identified: installed plugins only receive their `copilot/` or `claude/` subdirectory. Merging the trio into a single **Apollo** plugin solves distribution while keeping concerns separated from **Atlas** (workspace/project setup).

## Architecture: Earth & Star

| Plugin | Codename | Domain | Commands |
|--------|----------|--------|----------|
| **Atlas** | Earth side | Workspace & project setup | `/anchor` (scaffold, init, update, validate) |
| **Apollo** | Star side | Plugin lifecycle management | `/forge`, `/probe`, `/steward` |

### Why two plugins (not one monolith):
1. **Separation of concerns** — workspace setup (Atlas) and plugin lifecycle (Apollo) are orthogonal domains
2. **Independent versioning** — Atlas changes when workspace patterns evolve; Apollo changes when plugin rules evolve
3. **Installable standalone** — teams that only need workspace setup install Atlas alone; plugin authors also install Apollo
4. **Token budget** — splitting keeps each plugin well under the 4,000-token Level-1 threshold

### Key design decisions:
- **Distribution**: `build-platforms.py` extended to copy `scripts/`, `templates/`, `schemas/` → each plugin is self-contained
- **Script classification**: Tier 1 (repo-level, dev-time) vs Tier 2 (plugin-local, runtime). Only Tier 2 ships with the plugin.
- **Domain-explicit naming**: Every skill has a unique, domain-prefixed name to prevent trigger collisions

---

## Atlas Structure (with Scaffold capability)

Atlas gained a **scaffold** action: creates new projects from scratch (directory structure, language configs, CI/CD), then delegates to `init` for AI context.

```
atlas/commons/
├── plugin.base.json
├── hooks.json                    ← ⚠️ needs version:1 fix
├── commands/
│   └── atlas.md                  ← /anchor scaffold|init|update|validate
├── skills/
│   ├── scaffold/SKILL.md         ← NEW: greenfield project creation
│   ├── init/SKILL.md             ← existing: AI context + IDE config for existing projects
│   ├── update/SKILL.md           ← existing: sync managed files with latest templates
│   └── validate/SKILL.md         ← existing: check managed files for health
├── agents/
│   └── workspace-scanner.md      ← existing: structural scan for validate
├── references/
│   ├── managed-files.md          ← existing (extend with scaffold-managed files)
│   ├── shared-steps.md           ← existing (add [scaffold-structure] anchor)
│   ├── project-types.md          ← NEW: project type archetypes + directory layouts
│   └── stubs/                    ← existing: 32 instruction stub templates
└── templates/
    ├── templates.json            ← existing (extend with scaffold scope entries)
    ├── scaffold/                 ← NEW: project scaffolding templates
    │   ├── pyproject.toml.j2     ← Python project
    │   ├── package.json.j2       ← TypeScript/JS project
    │   ├── go.mod.j2             ← Go project
    │   ├── Makefile.j2           ← Generic build
    │   ├── .editorconfig.j2      ← Editor config
    │   ├── CONTRIBUTING.md.j2    ← Contribution guide
    │   └── ci/                   ← CI/CD templates
    │       ├── github-actions.yml.j2
    │       └── azure-pipelines.yml.j2
    └── (existing workspace/IDE templates)
```

### New: `/anchor scaffold` workflow

1. **Ask project questions**: project name, primary language(s), project type (library|app|service|cli), license, CI/CD platform
2. **Create directory structure**: language-appropriate layout (src/, tests/, docs/, scripts/)
3. **Render project files**: language config (pyproject.toml, package.json, go.mod), Makefile, .editorconfig, LICENSE, README, CHANGELOG, CONTRIBUTING
4. **Render CI/CD**: GitHub Actions and/or Azure Pipelines based on platform choice
5. **Delegate to init**: `scaffold` internally invokes the `init` skill workflow to add AI context (CLAUDE.md, copilot-instructions, IDE settings, instruction stubs)
6. **Git init**: `git init` + initial commit (if git_mode is not `none`)
7. **Summary**: report all created files and suggest next steps

### New: `project-types.md` reference

Defines 4 project archetypes with their standard directory layouts:

| Type | Description | Typical structure |
|------|-------------|-------------------|
| `library` | Reusable package/module | `src/`, `tests/`, `docs/`, `examples/` |
| `app` | Standalone application | `src/`, `tests/`, `config/`, `docs/` |
| `service` | Backend API / microservice | `src/`, `tests/`, `config/`, `scripts/`, `deploy/` |
| `cli` | Command-line tool | `cmd/`, `internal/`, `tests/`, `docs/` |

Each archetype maps to language-specific conventions (e.g., Go `cli` uses `cmd/<name>/main.go` + `internal/`).

### New: scaffold templates (scope: "scaffold")

| Template | Variables | Output |
|----------|-----------|--------|
| `pyproject.toml.j2` | project_name, version, description, author, license, python_version | `pyproject.toml` |
| `package.json.j2` | project_name, version, description, author, license | `package.json` |
| `go.mod.j2` | module_path, go_version | `go.mod` |
| `Makefile.j2` | project_name, language, project_type | `Makefile` |
| `.editorconfig.j2` | — | `.editorconfig` |
| `CONTRIBUTING.md.j2` | project_name | `CONTRIBUTING.md` |
| `github-actions.yml.j2` | language, test_cmd, build_cmd | `.github/workflows/ci.yml` |
| `azure-pipelines.yml.j2` | language, test_cmd, build_cmd, pool | `azure-pipelines.yml` |

Existing templates already used by scaffold: `README.md.j2`, `LICENSE.j2`, `CHANGELOG.md.j2`, `.gitignore.j2`, `project.code-workspace.j2`.

---

## Apollo Structure (Merged Trio)

Apollo merges Daedalus + Socrates + Aristotle into a single plugin for lifecycle management.

```
apollo/commons/
├── plugin.base.json
├── hooks.json                    ← version:1, wired with preToolUse guard
├── commands/
│   ├── forge.md                  ← /forge forge|edit|assemble|fix
│   ├── probe.md                  ← /probe <plugin>
│   └── steward.md                ← /steward classify|increment|survey|catalog|grade
├── skills/                       ← 13 skills (10 existing + 3 new knowledge)
│   ├── forge/                    ← from daedalus (apollo-forge)
│   ├── edit/                     ← from daedalus (apollo-edit)
│   ├── assemble/                 ← from daedalus (apollo-assemble)
│   ├── fix/                      ← from daedalus (apollo-fix)
│   ├── probe/                    ← from socrates (apollo-probe)
│   ├── classify/                 ← from aristotle (apollo-classify)
│   ├── increment/                ← from aristotle (apollo-increment)
│   ├── survey/                   ← from aristotle (apollo-survey)
│   ├── catalog/                  ← from aristotle (apollo-catalog)
│   ├── grade/                    ← from aristotle (apollo-grade)
│   ├── author/                   ← NEW knowledge skill (apollo-author)
│   ├── integrate/                ← NEW knowledge skill (apollo-integrate)
│   └── configure/                ← NEW knowledge skill (apollo-configure)
├── agents/
│   ├── scaffolder.md             ← from daedalus
│   ├── scanner.md                ← from socrates
│   ├── health-checker.md         ← from aristotle
│   └── agent-creator.md          ← NEW
├── references/
│   ├── resource-types.md         ← from daedalus
│   ├── rules-compact.md          ← from socrates
│   ├── dialogue-templates.md     ← from socrates
│   ├── version-protocol.md       ← from aristotle
│   └── shared-steps.md           ← NEW merged anchors
├── scripts/                      ← Tier 2 (distributed)
│   ├── run_eval.py               ← from copilot monolith
│   ├── run_loop.py               ← from copilot monolith
│   ├── improve_description.py    ← from copilot monolith
│   ├── guard-build-dirs.sh       ← NEW hook script
│   ├── guard-build-dirs.ps1      ← NEW hook script
│   ├── validate-agents.sh        ← from plugin-dev (adapted)
│   └── validate-hooks-json.sh    ← from plugin-dev (adapted)
├── schemas/                      ← ported from copilot monolith
│   ├── hooks.schema.json
│   ├── skill-frontmatter.schema.json
│   └── plugin.schema.json
└── templates/                    ← plugin resource scaffolding
    ├── templates.json
    └── resources/
        ├── SKILL.md.j2
        ├── agent.md.j2
        ├── command.md.j2
        ├── plugin.json.j2
        ├── hooks.json.j2
        ├── hook.sh.j2
        ├── hook.ps1.j2
        ├── mcp.json.j2
        └── README.md.j2
```

---

## Phased Build Sequence

### Phase 0 — Build System
- Extend `build-platforms.py` to copy `scripts/`, `templates/`, `schemas/`
- Test with existing atlas plugin (already has templates/)

### Phase 1 — Atlas Scaffold
- Create `workspace-scaffold` skill (~150-200 lines)
- Add `scaffold` route to `/anchor` command
- Create `project-types.md` reference
- Create scaffold templates: `pyproject.toml.j2`, `package.json.j2`, `go.mod.j2`, `Makefile.j2`, `.editorconfig.j2`, `CONTRIBUTING.md.j2`, CI/CD templates
- Extend `templates.json` with scaffold-scope entries
- Extend `managed-files.md` with scaffold-managed files
- Add `[scaffold-structure]` anchor to `shared-steps.md`
- Fix atlas `hooks.json` (add `"version": 1`)

### Phase 2 — Apollo Content Merge
- Create `apollo/commons/` directory tree
- Move all skills from trio with domain-explicit names
- Move all agents from trio
- Move and merge references
- Create merged commands: forge.md, probe.md, steward.md
- Create `plugin.base.json` with merged metadata
- Wire `hooks.json` with preToolUse guard

### Phase 3 — Apollo Tooling Port
- Port eval loop scripts (run_eval.py, run_loop.py, improve_description.py)
- Port bash validators (validate-agents.sh, validate-hooks-json.sh)
- Add JSON schemas (hooks, skill-frontmatter, plugin)
- Port plugin resource J2 templates + templates.json registry
- Port `render_template.py` to `veiled-market/scripts/` (Tier 1)

### Phase 4 — Knowledge Skills & Agents
- Create hook-authoring, mcp-authoring, settings-authoring knowledge skills
- Create agent-creator workflow agent
- Create Apollo shared-steps.md with merged anchors

### Phase 5 — Trio Deprecation
- Replace daedalus/socrates/aristotle `commons/` with deprecation notices
- Update marketplace.json entries
- Update all docs referencing the trio

### Phase 6 — Docs & Cleanup
- Update `plugin-lifecycle-blueprint.md` (currently stale — reflects trio)
- Update `plugin-inventory.md` with final file lists
- Final validation pass

## Skill Naming — Vote Results (7 agents)

### Final Names

| # | Domain | Old name | **Winner** | Votes | Strength | Runner-up |
|---|--------|----------|------------|-------|----------|-----------|
| 1 | Atlas | atlas-init | **atlas-init** | 5/7 | 🥇 Clear | bootstrap (1), provision (1) |
| 2 | Atlas | atlas-update | **atlas-sync** | 5/7 | 🥇 Clear | update (1), harmonize (1) |
| 3 | Atlas | atlas-validate | **atlas-validate** | 7/7 | 🏆 Unanimous | — |
| 4 | Forge | daedalus-create | **apollo-forge** | 6/7 | 🥇 Strong | generate (1) |
| 5 | Forge | daedalus-update | **apollo-edit** | 4/7 | ✅ Majority | revise (2), refine (1) |
| 6 | Forge | daedalus-build | **apollo-assemble** | 4/7 | ✅ Majority | compile (2), generate (1) |
| 7 | Forge | daedalus-remediate | **apollo-fix** | 3/7 | ⚖️ Plurality | resolve (1), repair (1), normalize (1), heal (1) |
| 8 | Probe | socrates | **apollo-probe** | 7/7 | 🏆 Unanimous | — |
| 9 | Steward | aristotle-triage | **apollo-classify** | 6/7 | 🥇 Strong | triage (1) |
| 10 | Steward | aristotle-bump | **apollo-increment** | 4/7 | ✅ Majority | rev (1), bump (1), advance (1) |
| 11 | Steward | aristotle-audit | **apollo-survey** | 4/7 | ✅ Majority | assess (2), audit (1) |
| 12 | Steward | aristotle-inventory | **apollo-catalog** | 6/7 | 🥇 Strong | list (1) |
| 13 | Steward | aristotle-review | **apollo-grade** ⚖️ | 3/7 | TIE | evaluate (3), critique (1) |
| 14 | Knowledge | apollo-hook-authoring | **apollo-author** | 3/7 | ⚖️ Plurality | guide (2), craft (2) |
| 15 | Knowledge | apollo-mcp-authoring | **apollo-integrate** 🔧 | 3/7 | Collision-resolved | configure (3) — blocked by #16 |
| 16 | Knowledge | apollo-settings-authoring | **apollo-configure** | 5/7 | 🥇 Clear | govern (1), define (1) |

### Tie-breaker Notes
- **#13**: grade (3) vs evaluate (3) — **grade recommended** as it's more specific to the eval-loop scoring context and avoids overlap with #8 probe's "evaluate" connotation
- **#15**: integrate (3) vs configure (3) — **integrate wins by deduction** since #16 already claims "configure" with 5 votes; no verb collisions allowed

### User's Original Preferences vs Vote
| Skill | User suggested | Vote picked | Aligned? |
|-------|---------------|-------------|----------|
| atlas-init | provision | init | ❌ (vote 5-1) |
| atlas-update | sync | sync | ✅ |
| atlas-validate | verify | validate | ❌ (vote 7-0) |

### Full Vocabulary (collision-free, 16 unique verbs + scaffold)

**Atlas (earth):** scaffold · init · sync · validate
**Apollo/Forge (create):** forge · edit · assemble · fix
**Apollo/Probe (validate):** probe
**Apollo/Steward (maintain):** classify · increment · survey · catalog · grade
**Apollo/Knowledge (teach):** author · integrate · configure

## Notes
- `plugin-inventory.md` and `plugin-lifecycle-blueprint.md` already exist in `veiled-market/docs/` — both need updating to reflect Apollo + scaffold
- Fix-type routing is unchanged — TODO files on disk, same schema, same values
- Domain-explicit skill naming prevents activation ambiguity across plugins
- Scaffold delegates to init — no duplicate AI context logic
