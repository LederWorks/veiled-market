# Plugin Inventory — veiled-market

> **Two foundational plugins. Every file catalogued.**
> **Last updated:** April 2026

---

## Architecture: Earth & Star

| Plugin | Codename | Domain | Command(s) | Role |
|--------|----------|--------|------------|------|
| **Atlas** | Earth side | Workspace & project setup | `/anchor` | Scaffolds new projects, configures local environment: AI context files, IDE settings |
| **Apollo** | Star side | Plugin lifecycle management | `/forge`, `/probe`, `/steward` | Forges, validates, and maintains marketplace plugins across platforms |

Both plugins use the `commons/` → `claude/` + `copilot/` build system.
Both are distributed as self-contained units — all runtime assets bundled.

---

## Naming Convention

Skills use the pattern `<plugin>-<verb>`. All 17 verbs are unique across the system (zero collisions).

### Vocabulary

| Domain | Verbs |
|--------|-------|
| **Atlas (earth)** | `scaffold` · `init` · `sync` · `validate` |
| **Apollo / Forge (create)** | `forge` · `edit` · `assemble` · `fix` |
| **Apollo / Probe (validate)** | `probe` |
| **Apollo / Steward (maintain)** | `classify` · `increment` · `survey` · `catalog` · `grade` |
| **Apollo / Knowledge (teach)** | `author` · `integrate` · `configure` |

---

## 1. Atlas (Earth Side)

### 1.1 Manifest

| Field | Value |
|-------|-------|
| **name** | `atlas` |
| **version** | `1.0.0` |
| **description** | 'Local workspace and project setup — scaffold, init, sync, and validate AI context files, IDE settings, and project structure for both Copilot CLI and Claude Code.' |
| **license** | MIT |
| **author** | Ledermayer |
| **category** | Coding |
| **platform** | Both (Claude Code + Copilot CLI) |
| **file** | `commons/plugin.base.json` (20 lines) |

### 1.2 Commands (1)

| File | Lines | Name | Description | Pattern | Routes to |
|------|-------|------|-------------|---------|-----------|
| `commands/atlas.md` | ~35 | `anchor` | 'local workspace and project setup — scaffold new projects, init AI context, sync managed files, and validate workspace health' | A (router) | `scaffold` → atlas-scaffold, `init` → atlas-init, `sync` → atlas-sync, `validate` → atlas-validate |

### 1.3 Skills (4)

| File | Lines | Name | Description | User-invocable |
|------|-------|------|-------------|----------------|
| `skills/scaffold/SKILL.md` | ~180 (NEW) | `atlas-scaffold` | 'Create a new project from scratch: ask project name, language, type (library/app/service/cli), license, CI/CD platform. Renders directory structure, language configs, and CI/CD, then delegates to atlas-init for AI context files.' | false |
| `skills/init/SKILL.md` | 123 | `atlas-init` | 'Full workspace setup: detect stack, configure AI context files, write IDE settings, and populate instruction stubs for both Copilot CLI and Claude Code.' | false |
| `skills/update/SKILL.md` | 95 | `atlas-sync` | 'Synchronise AI context files and IDE settings with the latest atlas templates. Compares current files against template output, shows a diff, and applies accepted changes.' | false |
| `skills/validate/SKILL.md` | 101 | `atlas-validate` | 'Check that all managed files exist, match template conventions, and have no stale sections. Spawns the workspace-scanner agent and reports a pass/fail summary.' | false |

### 1.4 Agents (1)

| File | Lines | Name | Description | Type | Model |
|------|-------|------|-------------|------|-------|
| `agents/workspace-scanner.md` | 144 | `workspace-scanner` | 'Scans a project workspace for managed files, checks completeness and consistency against atlas templates, and returns a structured JSON report.' | Workflow Agent | inherit |

### 1.5 References (3 + 32 stubs)

| File | Lines | Purpose |
|------|-------|---------|
| `references/managed-files.md` | ~145 | List of all files atlas manages (including scaffold-managed), their template source, and expected locations |
| `references/shared-steps.md` | ~220 | Named anchor sections: [analyse], [write-config], [detect-stubs], [validate-managed], [scaffold-structure] |
| `references/project-types.md` | ~100 (NEW) | 4 project archetypes (library, app, service, cli) with language-specific directory layouts and standard files |
| `references/stubs/*.instructions.j2` | 32 files | Language/tool instruction templates (aws, azure, bash, git, go, python, terraform, typescript, etc.) — 21–253 lines each |

**Stubs inventory (32 files):**

| Stub file | Lines | Domain |
|-----------|-------|--------|
| `aws.instructions.j2` | 166 | AWS cloud |
| `azure-devops.instructions.j2` | 137 | Azure DevOps |
| `azure.instructions.j2` | 70 | Azure cloud |
| `bash.instructions.j2` | 164 | Bash scripting |
| `claude.instructions.j2` | 27 | Claude Code |
| `cursor.instructions.j2` | 118 | Cursor IDE |
| `gcp.instructions.j2` | 150 | Google Cloud |
| `git.instructions.j2` | 253 | Git |
| `github.instructions.j2` | 90 | GitHub |
| `go.instructions.j2` | 122 | Go |
| `ide-universal.instructions.j2` | 29 | IDE universal |
| `instructions.md.j2` | 21 | Instructions base |
| `jetbrains.instructions.j2` | 97 | JetBrains IDEs |
| `jinja2.instructions.j2` | 181 | Jinja2 |
| `json.instructions.j2` | 204 | JSON |
| `markdown.instructions.j2` | 67 | Markdown |
| `oci.instructions.j2` | 162 | OCI (Oracle Cloud) |
| `powershell.instructions.j2` | 101 | PowerShell |
| `python.instructions.j2` | 204 | Python |
| `scripts.instructions.j2` | 73 | Scripts general |
| `security.instructions.j2` | 97 | Security |
| `sql.instructions.j2` | 219 | SQL |
| `terraform.instructions.j2` | 132 | Terraform |
| `typescript.instructions.j2` | 109 | TypeScript |
| `vscode.instructions.j2` | 113 | VS Code |
| `yaml.instructions.j2` | 190 | YAML |

### 1.6 Templates (31 + 8 scaffold + registry)

| File | Lines | Output target |
|------|-------|---------------|
| `templates/templates.json` | ~870 | Template registry — names, paths, variables, output patterns (extended with scaffold scope) |
| **Scaffold templates (NEW):** | | |
| `templates/scaffold/pyproject.toml.j2` | ~50 | `pyproject.toml` (Python projects) |
| `templates/scaffold/package.json.j2` | ~45 | `package.json` (TypeScript/JS projects) |
| `templates/scaffold/go.mod.j2` | ~15 | `go.mod` (Go projects) |
| `templates/scaffold/Makefile.j2` | ~60 | `Makefile` (generic build) |
| `templates/scaffold/.editorconfig.j2` | ~25 | `.editorconfig` |
| `templates/scaffold/CONTRIBUTING.md.j2` | ~50 | `CONTRIBUTING.md` |
| `templates/scaffold/ci/github-actions.yml.j2` | ~45 | `.github/workflows/ci.yml` |
| `templates/scaffold/ci/azure-pipelines.yml.j2` | ~45 | `azure-pipelines.yml` |
| **Workspace templates (existing):** | | |
| `templates/CLAUDE.md.j2` | 80 | `CLAUDE.md` |
| `templates/README.md.j2` | 170 | `README.md` |
| `templates/CHANGELOG.md.j2` | 59 | `CHANGELOG.md` |
| `templates/.gitignore.j2` | 169 | `.gitignore` |
| `templates/project.code-workspace.j2` | 40 | `*.code-workspace` |
| `templates/.config/atlas.json.j2` | 24 | `.config/atlas.json` |
| `templates/.config/features.yaml.j2` | 138 | `.config/features.yaml` |
| `templates/.config/marketplace.yaml.j2` | 13 | `.config/marketplace.yaml` |
| `templates/.config/repository.yaml.j2` | 24 | `.config/repository.yaml` |
| `templates/.config/workspace.yaml.j2` | 30 | `.config/workspace.yaml` |
| `templates/.github/copilot-instructions.md.j2` | 76 | `.github/copilot-instructions.md` |
| `templates/.github/hooks/hooks.json.j2` | 60 | `.github/hooks/hooks.json` |
| `templates/.github/instructions/instructions.md.j2` | 21 | `.github/instructions/*.md` |
| `templates/.claude/mcp.json.j2` | 43 | `.claude/mcp.json` |
| `templates/.vscode/extensions.json.j2` | 34 | `.vscode/extensions.json` |
| `templates/.vscode/launch.json.j2` | 29 | `.vscode/launch.json` |
| `templates/.vscode/mcp.json.j2` | 60 | `.vscode/mcp.json` |
| `templates/.vscode/settings.json.j2` | 53 | `.vscode/settings.json` |
| `templates/.vscode/tasks.json.j2` | 31 | `.vscode/tasks.json` |
| `templates/.azuredevops/pull_request_template/branches/main.md.j2` | 84 | Azure DevOps PR template |
| `templates/languages/go.yaml.j2` | 106 | Language config: Go |
| `templates/languages/j2.yaml.j2` | 59 | Language config: Jinja2 |
| `templates/languages/json.yaml.j2` | 58 | Language config: JSON |
| `templates/languages/markdown.yaml.j2` | 75 | Language config: Markdown |
| `templates/languages/powershell.yaml.j2` | 92 | Language config: PowerShell |
| `templates/languages/python.yaml.j2` | 127 | Language config: Python |
| `templates/languages/shell.yaml.j2` | 100 | Language config: Shell |
| `templates/languages/sql.yaml.j2` | 55 | Language config: SQL |
| `templates/languages/terraform.yaml.j2` | 100 | Language config: Terraform |
| `templates/languages/typescript.yaml.j2` | 152 | Language config: TypeScript |
| `templates/languages/yaml.yaml.j2` | 58 | Language config: YAML |

### 1.7 Hooks

| File | Content | Status |
|------|---------|--------|
| `hooks.json` | `{"hooks": {}}` | ⚠️ Missing `"version": 1` — defect to fix |

### 1.8 Scripts

None currently. Atlas has no plugin-local scripts.

### 1.9 Schemas

None currently. Atlas references `../../schemas/plugin.base.schema.json` from its manifest.

### 1.10 Atlas Totals

| Resource type | Count | Total lines |
|---------------|-------|-------------|
| Commands | 1 | ~35 |
| Skills | 4 (3 existing + 1 scaffold) | ~499 |
| Agents | 1 | 144 |
| References | 3 + 32 stubs | ~4,039 |
| Templates | 39 + registry (31 existing + 8 scaffold) | ~3,515 |
| Hooks | 1 (empty) | 1 |
| Manifest | 1 | 20 |
| **Total files** | **~81** | **~8,253** |

---

## 2. Apollo (Star Side) — Merged Trio

Apollo merges the former Daedalus (forge), Socrates (probe), and Aristotle (steward) plugins into a single lifecycle management plugin.

### 2.1 Manifest (NEW — to create)

| Field | Value |
|-------|-------|
| **name** | `apollo` |
| **version** | `1.0.0` |
| **description** | 'Plugin lifecycle management for veiled-market — forge, probe, fix, increment, survey, catalog, and grade marketplace plugins across Claude Code and Copilot CLI.' |
| **license** | MIT |
| **author** | Ledermayer |
| **category** | AI Agents |
| **platform** | Both (Claude Code + Copilot CLI) |
| **file** | `commons/plugin.base.json` (to create) |

### 2.2 Commands (3)

| File | Lines | Name | Description | Pattern | Routes to | Origin |
|------|-------|------|-------------|---------|-----------|--------|
| `commands/forge.md` | 44 | `forge` | 'Plugin craftsman for veiled-market. Forges new plugins or resources, edits existing content, assembles generated outputs, and fixes Socrates probe findings.' | A (router) | `forge` → apollo-forge, `edit` → apollo-edit, `assemble` → apollo-assemble, `fix` → apollo-fix | Daedalus |
| `commands/probe.md` | 25 | `probe` | 'Probes a plugin against marketplace-patterns rules using Socratic dialogue. Spawns a scanner, asks targeted questions only where design intent is ambiguous, then writes a structured TODO file and inline summary.' | B (direct) | → apollo-probe | Socrates |
| `commands/steward.md` | 33 | `steward` | 'Plugin lifecycle orchestrator. Classifies Socrates findings, increments versions, surveys cross-plugin health, catalogs inventory, and grades quality.' | A (router) | `classify` → apollo-classify, `increment` → apollo-increment, `survey` → apollo-survey, `catalog` → apollo-catalog, `grade` → apollo-grade | Aristotle |

### 2.3 Skills (10 existing + 3 new knowledge skills)

#### Existing skills (from trio)

| File | Lines | Name | Description | User-invocable | Origin |
|------|-------|------|-------------|----------------|--------|
| `skills/forge/SKILL.md` | 90 | `apollo-forge` | 'Forge a new veiled-market plugin or add a resource to an existing one. Collects inputs, confirms with the user, then spawns the scaffolder agent to create the correct commons/ files.' | false | Daedalus |
| `skills/edit/SKILL.md` | 56 | `apollo-edit` | 'Edit an existing resource in a plugin's commons/ directory. Reads the current file, applies the requested change, and reminds the user to assemble.' | false | Daedalus |
| `skills/assemble/SKILL.md` | 61 | `apollo-assemble` | 'Run the veiled-market build pipeline for one plugin or all plugins. Executes build-platforms.py then finalize.py and reports file counts.' | false | Daedalus |
| `skills/fix/SKILL.md` | 89 | `apollo-fix` | 'Read a Socrates TODO file and apply all auto-fixable findings in priority order. Edits commons/ files, marks fixed items, then reassembles.' | false | Daedalus |
| `skills/probe/SKILL.md` | 168 | `apollo-probe` | 'Probes a plugin against marketplace-patterns rules using Socratic dialogue. Spawns a scanner, asks targeted questions only where design intent is ambiguous, then writes a structured TODO file and inline summary.' | false | Socrates |
| `skills/classify/SKILL.md` | 58 | `apollo-classify` | 'Read a Socrates TODO file, classify findings into auto-fixable and manual groups, prioritise by severity, and output a dispatch plan for /forge fix.' | false | Aristotle |
| `skills/increment/SKILL.md` | 58 | `apollo-increment` | 'Increment a plugin semver version (patch/minor/major), run sync_versions.py or apply manual edits as fallback, then report changed files and the commit command.' | false | Aristotle |
| `skills/survey/SKILL.md` | 52 | `apollo-survey` | 'Survey plugin health across all (or one) veiled-market plugins by spawning the health-checker agent, then surface cross-plugin violations and per-plugin findings.' | false | Aristotle |
| `skills/catalog/SKILL.md` | 47 | `apollo-catalog` | 'Read sources/plugins.json and display a dashboard table of every plugin: version, build status, last probe date, and open finding counts by severity.' | false | Aristotle |
| `skills/grade/SKILL.md` | 73 | `apollo-grade` | 'Run a quality eval loop on a plugin skill: generate test prompts, grade trigger accuracy, analyse description breadth, and suggest an improved description if needed.' | false | Aristotle |

#### New knowledge skills (to create)

| File | Lines (target) | Name | Description | User-invocable | Source knowledge |
|------|----------------|------|-------------|----------------|------------------|
| `skills/author/SKILL.md` | ≤ 150 | `apollo-author` | 'Domain knowledge for authoring hook scripts: event types, stdin/stdout contract, guard patterns, session context injection, and anti-patterns. Trigger on: "add a hook", "create hook script", "preToolUse guard".' | false | plugin-dev `hook-development` (refactored to comply with size limits) |
| `skills/integrate/SKILL.md` | ≤ 150 | `apollo-integrate` | 'Domain knowledge for integrating MCP servers into plugins: .mcp.json structure, server types, auth patterns, and Domain Expert Agent pairing. Trigger on: "add MCP", "configure MCP server", "MCP integration".' | false | plugin-dev `mcp-integration` (refactored) |
| `skills/configure/SKILL.md` | ≤ 150 | `apollo-configure` | 'Domain knowledge for plugin settings: settings.json structure, permission levels, model selection, environment variables, and scope hierarchy. Trigger on: "plugin settings", "configure permissions", "set model".' | false | plugin-dev `plugin-settings` (refactored) |

### 2.4 Agents (3 existing + 1 new)

#### Existing agents (from trio)

| File | Lines | Name | Description | Type | Origin |
|------|-------|------|-------------|------|--------|
| `agents/scaffolder.md` | 131 | `scaffolder` | 'Workflow agent that creates commons/ files for a new plugin or a single resource. Invoked by the apollo-forge skill with structured inputs. Never creates claude/ or copilot/ outputs.' | Workflow Agent | Daedalus |
| `agents/scanner.md` | 137 | `scanner` | (No frontmatter — raw markdown) Structural scanner for Socratic validation. Checks plugin structure, size limits, frontmatter, rules compliance. | Domain Expert Agent | Socrates |
| `agents/health-checker.md` | 90 | `health-checker` | 'Checks a single plugin for structural completeness, build status, description limits, and open findings. Returns a structured JSON report used by the survey skill.' | Workflow Agent | Aristotle |

#### New agent (to create)

| File | Lines (target) | Name | Description | Type | Source pattern |
|------|----------------|------|-------------|------|----------------|
| `agents/agent-creator.md` | ≤ 150 | `agent-creator` | 'Workflow agent that generates agent .md files from a natural-language description. Produces frontmatter (name, description, model, color, tools), system prompt, and triggering examples.' | Workflow Agent | plugin-dev `agent-creator` (adapted for dual-platform) |

### 2.5 References (4 existing + 1 merged)

| File | Lines | Purpose | Origin |
|------|-------|---------|--------|
| `references/resource-types.md` | 136 | 9 resource type table: paths, size limits, frontmatter, build output mapping | Daedalus |
| `references/rules-compact.md` | 86 | 22 rules + 13 anti-patterns quick reference for scanner agent | Socrates |
| `references/dialogue-templates.md` | 40 | Question templates for Phase 2 Socratic dialogue | Socrates |
| `references/version-protocol.md` | 95 | Semver conventions, bump rules, propagation steps | Aristotle |
| `references/shared-steps.md` | ~120 (merged) | Named anchors from trio + copilot monolith pattern: `[read-manifest]`, `[check-names]`, `[resource-locations]`, `[version-bump-rules]` | NEW (merged) |

### 2.6 Scripts — Tier 2 (bundled, distributed with plugin)

#### Eval loop (ported from copilot monolith)

| File | Lines | Purpose | Port source |
|------|-------|---------|-------------|
| `scripts/run_eval.py` | ~312 | Inject skill description, spawn `claude -p` subprocesses, detect triggering from streaming JSON events, return per-query trigger rates | `marketplace/plugins/copilot/scripts/run_eval.py` |
| `scripts/run_loop.py` | ~328 | Full eval+improve loop: train/test split, iterate eval→improve, track best description, log transcripts | `marketplace/plugins/copilot/scripts/run_loop.py` |
| `scripts/improve_description.py` | ~248 | Send failed queries + history to Claude, enforce ≤1024 char limit, avoid overfitting | `marketplace/plugins/copilot/scripts/improve_description.py` |

#### Bash validators (adapted from plugin-dev)

| File | Lines (target) | Purpose | Port source |
|------|----------------|---------|-------------|
| `scripts/validate-agents.sh` | ~150 | Check agent frontmatter: name format, description examples, model validity, color, tools | `plugin-dev/skills/agent-development/scripts/validate-agent.sh` (217 lines, adapted) |
| `scripts/validate-hooks-json.sh` | ~120 | Check hooks.json schema, event names, script references, bash+powershell pair | `plugin-dev/skills/hook-development/scripts/validate-hook-schema.sh` (159 lines, adapted) |

#### Hook scripts (NEW)

| File | Lines (target) | Purpose |
|------|----------------|---------|
| `scripts/guard-build-dirs.sh` | ~30 | `preToolUse` hook: blocks direct writes to `claude/` or `copilot/` directories (enforces build system) |
| `scripts/guard-build-dirs.ps1` | ~30 | PowerShell pair for cross-platform hook support |

### 2.7 Schemas (ported from copilot monolith, NEW)

| File | Lines | Validates | Port source |
|------|-------|-----------|-------------|
| `schemas/hooks.schema.json` | ~89 | `hooks.json`: version const:1, 6 event types, bash+powershell pair per hook | `marketplace/plugins/copilot/schemas/hooks.schema.json` |
| `schemas/skill-frontmatter.schema.json` | ~48 | SKILL.md frontmatter: name, description, user-invocable | `marketplace/plugins/copilot/schemas/skill-frontmatter.schema.json` |
| `schemas/plugin.schema.json` | ~87 | `plugin.json`: name (kebab-case), version (semver), author, component paths | `marketplace/plugins/copilot/schemas/plugin.schema.json` |

### 2.8 Templates — Plugin Resource Templates (ported from copilot monolith, NEW)

| File | Lines | Generates | Port source |
|------|-------|-----------|-------------|
| `templates/templates.json` | ~160 | Template registry: names, paths, variables, output patterns | `marketplace/plugins/copilot/templates/templates.json` |
| `templates/resources/SKILL.md.j2` | ~102 | Skill file scaffold | `marketplace/plugins/copilot/templates/resources/skills/SKILL.md.j2` |
| `templates/resources/agent.md.j2` | ~111 | Agent file scaffold | `marketplace/plugins/copilot/templates/resources/agents/agent.md.j2` |
| `templates/resources/command.md.j2` | ~40 | Command file scaffold | `marketplace/plugins/copilot/templates/resources/commands/command.md.j2` |
| `templates/resources/plugin.json.j2` | ~44 | Plugin manifest scaffold | `marketplace/plugins/copilot/templates/resources/plugins/plugin.json.j2` |
| `templates/resources/hooks.json.j2` | ~21 | Hooks config scaffold | `marketplace/plugins/copilot/templates/resources/hooks/hooks.json.j2` |
| `templates/resources/hook.sh.j2` | ~16 | Hook bash script scaffold | `marketplace/plugins/copilot/templates/resources/hooks/hook.sh.j2` |
| `templates/resources/hook.ps1.j2` | ~17 | Hook powershell script scaffold | `marketplace/plugins/copilot/templates/resources/hooks/hook.ps1.j2` |
| `templates/resources/mcp.json.j2` | ~27 | MCP config scaffold | `marketplace/plugins/copilot/templates/resources/plugins/mcp.json.j2` |
| `templates/resources/README.md.j2` | ~60 | Plugin README scaffold | `marketplace/plugins/copilot/templates/resources/README.md.j2` |

### 2.9 Hooks

| File | Content | Status |
|------|---------|--------|
| `hooks.json` | `{"version": 1, "hooks": {"preToolUse": [...]}}` | NEW — wires `guard-build-dirs.sh`/`.ps1` |

### 2.10 Apollo Totals

| Resource type | Count | Total lines (approx) |
|---------------|-------|----------------------|
| Commands | 3 | 102 |
| Skills (existing) | 10 | 752 |
| Skills (new) | 3 | ~450 |
| Agents (existing) | 3 | 358 |
| Agents (new) | 1 | ~150 |
| References | 5 | ~477 |
| Scripts (eval loop) | 3 | ~888 |
| Scripts (validators) | 2 | ~270 |
| Scripts (hooks) | 2 | ~60 |
| Schemas | 3 | ~224 |
| Templates | 10 + registry | ~758 |
| Hooks | 1 (wired) | ~10 |
| Manifest | 1 | ~20 |
| **Total files** | **~47** | **~4,519** |

---

## 3. Repo-Level Infrastructure (Tier 1 — Not Distributed)

These scripts and schemas live at `veiled-market/` root. They are development-time tools that operate on the full repository. NOT bundled with any plugin.

### 3.1 Build & Validation Scripts

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/build-platforms.py` | 348 | Generate `claude/` + `copilot/` from `commons/` for each plugin |
| `scripts/finalize.py` | 358 | Promote draft plugins, bump versions, generate CHANGELOG, regen marketplace manifests |
| `scripts/validate_commons.py` | 354 | Structural validator: file presence, plugin.base.json schema, frontmatter, wiring, description limits |
| `scripts/sync_versions.py` | 241 | Bump/set semver for a plugin, propagate to all generated manifests |
| `scripts/scaffold_plugin.py` | 224 | Scaffold new `plugins/<name>/commons/` directory tree from scratch |
| `scripts/render_template.py` | ~264 | Jinja2 template renderer (to port from copilot monolith) |

### 3.2 Marketplace Pipeline Scripts

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/discover.py` | 548 | Query skill/plugin marketplaces, create GitHub issues for discovered resources |
| `scripts/evaluate.py` | 602 | Score discovered skills using GitHub Models API, compile recommended set |
| `scripts/enrich.py` | 141 | AI-powered enrichment: merge best elements from draft plugin.json files |
| `scripts/compose.py` | 400 | Generate filtered plugin.json based on language/platform tags |
| `scripts/registry.py` | 371 | Read/write skill evaluation registry |

### 3.3 Schemas

| File | Lines | Purpose |
|------|-------|---------|
| `schemas/plugin.base.schema.json` | 44 | Validates `plugin.base.json` (commons manifest) |
| `schemas/marketplace.schema.json` | 220 | Validates `marketplace.json` (plugin registry) |
| `schemas/marketplaces.schema.json` | 101 | Validates `marketplaces.json` |
| `schemas/plugins.shema.json` | 53 | Validates `plugins.json` (source registry) |
| `schemas/registry.schema.json` | 220 | Validates `registry.json` (eval registry) |

### 3.4 Build System Extension Required

`build-platforms.py` currently copies: `skills/`, `agents/`, `commands/`, `hooks.json`, `.mcp.json`, `references/`.

Must be extended to also copy: **`scripts/`**, **`templates/`**, **`schemas/`**.

This ensures Apollo's runtime scripts, resource templates, and validation schemas are distributed to the installed plugin's `claude/` and `copilot/` output directories.

---

## 4. Porting Inventory — What Comes From Where

### 4.1 From Copilot Monolith → Apollo

| Source file | Lines | Destination in Apollo | Category |
|-------------|-------|-----------------------|----------|
| `copilot/scripts/run_eval.py` | 312 | `scripts/run_eval.py` | Eval loop |
| `copilot/scripts/run_loop.py` | 328 | `scripts/run_loop.py` | Eval loop |
| `copilot/scripts/improve_description.py` | 248 | `scripts/improve_description.py` | Eval loop |
| `copilot/scripts/render_template.py` | 264 | `veiled-market/scripts/render_template.py` (Tier 1) | Build tool |
| `copilot/schemas/hooks.schema.json` | 89 | `schemas/hooks.schema.json` | Validation |
| `copilot/schemas/skill-frontmatter.schema.json` | 48 | `schemas/skill-frontmatter.schema.json` | Validation |
| `copilot/schemas/plugin.schema.json` | 87 | `schemas/plugin.schema.json` | Validation |
| `copilot/templates/templates.json` | 160 | `templates/templates.json` | Scaffolding |
| `copilot/templates/resources/*.j2` | 10 files | `templates/resources/*.j2` | Scaffolding |

### 4.2 From Plugin-Dev → Apollo (adapted, not copied verbatim)

| Source file | Lines | Destination in Apollo | Adaptation needed |
|-------------|-------|-----------------------|-------------------|
| `plugin-dev/skills/agent-development/scripts/validate-agent.sh` | 217 | `scripts/validate-agents.sh` | Adapt to dual-platform naming, remove Claude-Code-only checks |
| `plugin-dev/skills/hook-development/scripts/validate-hook-schema.sh` | 159 | `scripts/validate-hooks-json.sh` | Adapt event names for both platforms |
| `plugin-dev/skills/hook-development/` (knowledge) | 712 | `skills/hook-authoring/SKILL.md` (≤150 lines) + `references/` | Refactor: extract tables → references, comply with size limits |
| `plugin-dev/skills/mcp-integration/` (knowledge) | 554 | `skills/mcp-authoring/SKILL.md` (≤150 lines) + `references/` | Refactor: extract tables → references, comply with size limits |
| `plugin-dev/skills/plugin-settings/` (knowledge) | 544 | `skills/settings-authoring/SKILL.md` (≤150 lines) + `references/` | Refactor: extract tables → references, comply with size limits |
| `plugin-dev/agents/agent-creator.md` | 176 | `agents/agent-creator.md` (≤150 lines) | Adapt for dual-platform agent format |

### 4.3 From Trio → Apollo (move, minimal changes)

| Origin plugin | Files moved | Changes needed |
|---------------|-------------|----------------|
| **Daedalus** | 4 skills, 1 agent, 1 command, 1 reference | Rename skill dirs: `create` → `forge`, `update` → `edit`, `build` → `assemble`, `remediate` → `fix`. Rename frontmatter names to `apollo-*`. Update command routing. |
| **Socrates** | 1 skill, 1 agent, 1 command, 2 references | Rename skill dir: `socrates` → `probe`. Rename frontmatter to `apollo-probe`. Fix scanner.md: add frontmatter. |
| **Aristotle** | 5 skills, 1 agent, 1 command, 1 reference | Rename skill dirs: `triage` → `classify`, `bump` → `increment`, `audit` → `survey`, `inventory` → `catalog`, `review` → `grade`. Rename frontmatter to `apollo-*`. Update command routing. |

---

## 5. Data Flow Contracts

### 5.1 Fix-Type Routing (intra-plugin, unchanged)

```
/probe <plugin>
  → apollo-probe skill
    → scanner agent
      → writes .todos/socrates/<plugin>-YYYYMMDD.md

/steward classify <plugin>
  → apollo-classify skill
    → reads .todos/socrates/<plugin>-YYYYMMDD.md
    → classifies: auto-fixable vs manual
    → suggests: /forge fix <plugin>

/forge fix <plugin>
  → apollo-fix skill
    → reads .todos/socrates/<plugin>-YYYYMMDD.md
    → applies auto-fixable findings (fix-type ≠ manual)
    → marks [x] on success, appends FAILED on failure
    → reassembles with /forge assemble
```

### 5.2 Fix-Type Values

| Value | Meaning | Remediation action |
|-------|---------|-------------------|
| `edit-content` | Line limit, description, wrong body | Edit file content |
| `edit-structure` | File needs renaming or moving | Rename/move file |
| `add-file` | Required file missing | Create stub |
| `delete-file` | Orphaned or prohibited file | Delete file |
| `config-change` | hooks.json or plugin.base.json edit | Edit JSON config |
| `manual` | Complex architectural decision | **Skip** — escalate to human |

### 5.3 Health-Checker JSON Output

```json
{
  "plugin": "<name>",
  "version": "<semver>",
  "built": true,
  "violations": 0,
  "anti_patterns": 0,
  "improvements": 0,
  "last_probed": "YYYY-MM-DD",
  "issues": []
}
```

---

## 6. Cross-Reference: Resource Type Compliance

Every file in both plugins must comply with MARKETPLACE.md size rules:

| Resource type | Hard limit | Recommended | Apollo max | Atlas max | Status |
|---------------|-----------|-------------|------------|-----------|--------|
| Command | ≤ 66 lines | ≤ 44 | 44 (forge.md) | ~35 (atlas.md) | ✅ |
| Procedural Skill | ≤ 500 lines | ≤ 200 | 168 (apollo-probe) | ~180 (atlas-scaffold) | ✅ |
| Knowledge Skill | ≤ 500 lines | ≤ 174 | ≤ 150 (new skills) | N/A | ✅ (target) |
| Workflow Agent | ≤ 200 lines | ≤ 100 | 137 (scanner) | 144 (workspace-scanner) | ✅ |
| Reference | No hard limit | varies | 136 (resource-types) | 253 (git.instructions.j2) | ✅ |
| Script | No hard limit | ≤ 400 | ~328 (run_loop.py) | N/A | ✅ |
| Template | No hard limit | ≤ 120 | ~160 (templates.json) | 816 (templates.json) | ✅ |
| Hooks config | Must have version:1 | — | version:1 ✅ | ⚠️ Missing | Fix needed |

---

## 7. Grand Totals

| Metric | Atlas | Apollo | Repo infra | Total |
|--------|-------|--------|------------|-------|
| Commands | 1 | 3 | — | 4 |
| Skills | 4 (3+1 scaffold) | 13 (10+3) | — | 17 |
| Agents | 1 | 4 (3+1) | — | 5 |
| References | 35 (3+32 stubs) | 5 | — | 40 |
| Templates | 40 (31+8 scaffold+registry) | 11 | — | 51 |
| Scripts | 0 | 7 (3+2+2) | 11 | 18 |
| Schemas | 0 | 3 | 5 | 8 |
| Hooks files | 1 | 1 | — | 2 |
| Manifests | 1 | 1 | — | 2 |
| **Total files** | **~81** | **~47** | **~16** | **~144** |
| **Total lines** | **~8,253** | **~4,519** | **~4,863** | **~17,635** |
