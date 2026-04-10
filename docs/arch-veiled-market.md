# Architecture: veiled-market

## Overview

`veiled-market/` is a dual-platform plugin marketplace that publishes plugins for both **GitHub Copilot CLI** (`.github/plugin/marketplace.json`) and **Claude Code** (`.claude-plugin/marketplace.json`) from a single source of truth. Plugins are authored using the **commons build system**: human-authored source lives in `plugins/<name>/commons/`, and `scripts/build-platforms.py` generates per-platform `claude/` and `copilot/` subdirectories. The `06-build-platforms.yml` workflow runs this automatically on push. All pipeline state lives in `sources/plugins.json`; both manifest files are always regenerated together by `finalize.py`.

---

## Directory Structure

### Repository Root

```
veiled-market/
├── CLAUDE.md                            ← Per-repo AI guidance (pipeline overview, format rules)
├── AGENTS.md                            ← Full pipeline spec for AI agents (~21 KB, authoritative)
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore
│
├── .github/
│   ├── copilot-instructions.md          ← Format spec, label scheme, pipeline quick-reference
│   ├── ISSUE_TEMPLATE/
│   │   ├── plugin-proposal.yml          ← Structured form: new plugin proposals
│   │   └── skill-discovery.yml
│   ├── plugin/
│   │   └── marketplace.json             ← AUTO-GENERATED (Copilot CLI target) — never hand-edit
│   └── workflows/
│       ├── dev/                     ← 7 archived AI pipeline workflows (shelved)
│       ├── 06-build-platforms.yml   ← Commons build: commons/ → claude/ + copilot/ per plugin
│       └── ci.yml
│
├── .claude-plugin/
│   └── marketplace.json                 ← AUTO-GENERATED (Claude Code target) — never hand-edit
│
├── drafts/                              ← AI-managed WIP — do not hand-edit
│   ├── README.md
│   └── <plugin-name>/
│       ├── plugin.json
│       ├── ENRICHMENT_NOTES.md
│       └── skills/<skill-name>/SKILL.md
│
├── plugins/                             ← Finalized, published plugins
│   └── <plugin-name>/                   ← see canonical layouts below
│
├── schemas/
│   ├── marketplace.schema.json          ← Validates both marketplace.json output files
│   ├── marketplaces.schema.json         ← Validates sources/marketplaces.json
│   ├── plugin.base.schema.json          ← Validates plugins/*/commons/plugin.base.json
│   ├── plugins.shema.json               ← [sic — typo is a frozen API surface] Validates sources/plugins.json
│   └── registry.schema.json            ← Validates sources/registry.json
│
├── scripts/
│   ├── build-platforms.py   ← Commons build: reads commons/ → writes claude/ + copilot/ (stdlib only)
│   ├── scaffold_plugin.py   ← Scaffold new commons/ from CLI args (name, description, command, skills)
│   ├── validate_commons.py  ← Structural validation of commons/ before build; handles legacy skills format
│   ├── sync_versions.py     ← Semver bump + propagate to all versioned files + manifest regen
│   ├── discover.py
│   ├── evaluate.py
│   ├── enrich.py
│   ├── finalize.py
│   ├── registry.py
│   └── compose.py
│
├── sources/
│   ├── marketplaces.json                ← Registry of 8+ upstream discovery sources
│   ├── plugins.json                     ← SINGLE SOURCE OF TRUTH for all plugin metadata
│   └── registry.json                    ← Per-resource evaluation cache (sha + scores + recommendation)
│
└── docs/
    ├── FINDINGS.md
    ├── MARKETPLACE.md
    ├── PLUGIN-LIFECYCLE.md              ← Authoritative spec: Daedalus→Socrates→Aristotle cycle
    ├── TODOS.md
    ├── arch-commons-build.md            ← Commons dual-platform build spec (implemented)
    └── arch-veiled-market.md            ← This file
```

### Canonical Plugin Layouts

**Legacy finalized plugins** (promoted from `drafts/` via the now-shelved AI pipeline — see [DISCOVERY.md](DISCOVERY.md)):

```
plugins/<name>/
├── plugin.json              ← Shared manifest (works for Copilot CLI + Claude Code)
├── agents/
│   └── <name>.agent.md      ← Agent definition: tools[], platforms[], languages[] frontmatter
├── hooks.json               ← Claude Code hooks (at plugin root — NOT in hooks/ subdir)
├── .mcp.json                ← External MCP server configs
└── skills/
    └── <skill-name>/
        └── SKILL.md         ← Light frontmatter: name, description, platforms[], languages[]
```

**Commons-built plugins** (hand-authored source, dual-platform build output):

```
plugins/<name>/
├── commons/                 ← Human-authored source of truth
│   ├── plugin.base.json     ← Platform-neutral manifest (not plugin.json)
│   ├── hooks.json           ← Claude Code format (build adds version:1 for Copilot)
│   ├── commands/<name>.md   ← Command router
│   ├── skills/
│   │   └── <skill-name>/
│   │       └── SKILL.md     ← user-invocable: false → workflow.md in Copilot output
│   ├── agents/
│   │   └── <agent>.md       ← Unified agent; renamed to <agent>.agent.md for Copilot
│   ├── references/          ← Reference docs (copied verbatim to both platforms)
│   │   ├── shared-steps.md  ← Reusable named step anchors used by all skills
│   │   ├── managed-files.md ← Managed file table + render conditions
│   │   └── stubs/           ← Jinja2 instruction stub templates (atlas pattern)
│   │       └── <lang>.instructions.j2
│   └── templates/           ← Jinja2 project file templates (atlas pattern)
│       ├── templates.json   ← Registry: file → applyTo glob + condition
│       └── …                ← .j2 templates mirroring target workspace structure
├── claude/                  ← AUTO-GENERATED by build-platforms.py — never hand-edit
│   ├── plugin.json
│   ├── hooks.json
│   ├── skills/<skill-name>/SKILL.md
│   └── …
└── copilot/                 ← AUTO-GENERATED by build-platforms.py — never hand-edit
    ├── plugin.json
    ├── hooks.json
    ├── skills/<skill-name>/workflow.md    ← Renamed from SKILL.md; user-invocable stripped
    └── …
```

**Key transforms applied by `build-platforms.py`:**

| Commons file | Claude output | Copilot output |
|---|---|---|
| `skills/<n>/SKILL.md` (user-invocable: false) | `skills/<n>/SKILL.md` (kept) | `skills/<n>/workflow.md` (renamed, flag stripped) |
| `agents/<n>.md` | `agents/<n>.md` | `agents/<n>.agent.md` |
| `hooks.json` | verbatim | adds `"version": 1` |
| `commands/<n>.md` | verbatim | `${CLAUDE_PLUGIN_ROOT}/skills/<x>/SKILL.md` → `skills/<x>/workflow.md` |
| `references/` | copied verbatim | copied verbatim |
| `templates/` | copied verbatim | copied verbatim |

### Draft Plugin Layout

```
drafts/<name>/
├── plugin.json              ← Partial manifest (may be a stub if AI was unavailable)
├── ENRICHMENT_NOTES.md      ← AI enrichment log or manual enrichment instructions
└── skills/
    └── <skill-name>/
        └── SKILL.md
```

---

## Discovery Pipeline (Shelved)

The AI-powered plugin discovery pipeline has been shelved pending a redesign. Full documentation, including workflow stages, data flows, and resumption guide, is preserved in [docs/DISCOVERY.md](DISCOVERY.md).

---

## Plugin Anatomy

### `plugin.json` Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | **Required** | Kebab-case, ≤64 chars, must match folder name |
| `version` | string | **Required** | Semver; initial `0.1.0`; `finalize.py` auto-bumps |
| `description` | string | **Required** | ≤300 chars (stricter than `marketplace/` 1024-char limit) |
| `license` | string | Recommended | `"MIT"` |
| `author` | object | Recommended | `{name, email?, url?}` |
| `homepage` | URI | Optional | |
| `repository` | URI | Optional | |
| `keywords` | string[] | Optional | |
| `category` | string | Optional | One of: `AI Agents`, `Coding`, `Data`, `DevOps`, `Marketing`, `Media`, `Other`, `Productivity`, `Security`, `Writing` |
| `tags` | string[] | Optional | |
| `agents` | string | Optional | `"agents/"` |
| `skills` | string | Optional | `"skills/"` |
| `hooks` | string | Optional | `"hooks.json"` (at plugin root) |
| `mcpServers` | string | Optional | `".mcp.json"` (external file path reference, not inline object) |

> **Note:** No `$schema` field in current published plugins. `mcpServers` is a path string — differs from `marketplace/` which may inline the object.

### `SKILL.md` Frontmatter

```yaml
---
name: terraform-plan
description: Preview infrastructure changes by running terraform plan (or tofu plan). …
platforms: [aws, azure, gcp, oci, digitalocean, vsphere, terraform-cloud, hcp-vault, github-actions, azure-devops, gitlab-ci, jenkins]
languages: [hcl, bash]
---
```

Fields present: `name`, `description` (inline, not `>-` block scalar), `platforms`, `languages`.  
Fields absent (vs `marketplace/`): no `license`, no `metadata`, no `user-invocable`, no `argument-hint`.

### Agent Frontmatter (`agents/<name>.agent.md`)

```yaml
---
name: terraformer
description: Expert Terraform and OpenTofu infrastructure engineer. …
tools: ["bash", "view", "edit", "glob", "rg", "task"]
platforms: [aws, azure, gcp, oci, digitalocean, vsphere, terraform-cloud, hcp-vault, github-actions, azure-devops, gitlab-ci, jenkins]
languages: [hcl, bash, powershell, yaml]
---
```

`tools` uses JSON array syntax. `platforms` and `languages` mirror SKILL.md pattern.

### `hooks.json` (Claude Code Format)

**Location:** `plugins/<name>/hooks.json` — at plugin root, NOT in a `hooks/` subdirectory.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "bash",
        "hooks": [{"type": "command", "command": "bash -c '...'"}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "bash",
        "hooks": [{"type": "command", "command": "bash -c '...'"}]
      }
    ]
  }
}
```

Key format rules: PascalCase event names (`PreToolUse`/`PostToolUse`), `matcher` field present, single `command` field (bash only). No `version` field, no `timeoutSec`, no cross-platform `.ps1` pairing — incompatible with `marketplace/` hook schema.

### `.mcp.json` (External MCP Config)

```json
{
  "mcpServers": {
    "terraform-ls": {
      "command": "terraform-ls",
      "args": ["serve"],
      "env": {},
      "_comment": "…"
    },
    "infracost": {
      "command": "npx",
      "args": ["-y", "@infracost/mcp-server"],
      "env": {"INFRACOST_API_KEY": "${INFRACOST_API_KEY}"}
    }
  }
}
```

Secrets injected via `${VAR_NAME}` environment variable references. Referenced from `plugin.json` as `"mcpServers": ".mcp.json"`.

---

## Manifest Generation

### Dual Output Files

| File | Target Platform | `$schema` reference |
|------|----------------|---------------------|
| `.github/plugin/marketplace.json` | Copilot CLI | `"../../schemas/marketplace.schema.json"` |
| `.claude-plugin/marketplace.json` | Claude Code | `"../schemas/marketplace.schema.json"` |

### Data Flow

```
sources/plugins.json  (SINGLE SOURCE OF TRUTH)
        │
        ▼
scripts/finalize.py --step regen          (or --step marketplace --plugin <name>)
        │  calls _write_marketplace_files()
        │  strips platform_sources; routes per-platform source values
        ├──► .github/plugin/marketplace.json     (Copilot CLI — source = platform_sources.copilot)
        └──► .claude-plugin/marketplace.json     (Claude Code — source = platform_sources.claude)
```

For **commons-built plugins**, `sources/plugins.json` entries include a `platform_sources` field:

```json
"platform_sources": {
  "claude":  "./plugins/socrates/claude",
  "copilot": "./plugins/socrates/copilot"
}
```

This field is **stripped** from the output marketplace.json files; `_write_marketplace_files()` uses it to write the correct `source` value for each platform.

Triggered by: `04-finalize-plugin.yml` (automated on candidate PR merge), manual `--step regen` invocation, or `--step marketplace --plugin <name>` during finalization.

### Invariant: Always Generate Both

**Both files must always be written simultaneously.** Writing one without the other breaks the dual-platform invariant. `finalize.py` enforces this by calling `_write_marketplace_files()` as a single atomic step. Neither file is ever hand-edited.

---

## Sources Data Model

| File | Schema | Purpose |
|------|--------|---------|
| `sources/marketplaces.json` | `schemas/marketplaces.schema.json` | Registry of 8+ upstream sources queried by `discover.py` |
| `sources/plugins.json` | `schemas/plugins.shema.json` [sic] | **Single source of truth** for all plugin metadata; feeds manifest generation |
| `sources/registry.json` | `schemas/registry.schema.json` | Per-resource evaluation cache: stores content SHA, AI scores, and recommendation status to avoid re-evaluating unchanged resources |

---

## Schemas

| Schema File | Validates | Key Differences vs `marketplace/` |
|-------------|-----------|-----------------------------------|
| `marketplace.schema.json` | Both `.github/plugin/marketplace.json` and `.claude-plugin/marketplace.json` | Adds `sourceNpm`, `sourcePip`, `strict` bool, `categories` enum; description `maxLength: 300` |
| `marketplaces.schema.json` | `sources/marketplaces.json` | Upstream source registry shape |
| `plugin.base.schema.json` | `plugins/*/commons/plugin.base.json` | Commons manifests: requires `name`, `version`, `license` |
| `plugins.shema.json` **[sic — typo intentional, frozen API surface]** | `sources/plugins.json` | Central plugin registry; misspelling is load-bearing (see [Known Constraints](#known-constraints)) |
| `registry.schema.json` | `sources/registry.json` | Evaluation tracking: sha, scores, recommendation per resource |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `build-platforms.py` | Commons build: reads `plugins/<name>/commons/` → generates `claude/` + `copilot/` with all platform transforms. CLI: `python3 scripts/build-platforms.py --plugin <name> [--dry-run]`. Stdlib-only. |
| `scaffold_plugin.py` | Scaffold a new `commons/` directory tree from CLI args (`--name`, `--description`, `--version`, `--command`, `--skills`, `--author`). Creates all required files and stub SKILL.md files. |
| `validate_commons.py` | Structural validation of `commons/` before build: required files present, `plugin.base.json` schema valid, frontmatter present, `hooks.json` wired, no orphaned scripts. Handles both modern array-of-objects and legacy string `skills` formats. |
| `sync_versions.py` | Semver bump (`patch`/`minor`/`major`) + propagate new version to `commons/plugin.base.json`, `claude/plugin.json`, `copilot/plugin.json`, and both `marketplace.json` files. Reports: `<plugin>: 1.0.0 → 1.0.1`. |
| `discover.py` | Query 8+ upstream sources → create one GitHub Issue per discovered resource |
| `evaluate.py` | AI-score open issues via GitHub Models API → synthesise draft plugin in `drafts/` |
| `enrich.py` | AI-enrich the best-scored draft → open candidate PR |
| `finalize.py` | Promote candidate from `drafts/` → `plugins/`; regenerate both `marketplace.json` files. Use `--step regen` to regenerate manifests only (no `--plugin` needed). |
| `registry.py` | Registry read/write/merge-patch helpers consumed by all other pipeline scripts |
| `compose.py` | Pipeline utility: manifest composition and assembly |

**Dependency note:** All scripts use Python stdlib only. `jsonschema` (pip) is the sole third-party dependency and is used exclusively in CI validation (`ci.yml`), not in the pipeline scripts themselves.

---

## Conventions

### Naming

- Plugin folder names: **kebab-case**, match `plugin.json` `name` field exactly, ≤64 chars.
- Skill folder names: kebab-case, match `SKILL.md` `name` frontmatter field.
- Agent files: `<plugin-name>.agent.md` inside `agents/`.

### Versioning

- Initial release: `0.1.0` (semver).
- `finalize.py` auto-bump logic:
  - **MINOR** bump if new skills or agents are added.
  - **PATCH** bump otherwise.
- All components within a plugin share the same version (`plugin.json`, agents, skills).

### Commit Style

Conventional Commits are mandatory:

```
feat(terraformer): add terraform-test skill
chore(registry): merge discovery patches [skip ci]
chore(finalize): promote terraformer to plugins/ [skip ci]
```

**`[skip ci]` is mandatory on every automated bot commit.** Omitting it causes cascade trigger loops across the pipeline (workflow triggers firing on bot-generated commits re-entering earlier pipeline stages). This is a hard operational rule, not a preference.

---

## Plugin Status

### Commons-Built Plugins

These plugins are hand-authored using the `commons/` build system and published to both platforms:

| Plugin | Status | Skills | Command |
|--------|--------|--------|---------|
| `atlas` | ✅ Built | init, update, validate | `/anchor` |
| `daedalus` | ✅ Built | create, update, build, remediate | `/forge` |
| `socrates` | ✅ Built | probe | `/probe` |
| `aristotle` | ✅ Built | triage, bump, audit, inventory, review | `/steward` |
| `zeno` | 🔲 Planned | — | `/bisect` |

### The Plugin Lifecycle Cycle

The three philosopher plugins form a closed management loop. Every plugin goes through this cycle:

```
/forge create       ─────────────────────────────────────────────────┐
/forge update       → /forge build → /probe → /steward triage →      │
/forge remediate ←───────────────────────────────────────────────────┘
      ↑
      └─── /steward bump → (done) ←── /probe passes
```

**Handoff chain:**

| Step completes | Next action |
|---------------|-------------|
| `/forge build` | `→ /probe <plugin>` |
| `/forge remediate` (+ build) | `→ /probe <plugin>` (re-audit) |
| `/probe` verdict written | `→ /steward triage <plugin>` |
| `/steward triage` | `→ /forge remediate <plugin>` (auto-fixes) |
| `/steward audit` | `→ /steward triage <plugin>` (per plugin) |
| `/steward bump` | `→ git add -A && git commit -m 'chore: bump <plugin> to vX.Y.Z'` |

See `docs/PLUGIN-LIFECYCLE.md` for the authoritative spec: `commons/` layout, 9 resource types, Socrates TODO schema, Aristotle triage protocol, and build conventions.

---

## Known Constraints

1. **`marketplace.json` files are never hand-edited.** Both `.github/plugin/marketplace.json` and `.claude-plugin/marketplace.json` are downstream artefacts generated by `finalize.py` from `sources/plugins.json`. Any direct edit will be overwritten on the next pipeline run.

2. **Hooks format is incompatible with `marketplace/`.** `veiled-market/` uses PascalCase event names (`PreToolUse`/`PostToolUse`), a `matcher` field, no `.ps1` pair, no `version` field, and no `timeoutSec` — all structurally incompatible with the Copilot CLI hook schema used in `marketplace/`. Do not copy hooks between repos without schema-aware transformation. `build-platforms.py` handles this by adding `"version": 1` for Copilot output only.

3. **`plugins.shema.json` typo is a frozen API surface.** The misspelling (`shema` not `schema`) is encoded in three places: the `$schema` field in `sources/plugins.json`, the `AGENTS.md` pipeline spec, and `ci.yml`. Renaming the file requires an atomic update of all three references in a single commit or the CI validation will break.

4. **Most `drafts/` entries are AI-unavailable stubs.** Only `terraformer` has been fully enriched and promoted via the AI pipeline. The 7 remaining drafts (`easy-*`) require manual enrichment or re-triggering `02-evaluate.yml`. They must not be promoted to `plugins/` in their current stub state.

5. **`[skip ci]` is required on all bot commits.** Any automated commit missing this tag re-enters the pipeline at `01-discovery.yml` or `02-evaluate.yml`, causing a cascade loop that consumes workflow minutes and creates duplicate issues.

6. **`01-discovery.yml` is shelved.** Automated triggers (`workflow_run` and `schedule`) have been removed from this workflow after it generated ~15k issue drafts. It now fires only via `workflow_dispatch`. To resume automated discovery, re-add the triggers and add appropriate guards (e.g., per-source deduplication or rate limits).

7. **Commons-built plugin outputs are committed artefacts.** The `claude/` and `copilot/` directories under `plugins/<name>/` are generated by `build-platforms.py` and committed to the repository. Do not hand-edit them — changes will be overwritten on the next `06-build-platforms.yml` run. Edit `commons/` instead.

8. **`platform_sources` is an internal routing field.** When present in `sources/plugins.json`, the `platform_sources` object is stripped from both marketplace.json output files by `_write_marketplace_files()`. It must never appear in the generated manifests.

9. **Atlas templates and stubs are not processed by the build script.** `build-platforms.py` copies `templates/` and `references/stubs/` verbatim to both platform outputs. Jinja2 rendering of `.j2` files is performed at runtime by the AI (skills read and render templates directly — no `render_template.py` script). Do not add build-time template rendering without updating the build script.

10. **`.config/` is the shared config directory.** All atlas config lives in `.config/atlas.json` — not a separate `.atlas/` folder. Any future plugins adding project-level config should follow this convention and place their config file in `.config/<plugin-name>.json`.

11. **`validate_commons.py` handles both `skills` formats.** The validator auto-detects both the modern array-of-objects format (per `docs/PLUGIN-LIFECYCLE.md`) and the legacy string format (`atlas` uses `"skills": "skills/"`). Do not "fix" the atlas format — both are supported by the validator and the build script.

---

## Planned Work

### Next Commons-Built Plugin: `zeno`

`zeno` (`/bisect`) is the only remaining planned plugin. Purpose: Terraform code review, narrowing down infrastructure diffs step by step. Not yet scoped.
