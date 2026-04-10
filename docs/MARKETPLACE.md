# Marketplace Resource Ruleset: Authoritative Decision Guide

This is the authoritative, multi-platform ruleset for the AI Tools Marketplace. Every design
decision about what resource to create, where to put it, and how large it may be is governed by
the rules in this document.

> **Platform scope:** This ruleset covers **Claude Code** and **GitHub Copilot CLI**. Rules are
> presented in a platform-neutral format where possible. Where behavior diverges, a comparison
> table is provided. The document is structured to accommodate future shells (Codex CLI, Gemini CLI)
> by adding columns.

> **Note:** This document is a Level-3 reference (read on demand, not a skill), so its length is
> acceptable. Do not use it as a model for SKILL.md sizing.

> **Notation:** Claims are marked as follows:
> - No marker = platform-documented behavior with source link
> - 🏠 = House convention (our design standard, not platform-documented)
> - 👁️ = Observed behavior (empirically verified but not in official docs)
>
> Last verified against official docs: April 2026

### Official Documentation Sources

| Platform | Documentation Root | Key References |
|----------|-------------------|----------------|
| **Claude Code** | [code.claude.com/docs/en](https://code.claude.com/docs/en) | [Plugins](https://code.claude.com/docs/en/plugins) · [Plugin Reference](https://code.claude.com/docs/en/plugins-reference) · [Skills](https://code.claude.com/docs/en/skills) · [Hooks](https://code.claude.com/docs/en/hooks) · [Marketplace](https://code.claude.com/docs/en/discover-plugins) · [Creating Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) · [Subagents](https://code.claude.com/docs/en/sub-agents) · [Settings](https://code.claude.com/docs/en/settings) |
| **Copilot CLI** | [docs.github.com/en/copilot](https://docs.github.com/en/copilot) | [About Plugins](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins) · [Plugin Reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) · [Creating Plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) · [Creating Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills) · [Finding Plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-finding-installing) · [Custom Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot) |

---

## Table of Contents

- [1. The Cost Hierarchy — Read This First](#1-the-cost-hierarchy--read-this-first)
  - [1.1 Token Cost Model](#11-token-cost-model)
  - [1.2 Four-Level Loading Model](#12-four-level-loading-model)
  - [1.3 Cost Design Rules](#13-cost-design-rules)
  - [1.4 Instructions Files vs Knowledge Skills — Choosing the Right Layer](#14-instructions-files-vs-knowledge-skills--choosing-the-right-layer)
- [2. Resource Type Reference](#2-resource-type-reference)
  - [2.1 Plugin](#21-plugin)
  - [2.2 Command](#22-command)
  - [2.3 Procedural Skill](#23-procedural-skill)
  - [2.4 Knowledge Skill](#24-knowledge-skill)
  - [2.5 Workflow Agent](#25-workflow-agent)
  - [2.6 Domain Expert Agent](#26-domain-expert-agent)
  - [2.7 Reference](#27-reference)
  - [2.8 Script](#28-script)
  - [2.9 Hook](#29-hook)
  - [2.10 MCP Config](#210-mcp-config)
  - [2.11 Template](#211-template)
- [3. Standard Rules](#3-standard-rules)
- [4. Anti-Patterns](#4-anti-patterns)
- [5. Cost-Efficiency Playbook](#5-cost-efficiency-playbook)
  - [5.1 Universal Rules (Apply to All Platforms)](#51-universal-rules-apply-to-all-platforms)
  - [5.2 Platform-Specific Optimization](#52-platform-specific-optimization)
  - [5.3 Pattern A vs Pattern B Cost Comparison](#53-pattern-a-vs-pattern-b-cost-comparison)
- [6. Platform Plugin Architecture](#6-platform-plugin-architecture)
  - [6.1 Plugin Directory Structure](#61-plugin-directory-structure)
  - [6.2 Plugin Discovery and Registration](#62-plugin-discovery-and-registration)
  - [6.3 Plugin Source Types](#63-plugin-source-types)
  - [6.4 Skill Discovery and Loading Order](#64-skill-discovery-and-loading-order)
  - [6.5 Installation Scopes](#65-installation-scopes)
- [7. Summary Decision Tree](#7-summary-decision-tree)
- [8. Quick Reference Card](#8-quick-reference-card)
- [9. Plugin and Marketplace Setup](#9-plugin-and-marketplace-setup)
  - [9.1 Local Plugin Install](#91-local-plugin-install)
  - [9.2 Marketplace Setup](#92-marketplace-setup)
- [10. TODO File Standard](#10-todo-file-standard)

---

## 1. The Cost Hierarchy — Read This First

Every resource you add to the marketplace has a token cost paid by the AI's context window.
Understanding the cost model is the single most important factor in marketplace design — an
oversized SKILL.md degrades every session that triggers it.

### 1.1 Token Cost Model

> **Estimation rule of thumb:** 1 line ≈ 12 tokens. This is an empirical approximation; actual
> tokenization varies by content density.

| Resource | Tokens consumed | When the cost is paid |
|---|---|---|
| **Project context file** | **1 line = ~12 tokens, every session** | **ALWAYS — unconditional, every session forever** |
| **Path-scoped instructions** | **60–248 lines = 720–2,976 tokens** | **When matching file pattern is active** |
| Skill frontmatter (name + description only) | ~36 tokens | **ALWAYS** — every session, every plugin loaded |
| Command `.md` — thin router (≤66 lines) | 480–792 tokens | Only when command invoked |
| **Large command file (>200 lines, inline logic)** | **2,400–5,000+ tokens** | **Every invocation — all branches load** |
| Knowledge skill SKILL.md (135–174 lines) | 1,620–2,088 tokens | Every time description triggers — even passively |
| Procedural skill SKILL.md (66–113 lines) | 792–1,356 tokens | Every time the skill is explicitly invoked |
| Procedural skill SKILL.md (>300 lines) | 3,600–5,508 tokens | Every invocation — **high-cost signal** |
| Agent `.md` body (52–280 lines) | 624–3,360 tokens | **ONLY** when explicitly spawned |
| Reference `.md` (103–430 lines) | 1,236–5,160 tokens | **ONLY** when explicitly read |
| Script (Python / Bash) | **0 tokens** | Never — executed by the OS |
| Template (`.j2`, `.md`, `.yaml`, etc.) 🏠 | **0 tokens** | Never — rendered by command/skill |
| MCP config | **0 tokens** | Never — connection metadata |

### 1.2 Four-Level Loading Model

Both platforms use a progressive loading model. Design every resource with its level in mind:

| Level | Name | What's loaded | Cost profile |
|-------|------|--------------|-------------|
| **Level 0** | Project context (always loaded) | Project-wide instructions file | Most expensive — paid on every session unconditionally |
| **Level 1** | Plugin metadata (always loaded) | Skill frontmatter (name + description) | ~36 tokens per skill, every session |
| **Level 2** | Triggered load | SKILL.md body, command body, path-scoped instructions | Paid when skill activates, command invoked, or file pattern matches |
| **Level 3** | Explicit read | References, scripts, templates, agents | Zero cost until a Level-2 resource explicitly reads them |

**Platform comparison for Level 0:**

| Aspect | Claude Code | Copilot CLI |
|--------|------------|-------------|
| **Level-0 file** | `CLAUDE.md` ([docs](https://code.claude.com/docs/en/memory)) | `.github/copilot-instructions.md` ([docs](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)) |
| **Recommended limit** | ≤ 200 lines (~2,400 tokens) — [source](https://code.claude.com/docs/en/memory) 🏠 We target ≤ 150 lines for stricter cost control | ≤ 150 lines (~1,800 tokens) 🏠 |
| **Also reads** | `.claude/rules/*.md`, parent `CLAUDE.md` files | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` (as fallbacks) |

**Platform comparison for Level 1:**

| Aspect | Claude Code | Copilot CLI |
|--------|------------|-------------|
| **What loads** | Skill `description` field (truncated at 250 chars in listing — [source](https://code.claude.com/docs/en/skills)) | Skill `description` field |
| **`disable-model-invocation: true`** | Description **NOT** loaded into context (zero Level-1 cost) — [source](https://code.claude.com/docs/en/skills) | **Not supported** — all descriptions always load |
| **Cost elimination** | Use `disable-model-invocation: true` for user-only workflows | No equivalent — use `workflow.md` rename + command router pattern |

**Platform comparison for Level 2 (path-scoped instructions):**

| Aspect | Claude Code | Copilot CLI |
|--------|------------|-------------|
| **File** | `.claude/rules/*.md` with `paths:` frontmatter ([docs](https://code.claude.com/docs/en/memory#path-specific-rules)) | `.github/instructions/*.instructions.md` with `applyTo:` frontmatter ([docs](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot#creating-path-specific-custom-instructions)) |
| **Trigger** | File matching glob pattern is being worked on | File matching `applyTo` pattern is open in editor |
| **Selectivity** | Path-glob gated | File-type gated |

### 1.3 Cost Design Rules

> **Rule A:** If information can live at Level 3, it MUST NOT be inlined into a Level-2 resource.

> **Rule B:** If a Level-2 resource exceeds 300 lines, it MUST be split or its detail extracted to Level 3.

> **Rule C:** The Level-0 file MUST NOT contain file-type coding standards — those belong in
> path-scoped instruction files (`.claude/rules/` or `.github/instructions/`).

### 1.4 Instructions Files vs Knowledge Skills — Choosing the Right Layer

Both instruction files and Knowledge Skills enrich AI context with domain knowledge. They are
NOT interchangeable. Choosing the wrong one pays the wrong cost at the wrong time.

Both platforms have instruction files — they just use different filenames, locations, and scoping
mechanisms.

#### Instruction file comparison

| Aspect | Claude Code ([source](https://code.claude.com/docs/en/memory)) | Copilot CLI ([source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)) |
|--------|------------|-------------|
| **Level-0 project file** | `CLAUDE.md` or `.claude/CLAUDE.md` at project root | `.github/copilot-instructions.md` + `AGENTS.md` at repo root |
| **User/personal file** | `~/.claude/CLAUDE.md` | `$HOME/.copilot/copilot-instructions.md` |
| **Local (gitignored)** | `CLAUDE.local.md` at project root | — (not supported natively) |
| **Org-managed policy** | OS-specific path (e.g. macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`) | — (not supported natively) |
| **Path-scoped rules** | `.claude/rules/*.md` with `paths:` frontmatter — [source](https://code.claude.com/docs/en/memory#path-specific-rules) | `.github/instructions/*.instructions.md` with `applyTo:` frontmatter — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions#creating-path-specific-custom-instructions) |
| **Path glob syntax** | `paths: ["src/**/*.ts"]` (YAML array) | `applyTo: "src/**/*.ts"` (comma-separated string) |
| **Subdirectory loading** | `CLAUDE.md` in subdirs loads on-demand when files are read there | `AGENTS.md` at repo root (primary) + CWD + `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` paths (additional) — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions#agent-instructions) |
| **Cross-file import** | `@path/to/file` syntax in CLAUDE.md (max 5 hops) — [source](https://code.claude.com/docs/en/memory#import-additional-files) | — (not supported) |
| **Compatibility reads** | — | Also reads `CLAUDE.md` and `GEMINI.md` at repo root |
| **Extra dirs env var** | `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` + `--add-dir` | `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` (comma-separated paths) |
| **Auto memory** | ✅ Claude writes own notes (first 200 lines / 25 KB) — [source](https://code.claude.com/docs/en/memory#auto-memory) | — (not supported) |
| **Disable flag** | `--no-custom-instructions` | 👁️ `--no-custom-instructions` |

> **Cross-platform tip:** Copilot CLI reads `CLAUDE.md` at the repo root for compatibility
> ([source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions#agent-instructions)).
> Claude Code reads `CLAUDE.md` natively. This enables three setup strategies:

#### Cross-platform instruction strategies

| | Claude-only | Copilot-only | Hybrid (recommended) |
|---|---|---|---|
| **Files created** | `CLAUDE.md` | `.github/copilot-instructions.md` + `AGENTS.md` | `CLAUDE.md` + `.github/copilot-instructions.md` |
| **Who reads what** | Claude reads `CLAUDE.md` | Copilot reads both files | Claude reads `CLAUDE.md`; Copilot reads `CLAUDE.md` **+** `.github/copilot-instructions.md` |
| **Path-scoped rules** | `.claude/rules/*.md` | `.github/instructions/*.instructions.md` | Both dirs (each shell reads only its own) |
| **Personal/user file** | `~/.claude/CLAUDE.md` | `$HOME/.copilot/copilot-instructions.md` | Both (each shell reads only its own) |
| **Shared instructions** | Everything in `CLAUDE.md` | Everything in `copilot-instructions.md` | Common rules go in `CLAUDE.md` (both read it) |
| **Platform overrides** | N/A | N/A | Copilot-specific rules go in `.github/copilot-instructions.md` (Claude ignores it) |

<details>
<summary><strong>Hybrid mode — file tree example</strong> (click to expand)</summary>

```
my-project/
├── CLAUDE.md                          # ← Shared: both shells load this
├── .github/
│   ├── copilot-instructions.md        # ← Copilot-only overrides/additions
│   └── instructions/
│       └── terraform.instructions.md  # ← Copilot path-scoped (applyTo: "**/*.tf")
├── .claude/
│   ├── CLAUDE.md                      # ← Claude-only additions (optional)
│   └── rules/
│       └── terraform.md               # ← Claude path-scoped (paths: ["**/*.tf"])
└── CLAUDE.local.md                    # ← Claude-only, gitignored, personal
```

</details>

<details>
<summary><strong>Hybrid mode — override example</strong> (click to expand)</summary>

**`CLAUDE.md`** (shared — both shells read this):
```markdown
# Project Standards

- Use Go 1.24+
- Run `make lint` before committing
- All public functions must have doc comments
- Prefer table-driven tests
```

**`.github/copilot-instructions.md`** (Copilot-only addition):
```markdown
# Copilot-Specific

- When using the task tool, prefer mode: "background" for builds
- Use /skills list to discover available skills before starting complex tasks
- Commit messages must include a Co-authored-by trailer for Copilot
```

**`.claude/CLAUDE.md`** (Claude-only addition, optional):
```markdown
# Claude-Specific

- Use ultrathink for architectural decisions
- Prefer plan mode (Shift+Tab) for multi-file changes
- Auto-memory is enabled — learn from corrections
```

**How override works:**
- Claude Code loads: `CLAUDE.md` (root) → `.claude/CLAUDE.md` → `CLAUDE.local.md`. It never sees `.github/copilot-instructions.md`.
- Copilot CLI loads: `CLAUDE.md` (root, as compatibility read) → `.github/copilot-instructions.md`. It never sees `.claude/CLAUDE.md`.
- Shared rules in `CLAUDE.md` apply to both. Platform-specific rules only reach their target shell.
- If instructions conflict between `CLAUDE.md` and `.github/copilot-instructions.md`, Copilot treats both as primary — last-read wins (non-deterministic). **Avoid contradictions; use additions, not overrides.**
</details>

#### Cost tiers (universal)

| Mechanism | Trigger | Selectivity | Cost per session |
|---|---|---|---|
| Level-0 project file | Always, unconditional | None | 1,800+ tokens × every session |
| Path-scoped instructions | Matching file pattern active | File-type gated | 720–2,976 tokens × when active |
| Knowledge Skill (`user-invocable: false`) | Description semantically matches user query | Query-intent gated | 1,620–2,088 tokens × on trigger |

#### Content placement rules

- **"Should the AI follow this rule when WRITING this file type?"** → Path-scoped instructions (`.claude/rules/` or `.github/instructions/`)
- **"Should the AI know this when REVIEWING or ANALYSING this domain?"** → Knowledge Skill
- **"Does the AI need this on EVERY session?"** → Level-0 project file (if ≤150 total lines)
- **"Is this detail only needed on demand?"** → Reference (Level 3)

<details>
<summary><strong>Claude Code path-scoped rule example</strong> (click to expand)</summary>

```yaml
# .claude/rules/api-design.md
---
paths:
  - "src/api/**/*.ts"
  - "src/api/**/*.tsx"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format from `src/api/errors.ts`
```

Source: [Claude Code — Path-specific rules](https://code.claude.com/docs/en/memory#path-specific-rules)
</details>

<details>
<summary><strong>Copilot CLI path-scoped instruction example</strong> (click to expand)</summary>

```yaml
# .github/instructions/api-design.instructions.md
---
applyTo: "src/api/**/*.ts,src/api/**/*.tsx"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format from `src/api/errors.ts`
```

Source: [Copilot CLI — Path-specific instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions#creating-path-specific-custom-instructions)
</details>

---

## 2. Resource Type Reference

### 2.1 Plugin

**Definition:** A named, installable unit containing commands, skills, agents, hooks, and
optional MCP/LSP config.

**CREATE WHEN:**
- You have a coherent domain that a user would think of as a distinct tool
- The domain has at least one user-facing command and at least one skill
- The domain requires hooks or MCP that would be inappropriate in an existing plugin

**DO NOT CREATE WHEN:**
- You have only utility agents or references → add to existing platform plugin
- You have a single skill with no command → add to the closest domain plugin
- You are duplicating an existing plugin's domain → extend the existing plugin

**Token cost tier:** Structural only — cost is paid by child resources.

**Manifest comparison:**

| Aspect | Claude Code ([source](https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema)) | Copilot CLI ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#pluginjson)) |
|--------|------------|-------------|
| **Manifest file** | `.claude-plugin/plugin.json` | `.plugin/plugin.json` → `plugin.json` → `.github/plugin/plugin.json` → `.claude-plugin/plugin.json` (checked in order — [source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#file-locations)) |
| **Required field** | `name` only (manifest itself is optional) | `name` only |
| **`skills` key** | Normal field — specifies custom skills directory path. Accepts string or array. | Normal field — specifies skills directory path. Accepts string or array. |
| **`commands` key** | Custom command file paths (string or array) | Custom command directory paths (string or array) |
| **`hooks` key** | Path(s) to hooks file, inline object, or array of paths | Path to hooks file or inline object |
| **`mcpServers`** | Path(s) to MCP config, inline object, or array | Path to MCP config or inline object |
| **`lspServers`** | Path(s) to LSP config, inline object, or array | Path to LSP config or inline object |
| **`agents`** | Custom agent file paths | Agent directories (`.agent.md` files) |
| **`userConfig`** | ✅ Prompts user at enable time | ❌ Not supported |
| **`channels`** | ✅ Message injection channels | ❌ Not supported |
| **`outputStyles`** | ✅ Custom response formatting | ❌ Not supported |

<details>
<summary><strong>Claude Code plugin.json schema</strong> (click to expand)</summary>

```json
{
  "name": "plugin-name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "skills": "./custom/skills/",
  "commands": ["./custom/commands/special.md"],
  "agents": "./custom/agents/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/",
  "userConfig": {
    "api_endpoint": {
      "description": "Your API endpoint",
      "sensitive": false
    }
  }
}
```

Source: [Plugin Reference — Complete schema](https://code.claude.com/docs/en/plugins-reference#complete-schema)
</details>

<details>
<summary><strong>Copilot CLI plugin.json schema</strong> (click to expand)</summary>

```json
{
  "name": "plugin-name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "category": "development",
  "tags": ["tag1"],
  "agents": "agents/",
  "skills": ["skills/", "extra-skills/"],
  "commands": "commands/",
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json",
  "lspServers": "lsp.json"
}
```

Source: [CLI Plugin Reference — plugin.json](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#pluginjson)
</details>

---

### 2.2 Command

**Definition:** A thin router markdown file in `commands/` that maps slash-command invocations
to skill or agent calls. Contains no domain logic — only routing and argument parsing.

**Two valid patterns:**

| Pattern | Use when | Token cost |
|---------|----------|-----------|
| **A — Single router + skills** (`/plugin action`) | Actions share a namespace + common sub-procedures | 480 router + skill-body per action |
| **B — Multiple focused commands** (`/command`) | Independent entry points, no shared workflow | 600–792 per command |

**DO NOT** inline domain logic in command files. The ≤66 line limit is a mechanical test for this.

**Platform comparison:**

| Aspect | Claude Code | Copilot CLI |
|--------|------------|-------------|
| **Standalone skill invocation** | `/skill-name` (flat) — [source](https://code.claude.com/docs/en/skills) | `/skill-name` (flat, first-found-wins) — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills#using-agent-skills) |
| **Plugin command invocation** | `/plugin-name:command-name` (namespaced) — [source](https://code.claude.com/docs/en/skills#where-skills-live) | `/plugin-name:command-name` (namespaced) |
| **Plugin skill invocation** | `/plugin-name:skill-name` (namespaced) — [source](https://code.claude.com/docs/en/skills#where-skills-live) | `/skill-name` (no namespace; first-found-wins by name) — [source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#loading-order-and-precedence) |
| **Knowledge skill trigger** | Auto-invoked when description matches user query | Auto-invoked when description matches user query |
| **Name collision** | Skill wins over command if same name; plugin skills namespaced as `plugin:skill` (no conflict) ([source](https://code.claude.com/docs/en/skills#where-skills-live)) | First-found-wins for skills (project > personal > plugin); skills override commands ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#loading-order-and-precedence)) |
| **Precedence** | enterprise > personal > project; skill > command of same name | Project-level > plugin-level (first-found-wins for skills) |

**Size limit:** MUST be ≤ 66 lines. Exceeding this is evidence of inline domain logic.

---

### 2.3 Procedural Skill

**Definition:** A SKILL.md with numbered steps and interactive prompts guiding a workflow.

**CREATE WHEN:** A user triggers a multi-step workflow (init, update, validate).

**Size limit:** MUST be ≤ 200 lines. Extract sub-procedures to `references/`.

**Token cost tier:** LOW–MEDIUM (792–2,400 tokens, per invocation).

---

### 2.4 Knowledge Skill

**Definition:** A SKILL.md with no numbered steps — a domain encyclopedia that enriches AI
context when description matching fires.

**CREATE WHEN:** Dense domain rules or best practices the AI needs passively.

**CRITICAL:** Knowledge skills pay their full token cost EVERY TIME their description triggers.
Keep them focused.

**Token cost tier:** MEDIUM (1,620–2,088 tokens, paid passively on every trigger).

**Platform comparison for invocation control:**

| Frontmatter | Claude Code | Copilot CLI |
|-------------|------------|-------------|
| `user-invocable: true` (default) | User types `/skill`; Claude auto-invokes; description in context | User types `/plugin:skill`; Copilot auto-invokes; description in context |
| `user-invocable: false` | No user slash command; Claude still auto-invokes; description in context | 👁️ Hidden from `/skills list`; may still auto-trigger (not in official docs) |
| `disable-model-invocation: true` | User types `/skill`; Claude CANNOT auto-invoke; **description NOT in context** (zero Level-1 cost) — [source](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill) | **Not supported** |
| Both `false` + `true` | Neither user nor Claude can invoke; description not in context | Not possible |

> **Copilot SKILL.md frontmatter:** Official docs document `name` (required), `description` (required), `allowed-tools`, and `license` as frontmatter fields ([source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills)). The `user-invocable` field is part of the [Agent Skills](https://agentskills.io) standard which Copilot supports, but its behavior in Copilot is 👁️ observed, not officially documented.

#### SKILL.md Frontmatter Schema (three-layer model)

SKILL.md frontmatter follows the [Agent Skills](https://agentskills.io) open standard, with
platform-specific extensions. Fields are layered:

| Field | Agent Skills Standard | Claude Code | Copilot CLI |
|-------|-----------------------|-------------|-------------|
| `name` | ✅ Required (max 64 chars) — [source](https://agentskills.io/specification) | Optional (uses dir name if omitted) — [source](https://code.claude.com/docs/en/skills#frontmatter-reference) | ✅ Required — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills) |
| `description` | ✅ Required (max 1024 chars) | Recommended (truncated at 250 chars in listing) | ✅ Required |
| `license` | Optional | ✅ | ✅ |
| `compatibility` | Optional (max 500 chars) | ✅ | 👁️ Works (used in [awesome-copilot](https://github.com/github/awesome-copilot), not in official docs) |
| `metadata` | Optional (string→string map) | ✅ | 👁️ Works (confirmed in practice, not in official docs) |
| `allowed-tools` | Optional (experimental) | ✅ Space-separated or YAML list | ✅ — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills#enabling-a-skill-to-run-a-script) |
| `argument-hint` | — | ✅ Autocomplete hint, e.g. `[issue-number]` | — |
| `disable-model-invocation` | — | ✅ `true` = manual only; description NOT in context | — |
| `user-invocable` | — | ✅ `false` = hide from `/` menu | 👁️ Observed (hidden from `/skills list`) |
| `model` | — | ✅ Model override when skill is active | — |
| `effort` | — | ✅ `low` / `medium` / `high` / `max` | — |
| `context` | — | ✅ `fork` = run in subagent | — |
| `agent` | — | ✅ Subagent type when `context: fork` | — |
| `hooks` | — | ✅ Hooks scoped to skill lifecycle — [source](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents) | — |
| `paths` | — | ✅ Glob patterns limiting auto-activation | — |
| `shell` | — | ✅ `bash` (default) or `powershell` | — |

> **Legend:** ✅ = officially documented, 👁️ = works in practice but not in official docs, — = not supported

<details>
<summary><strong>Claude Code SKILL.md example</strong> (click to expand)</summary>

```yaml
---
name: my-skill
description: What this skill does and when to use it
license: MIT
compatibility: Requires Node.js 18+
metadata:
  author: your-name
  version: "1.0.0"
argument-hint: "[target] [options]"
disable-model-invocation: true
user-invocable: true
allowed-tools: Read Grep Bash(npm test *)
model: sonnet
effort: high
context: fork
agent: code-review
hooks:
  PreToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: "${CLAUDE_SKILL_DIR}/scripts/validate.sh"
paths: "src/**/*.ts, tests/**/*.ts"
shell: bash
---

Your skill instructions here...
```

Source: [Claude Code Skills — Frontmatter reference](https://code.claude.com/docs/en/skills#frontmatter-reference)
</details>

<details>
<summary><strong>Copilot CLI SKILL.md example</strong> (click to expand)</summary>

```yaml
---
name: my-skill
description: What this skill does and when to use it
license: MIT
compatibility: Requires Node.js 18+
metadata:
  author: your-name
  version: "1.0.0"
allowed-tools: shell
---

Your skill instructions here...
```

Source: [Copilot CLI — Creating agent skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-skills)
· `compatibility` and `metadata` from [Agent Skills spec](https://agentskills.io/specification)
· Example: [phoenix-cli SKILL.md](https://github.com/github/awesome-copilot/blob/main/plugins/phoenix/skills/phoenix-cli/SKILL.md)
</details>

---

### 2.5 Workflow Agent

**Definition:** An agent with `## Inputs` declaration, structured parameters, and contract-driven
interface. Called by skills with well-defined arguments.

**CREATE WHEN:** "Given X, produce Y" with a fixed parameter contract, reused by 2+ skills.

**Token cost tier:** ZERO until spawned (624–3,360 tokens when invoked).

#### Agent Frontmatter Schema (platform comparison)

Agent frontmatter differs significantly between platforms. Notably, Copilot CLI officially documents
more frontmatter fields for agents than it does for skills.

| Field | Claude Code ([source](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)) | Copilot CLI ([source](https://docs.github.com/en/copilot/reference/custom-agents-configuration#yaml-frontmatter-properties)) |
|-------|------------|-------------|
| `name` | ✅ Required (lowercase + hyphens) | ✅ Optional (display name) |
| `description` | ✅ Required | ✅ **Required** |
| `tools` | ✅ Allowlist (inherits all if omitted) | ✅ List of tool names/aliases; `["*"]` for all |
| `disallowedTools` | ✅ Denylist (applied before `tools`) | — |
| `model` | ✅ `sonnet`, `opus`, `haiku`, full ID, or `inherit` | ✅ Model to use |
| `disable-model-invocation` | — (use skill-level field instead) | ✅ `true` = manual select only |
| `user-invocable` | — (use skill-level field instead) | ✅ `false` = only programmatic access |
| `target` | — | ✅ `vscode` or `github-copilot` |
| `mcp-servers` / `mcpServers` | ✅ Inline definitions or name references | ✅ Additional MCP servers (YAML object) |
| `metadata` | — | ✅ Key-value annotation |
| `permissionMode` | ✅ `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan` | — |
| `maxTurns` | ✅ Limit conversation turns | — |
| `skills` | ✅ Preload skill content at startup | — |
| `hooks` | ✅ Lifecycle hooks scoped to agent — [source](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents) | — |
| `memory` | ✅ `user` / `project` / `local` (persistent across sessions) | — |
| `background` | ✅ Run as background task | — |
| `effort` | ✅ `low` / `medium` / `high` / `max` | — |
| `isolation` | ✅ `worktree` for git worktree isolation | — |
| `color` | 👁️ Display color (`red`, `blue`, `green`, etc.) | — |
| `initialPrompt` | 👁️ Auto-submitted first user turn (with `--agent`) | — |
| `infer` | — | ⚠️ Retired — use `disable-model-invocation` instead |

> **Key insight:** Copilot CLI officially supports `disable-model-invocation`, `user-invocable`, and
> `metadata` for **agents** but NOT for **skills**. This creates an asymmetry — if you need these
> controls on a skill, you must wrap it in an agent or use the 👁️ observed (undocumented) behavior.

<details>
<summary><strong>Claude Code agent example</strong> (click to expand)</summary>

```yaml
---
name: code-reviewer
description: Reviews code for quality, security, and best practices
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
model: sonnet
effort: medium
maxTurns: 20
permissionMode: plan
memory: user
skills:
  - api-conventions
  - error-handling-patterns
hooks:
  PostToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "echo 'Tool used'"
---

You are a senior code reviewer. Analyze code for quality, security, and best practices.
```

Source: [Claude Code — Subagents](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)
</details>

<details>
<summary><strong>Copilot CLI agent example</strong> (click to expand)</summary>

```yaml
---
name: test-specialist
description: Focuses on test coverage and testing best practices
tools: ['read', 'edit', 'search', 'execute']
model: gpt-4-turbo
disable-model-invocation: false
user-invocable: true
target: github-copilot
metadata:
  author: your-name
  version: "1.0.0"
mcp-servers:
  custom-mcp:
    type: local
    command: some-command
    args: ['--arg1']
---

You are a testing specialist. Analyze tests and improve coverage.
```

Source: [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
</details>

---

### 2.6 Domain Expert Agent

**Definition:** An agent with no explicit Inputs section. Uses tools or MCP directly. Acts as
a specialist reviewer or generator.

**CREATE WHEN:** Specialist needs direct tool access, no fixed parameter contract.

**Token cost tier:** ZERO until spawned.

**Frontmatter:** Uses the same agent frontmatter schema as §2.5 Workflow Agent (see table above).
The distinction between Workflow and Domain Expert agents is structural (Inputs declaration vs.
free-form prompt), not schema-level — both use `.agent.md` files with identical frontmatter fields.

> **Plugin agent restriction (Claude Code only):** Plugin-shipped agents cannot use `hooks`,
> `mcpServers`, or `permissionMode` in their frontmatter — these are stripped for security.
> ([source](https://code.claude.com/docs/en/plugins-reference#agents))

---

### 2.7 Reference

**Definition:** A standalone `.md` in `references/` — tables, schemas, constraint catalogues.

**CREATE WHEN:** SKILL.md would exceed 300 lines, or multiple skills need the same content.

**Token cost tier:** ZERO until explicitly read.

---

### 2.8 Script

**Definition:** Python or Bash in `scripts/`. Executed by the OS; never loaded into context.

**CREATE WHEN:** Deterministic logic: loops, data transforms, file parsing.

**Token cost tier:** ZERO always.

---

### 2.9 Hook

**Definition:** An event handler wired to a lifecycle event.

**Platform comparison:**

| Aspect | Claude Code ([source](https://code.claude.com/docs/en/hooks)) | Copilot CLI ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#file-locations)) |
|--------|------------|-------------|
| **Config location** | `hooks/hooks.json` in plugin, or inline in `plugin.json` | `hooks.json` at plugin root, or `hooks/hooks.json` |
| **Required?** | Optional — absent `hooks.json` is fine | Optional (both `hooks.json` and `hooks/hooks.json` are checked) |
| **Event casing** | PascalCase: `SessionStart`, `PreToolUse`, `PostToolUse` | camelCase: `sessionStart`, `preToolUse`, `postToolUse` |
| **Hook types** | `command`, `http`, `prompt`, `agent` | `command` (primary), others vary |
| **Total events** | 24+ events (see table below) | ~6 core events |
| **Matcher** | Regex or exact string on tool name | Tool name matching |
| **`if` field** | Permission-rule syntax (`Bash(git *)`) | Not documented |

<details>
<summary><strong>Claude Code — Complete hook events list</strong> (click to expand)</summary>

| Event | When it fires | Matcher filters |
|-------|--------------|----------------|
| `SessionStart` | Session begins or resumes | `startup`, `resume`, `clear`, `compact` |
| `UserPromptSubmit` | Prompt submitted, before Claude processes | No matcher support |
| `PreToolUse` | Before a tool call executes (can block) | Tool name |
| `PermissionRequest` | Permission dialog appears | Tool name |
| `PermissionDenied` | Tool call denied by classifier | Tool name |
| `PostToolUse` | After tool call succeeds | Tool name |
| `PostToolUseFailure` | After tool call fails | Tool name |
| `Notification` | Claude sends notification | Notification type |
| `SubagentStart` | Subagent spawned | Agent type |
| `SubagentStop` | Subagent finishes | Agent type |
| `TaskCreated` | Task created via TaskCreate | No matcher support |
| `TaskCompleted` | Task marked completed | No matcher support |
| `Stop` | Claude finishes responding | No matcher support |
| `StopFailure` | Turn ends due to API error | Error type |
| `TeammateIdle` | Agent team teammate going idle | No matcher support |
| `InstructionsLoaded` | CLAUDE.md loaded into context | Load reason |
| `ConfigChange` | Config file changes during session | Config source |
| `CwdChanged` | Working directory changes | No matcher support |
| `FileChanged` | Watched file changes on disk | Literal filenames |
| `WorktreeCreate` | Worktree being created | No matcher support |
| `WorktreeRemove` | Worktree being removed | No matcher support |
| `PreCompact` | Before context compaction | Trigger type |
| `PostCompact` | After context compaction | Trigger type |
| `Elicitation` | MCP server requests user input | MCP server name |
| `ElicitationResult` | User responds to MCP elicitation | MCP server name |
| `SessionEnd` | Session terminates | End reason |

Source: [Hooks Reference](https://code.claude.com/docs/en/hooks)
</details>

<details>
<summary><strong>Copilot CLI — Hook events</strong> (click to expand)</summary>

> 👁️ The complete list of Copilot CLI hook events is not enumerated in official docs.
> The following are observed/inferred from plugin reference and creating plugins pages:

| Event | When it fires |
|-------|--------------|
| `sessionStart` | Session begins |
| `preToolUse` | Before tool execution |
| `postToolUse` | After tool execution |
| `sessionEnd` | Session terminates |
| `userPromptSubmitted` | User submits prompt |
| `errorOccurred` | Error occurs |

Source: [CLI Plugin Reference — hooks](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#file-locations) · [Creating Plugins — hooks](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
</details>

**Token cost tier:** ZERO (executed by runtime, never in context).

---

### 2.10 MCP Config

**Definition:** JSON declaring an MCP server connection for external API access.

**CREATE WHEN** all three conditions are true:
1. Agent needs an external API not reachable via plain Bash
2. API requires authentication or session management
3. Consumer is a Domain Expert Agent (not a Workflow Agent)

**Token cost tier:** ZERO (connection metadata only).

**Platform comparison:**

| Aspect | Claude Code ([source](https://code.claude.com/docs/en/mcp)) | Copilot CLI ([source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)) |
|--------|------------|-------------|
| **Config files** | `.mcp.json` (project), `~/.claude.json` (local/user) | `~/.copilot/mcp-config.json`, `.mcp.json`, `.vscode/mcp.json`, `.devcontainer/devcontainer.json`, `.github/mcp.json` |
| **Plugin MCP** | `.mcp.json` at plugin root or inline in `plugin.json` | Plugin MCP configs (loaded by install order) |
| **Transports** | `stdio`, `sse`, `http` | `local`/`stdio`, `http`, `sse` |
| **Precedence** | Local > Project > User (same-name conflict) — [source](https://code.claude.com/docs/en/mcp#scope-hierarchy-and-precedence) | `--additional-mcp-config` > Plugin > `.vscode/mcp.json` > `~/.copilot/mcp-config.json` (last-wins) — [source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#loading-order-and-precedence) |
| **Env var expansion** | `${VAR}`, `${VAR:-default}` in `.mcp.json` | `$VAR`, `${VAR}`, `${VAR:-default}`, `${{ secrets.VAR }}` |
| **Add command** | `claude mcp add --transport <type> <name> <url>` | `/mcp add` (interactive form) |
| **List command** | `claude mcp list` or `/mcp` | `/mcp show` |
| **Built-in server** | None (all must be configured) | GitHub MCP server (built-in, no config needed) |
| **Scopes** | Local, Project, User — [source](https://code.claude.com/docs/en/mcp#mcp-installation-scopes) | User-global (`~/.copilot/mcp-config.json`) + project-level files |
| **Tools filter** | N/A (all tools from connected server) | `"tools": ["*"]` or specific tool names |

<details>
<summary><strong>Claude Code .mcp.json schema</strong> (click to expand)</summary>

```json
{
  "mcpServers": {
    "server-name": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    },
    "local-server": {
      "command": "npx",
      "args": ["-y", "some-mcp-server"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

Scopes:
- **Project** (`.mcp.json` at project root) — shared via version control
- **Local** (`~/.claude.json` → `projects.<path>.mcpServers`) — private, per-project
- **User** (`~/.claude.json` → `mcpServers`) — private, all projects

Source: [Claude Code — MCP installation scopes](https://code.claude.com/docs/en/mcp#mcp-installation-scopes)
</details>

<details>
<summary><strong>Copilot CLI mcp-config.json schema</strong> (click to expand)</summary>

```json
{
  "mcpServers": {
    "playwright": {
      "type": "local",
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {},
      "tools": ["*"]
    },
    "remote-api": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "API_KEY": "YOUR-API-KEY"
      },
      "tools": ["*"]
    }
  }
}
```

Config locations (checked in this order, last-wins for same server name):
1. `~/.copilot/mcp-config.json` — user-global (lowest priority)
2. `.vscode/mcp.json` — workspace
3. Plugin MCP configs — from installed plugins
4. `--additional-mcp-config` flag — highest priority

Source: [Copilot CLI — Adding MCP servers](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers)
· [CLI Plugin Reference — Loading order](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#loading-order-and-precedence)
</details>

> **Transport type mapping:** Claude Code's `stdio` type corresponds to Copilot CLI's `local` type.
> Copilot CLI accepts both `stdio` and `local` for compatibility
> ([source](https://docs.github.com/en/copilot/reference/custom-agents-configuration#mcp-server-type)).

---

### 2.11 Template

**Definition:** A boilerplate file used by a command or skill to scaffold new files. Templates
live inside a plugin's `templates/` directory and are referenced by the skill/command that
renders them. 🏠

> **Neither platform defines a native `templates/` directory.** This is a plugin-internal house
> convention. Templates are just supporting files inside a plugin — the AI shell does not
> discover or process them on its own.

**Supported formats:**

| Format | Extension | Rendering | Use case |
|--------|-----------|-----------|----------|
| Jinja2 | `.j2` | Variable substitution, loops, conditionals | Complex scaffolding with logic |
| Markdown | `.md` | AI fills in sections / placeholders | Document templates, architecture docs |
| Plain text / YAML / JSON | `.yaml`, `.json`, `.txt`, etc. | AI copies and adapts | Config file starters, manifests |
| Shell script | `.sh`, `.ps1` | AI executes or adapts | Init scripts, setup automation |

**Token cost tier:** ZERO always — templates are rendered by the command/skill, never injected
raw into context.

**Typical plugin layout:**
```
my-plugin/
├── skills/
│   └── scaffold/
│       └── SKILL.md          # References templates/
├── commands/
│   └── scaffold.md           # Orchestrates rendering
└── templates/
    ├── component.tsx.j2      # Jinja2 with variables
    ├── arch-blueprint.md     # Markdown template
    └── config.yaml           # Plain starter file
```

---

## 3. Standard Rules

| # | Rule | Claude Code | Copilot CLI |
|---|------|------------|-------------|
| **1** | Plugin MUST use Pattern A OR Pattern B — never hybrid | ✅ Same | ✅ Same |
| **2** | Command file MUST contain only routing logic (≤66 lines) | ✅ Same | ✅ Same |
| **3** | Every skill MUST address exactly one concern | ✅ Same | ✅ Same |
| **4** | SKILL.md body MUST NOT exceed 500 lines | ✅ Same | ✅ Same |
| **5** | Knowledge Skill MUST NOT contain numbered steps or interactive prompts | ✅ Same | ✅ Same |
| **6** | `user-invocable: false` — no user slash command; model still auto-invokes | ✅ Description stays in context | ✅ Hidden from `/skills list` |
| **6a** | `disable-model-invocation: true` — zero passive cost | ✅ Description NOT in context — [source](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill) | ❌ Not supported |
| **7** | Workflow Agent MUST declare `## Inputs` with typed parameters | ✅ Same | ✅ Same |
| **8** | Shared setup steps in 2+ skills → extract to Reference | ✅ Same | ✅ Same |
| **9** | Shared steps across 2+ plugins → extract to platform plugin | ✅ Same | ✅ Same |
| **10** | Loops/transforms/parsing → Script in `scripts/` | ✅ Same | ✅ Same |
| **10a** | Cross-plugin scripts → platform plugin's `scripts/` | ✅ Same | ✅ Same |
| **11** | Lookup content >20 lines → Reference, not inline | ✅ Same | ✅ Same |
| **12** | Boilerplate generation → Jinja2 template | ✅ Same | ✅ Same |
| **13** | Every hook script MUST be wired in hooks config | ✅ In `hooks/hooks.json` | ✅ In `hooks.json` or `hooks/hooks.json` |
| **14** | `PreToolUse` for guards, never `PostToolUse` | ✅ `PreToolUse` | ✅ `preToolUse` (camelCase) |
| **15** | `SessionStart` for context injection only | ✅ `SessionStart` | ✅ `sessionStart` (camelCase) |
| **16** | MCP config only when all three conditions met | ✅ Same | ✅ Same |
| **17** | Platform plugin is canonical home for generic reusable resources | ✅ Same | ✅ Same |
| **18** | Domain plugin MUST NOT contain generic utility logic | ✅ Same | ✅ Same |
| **19** | No duplicate Knowledge Skills across plugins | ✅ Same | ✅ Same |
| **20** | Skill >300 lines → measure tokens; >4,000 tokens → split | ✅ Same | ✅ Same |
| **21** | Description ≤ 60 words (Level-1 tax on every session) | ✅ Truncated at 250 chars in listing | ✅ Same principle |
| **22** | 🏠 Plugin SHOULD have hooks config file if it defines hooks | ❌ **Optional** — absent `hooks.json` is fine ([source](https://code.claude.com/docs/en/plugins-reference)) | Optional — `hooks.json` or `hooks/hooks.json` checked if present ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#file-locations)) |
| **23** | Skill compaction budget: ≤ 5,000 tokens per skill, 25,000 combined | ✅ After auto-compaction — [source](https://code.claude.com/docs/en/skills#skill-content-lifecycle) | — Not documented |

---

## 4. Anti-Patterns

**Anti-pattern 1 — Orphaned hook scripts**
Hook scripts exist in `hooks/` but are not wired in the hooks config. They never fire.
Violates Rule 13.

**Anti-pattern 2 — Domain logic in command files**
A command file with workflow branches, numbered steps, or inline sub-procedures. Every invocation
loads all content regardless of which action the user typed. A 415-line command file costs ~4,980
tokens per invocation. Violates Rule 2.

**Anti-pattern 3 — Knowledge skills misclassified as procedural**
Pure domain encyclopedias (no numbered steps, no interaction) marked `user-invocable: true`. They
should be `user-invocable: false`. Violates Rule 5.

**Anti-pattern 4 — Inline large reference tables in SKILL.md**
A 50-row matrix inline in SKILL.md loads on every trigger. The same data in `references/` costs
zero passively. Violates Rule 11.

**Anti-pattern 5 — Workflow Agent without `## Inputs`**
Forces callers to guess the parameter contract. Violates Rule 7.

**Anti-pattern 6 — Generic utility agents in domain plugins**
A "validate JSON" agent inside `azure-ops` is invisible to other plugins. Generic agents MUST
live in the platform plugin. Violates Rule 18.

**Anti-pattern 7 — Forcing independent entry points into Pattern A**
Pattern A router overhead (~480 tokens) adds cost when actions have different arg signatures and
no shared sub-procedures. Use Pattern B. Violates Rule 1.

**Anti-pattern 8 — Overly broad Knowledge Skill descriptions**
`description: "Use when doing any git operation"` fires on every git-adjacent session. Scope
descriptions to the specific domain. Violates Rule 21.

**Anti-pattern 9 — MCP config on a Workflow Agent**
Workflow Agents MUST NOT hold external API connections. MCP belongs to Domain Expert Agents.
Violates Rule 16.

**Anti-pattern 10 — Orphaned hooks without config**
Hook scripts exist but are not wired in any hooks config file. Both platforms check for hooks
config (`hooks/hooks.json` or `hooks.json`) but neither requires it if no hooks are defined.

**Anti-pattern 11 — Duplicated content in instructions + Knowledge Skills**
Both fire simultaneously: instructions because a file is open, the skill because the user
mentioned the domain. Double token cost, no benefit. Separate by intent.

**Anti-pattern 12 — Coding standards in Level-0 project file**
The Level-0 file (CLAUDE.md / copilot-instructions.md) is paid every session. File-type standards
belong in path-scoped instruction files. Violates Level-0 constraint in §1.

**Anti-pattern 13 — TODO files in repository root**
Commands writing `.copilot-todo.md` to the root create unmanaged garbage. Write to
`.todos/<plugin>/` with proper naming.

**Anti-pattern 14 — Skills in `~/.claude/skills/` (cross-shell pollution)**
Copilot CLI scans `~/.claude/skills/` as a personal skills location ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#loading-order-and-precedence)).
Skills placed there for Claude Code will also appear in Copilot. Use plugins instead of standalone skill directories.

---

## 5. Cost-Efficiency Playbook

### 5.1 Universal Rules (Apply to All Platforms)

These cost optimization strategies apply regardless of platform:

| Strategy | Signal | Action | Token savings |
|----------|--------|--------|--------------|
| **Extract to Reference** | SKILL.md has >20 lines of tables/examples | Move to `references/<topic>.md`; add one read instruction | Zero cost until read |
| **Use scripts** | SKILL.md has "loop through each X and check Y" | Write as Python/Bash script; AI calls it | Zero cost always |
| **Extract shared steps** | Same 3+ steps copied across multiple skills | Extract to Reference in `references/` | N× → 1× cost |
| **Split oversized skills** | Body >200 lines OR two distinct outcomes | Split into focused skills | Only invoked skill loads |
| **Inline small tasks** | Sub-task ≤10 lines, used by 1 skill only | Keep inline (spawning agent adds latency) | Avoids agent overhead |

### 5.2 Platform-Specific Optimization

| Optimization | Claude Code | Copilot CLI |
|-------------|------------|-------------|
| **Eliminate passive cost** | `disable-model-invocation: true` → zero Level-1 cost for user-only workflows | Not possible — use `workflow.md` rename + command router to minimize exposure |
| **Dev testing** | `claude --plugin-dir ./my-plugin` (session-scoped, no install needed) — [source](https://code.claude.com/docs/en/plugins-reference#debugging-and-development-tools) | `/plugin install ./my-plugin` from inside the shell or `copilot plugin install ./my-plugin` from outside — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) |
| **Live reload** | `/reload-plugins` picks up changes without restart — [source](https://code.claude.com/docs/en/discover-plugins#apply-plugin-changes-without-restarting) | No hot reload — must re-install (`/plugin install ./my-plugin`) to refresh cache; restart alone is NOT sufficient — [source](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) |
| **Persistent data** | `${CLAUDE_PLUGIN_DATA}` survives updates — [source](https://code.claude.com/docs/en/plugins-reference#persistent-data-directory) | No equivalent — plugin directory IS the data directory |
| **Plugin variable** | `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` — [source](https://code.claude.com/docs/en/plugins-reference#environment-variables) | No variables — use absolute paths |
| **Compaction survival** | Skills re-attached after compaction (first 5,000 tokens each, 25,000 combined budget, most-recent-first) — [source](https://code.claude.com/docs/en/skills#skill-content-lifecycle) | Not documented |
| **Description budget** | Truncated at 250 chars in skill listing — [source](https://code.claude.com/docs/en/skills#frontmatter-reference) | No documented truncation |

### 5.3 Pattern A vs Pattern B Cost Comparison

**Pattern A — Single router + skills** (`/plugin action`):

| Component | Lines | Tokens | When paid |
|---|---|---|---|
| Routing command | 40 | 480 | Every invocation |
| 3 skill frontmatters | — | 108 | Every session |
| Typical skill body | 80–150 | 960–1,800 | Only when that action invoked |
| Shared steps (Reference) | 60 | 720 | When skill reads it |

Per-session cost (10 invocations): **~18,480 tokens**

**Pattern B — Focused independent commands:**

| Component | Lines | Tokens | When paid |
|---|---|---|---|
| Each command frontmatter | — | 36 | Every session, per command |
| Each command file | ~50–66 | 600–792 | Only when invoked |

Per-session cost (10 invocations across 5 commands): **~7,920 tokens**

**Decision rule:**
- Actions share namespace + common sub-procedures → Pattern A
- Actions are independent with separate arg signatures → Pattern B
- Inline all action workflows in one command file → **NEVER** (Anti-pattern 2)

---

## 6. Platform Plugin Architecture

### 6.1 Plugin Directory Structure

```
Claude Code                              Copilot CLI
──────────────────────────────────       ──────────────────────────────────
~/.claude/plugins/cache/                 ~/.copilot/installed-plugins/
  <marketplace>/                           <marketplace>/
    <plugin>/<version>/                      <plugin>/
      .claude-plugin/                          plugin.json        ← at root
        plugin.json      ← in subdir          hooks.json         ← at root or hooks/
      skills/                                  commands/
        <name>/SKILL.md                          <name>.md
      commands/                                skills/
        <name>.md                                <name>/
      agents/                                      SKILL.md (or workflow.md)
        <name>.md                              agents/
      hooks/                                     <name>.agent.md
        hooks.json
      scripts/
      references/
      templates/
```

### 6.2 Plugin Discovery and Registration

| Aspect | Claude Code | Copilot CLI |
|--------|------------|-------------|
| **Marketplace manifest** | `.claude-plugin/marketplace.json` | `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, or `.claude-plugin/marketplace.json` ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#file-locations)) |
| **Plugin manifest** | `.claude-plugin/plugin.json` (optional — auto-discovers if absent) | `plugin.json`, `.plugin/plugin.json`, `.github/plugin/plugin.json`, or `.claude-plugin/plugin.json` |
| **Install command** | `/plugin install <name>@<marketplace>` | `copilot plugin install <spec>` or `/plugin install` |
| **Registration** | `~/.claude/plugins/installed_plugins.json` + `settings.json` | `~/.copilot/installed-plugins/` directory structure |
| **Uninstall** | `/plugin uninstall <name>@<marketplace>` | `copilot plugin uninstall <name>` |
| **Marketplace add** | `/plugin marketplace add <source>` | `copilot plugin marketplace add <source>` |

### 6.3 Plugin Source Types

| Source type | Claude Code ([source](https://code.claude.com/docs/en/plugin-marketplaces#plugin-sources)) | Copilot CLI ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#plugin-specification-for-install-command)) |
|-------------|------------|-------------|
| **Relative path** | `"./plugins/my-plugin"` | `"./plugins/my-plugin"` or `"plugins/my-plugin"` |
| **GitHub** | `{ "source": "github", "repo": "owner/repo" }` | `OWNER/REPO` |
| **GitHub subdir** | `{ "source": "git-subdir", "url": "...", "path": "..." }` | `OWNER/REPO:PATH/TO/PLUGIN` |
| **Git URL** | `{ "source": "url", "url": "https://..." }` | `https://github.com/o/r.git` |
| **Local path** | Direct path to dir or `marketplace.json` | `./my-plugin` or `/abs/path` |
| **npm** | `{ "source": "npm", "package": "@scope/pkg" }` | Not documented |
| **Version pinning** | `ref` + `sha` fields | Not documented |

### 6.4 Skill Discovery and Loading Order

**Copilot CLI loading precedence** ([source](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#loading-order-and-precedence)):

```
Skills (first-found-wins):
  1. <project>/.github/skills/     (project)
  2. <project>/.agents/skills/     (project)
  3. <project>/.claude/skills/     (project)
  4. <parents> inherited            (monorepo)
  5. ~/.copilot/skills/             (personal-copilot)
  6. ~/.agents/skills/              (personal-agents)
  7. ~/.claude/skills/              (personal-claude)  ← cross-shell pollution!
  8. PLUGIN: skills/ dirs           (plugin)
  9. COPILOT_SKILLS_DIRS env        (custom)
```

> ⚠️ **Cross-shell pollution:** Copilot CLI scans `~/.claude/skills/` (item 7) as a personal
> skills location. Skills placed there for Claude Code will also appear in Copilot's
> `/skills list`. To avoid this, use plugins instead of standalone skill directories.

**Claude Code loading** ([source](https://code.claude.com/docs/en/skills#where-skills-live)):

```
Skills (priority: enterprise > personal > project; plugin skills are namespaced separately):
  1. Enterprise managed settings    (highest)
  2. ~/.claude/skills/<name>/       (personal)
  3. .claude/skills/<name>/         (project)
  4. <plugin>/skills/<name>/        (plugin — namespaced as plugin-name:skill-name, no conflict)
  5. Nested .claude/skills/ in subdirs (monorepo auto-discovery)
```

> Plugin skills use the `plugin-name:skill-name` namespace and therefore do not compete with
> enterprise/personal/project skills of the same name.

### 6.5 Installation Scopes

| Scope | Claude Code ([source](https://code.claude.com/docs/en/settings#configuration-scopes)) | Copilot CLI |
|-------|------------|-------------|
| **User** | `~/.claude/settings.json` — across all projects (default) | `~/.copilot/installed-plugins/` — across all projects |
| **Project** | `.claude/settings.json` — shared via repo | Not documented as separate scope |
| **Local** | `.claude/settings.local.json` — gitignored | Not documented |
| **Managed** | Admin-controlled, read-only | Not documented |

---

## 7. Summary Decision Tree

```
New resource needed
│
├─ A. USER-FACING CONTENT
│   │
│   ├─ Slash command
│   │   ├─ Existing plugin domain? → Add skill + update routing
│   │   └─ New domain? → CREATE Plugin
│   │       ├─ Shared namespace + sub-procedures → Pattern A
│   │       └─ Independent actions → Pattern B
│   │
│   ├─ Multi-step interactive workflow → CREATE Procedural Skill
│   │
│   └─ AI activates by context match
│       ├─ Dense domain rules → CREATE Knowledge Skill
│       └─ Lookup data / changes per session → CREATE Reference
│
├─ B. SUPPORTING INFRASTRUCTURE
│   │
│   ├─ Fixed-contract sub-task → Workflow Agent
│   ├─ Specialist analysis with tool access → Domain Expert Agent
│   ├─ Lookup tables >20 lines → Reference
│   ├─ Deterministic computation → Script
│   └─ Boilerplate generation → Template
│
├─ C. LIFECYCLE AUTOMATION
│   │
│   ├─ Inject context before AI starts → SessionStart / sessionStart
│   ├─ Block dangerous tool → PreToolUse / preToolUse
│   ├─ Side effect after write → PostToolUse / postToolUse
│   ├─ Gate before session close → SessionEnd / sessionEnd
│   └─ Read-only analysis plugin → SKIP hooks entirely
│
└─ D. SCOPE DECISIONS
    │
    ├─ Generic resource (git ops, schema validation) → Platform plugin
    ├─ Domain-specific, 1 plugin → That plugin's directory
    ├─ Domain-specific, 2+ plugins → Extract to platform plugin
    └─ New coherent domain with command → New plugin
```

**Platform-specific decision factors:**

| Decision | Claude Code | Copilot CLI |
|----------|------------|-------------|
| **Should this skill be user-only?** | Use `disable-model-invocation: true` | 👁️ Use command router + `workflow.md` rename (house convention) |
| **Where to put personal skills?** | Plugin in local marketplace (not `~/.claude/skills/`) | Plugin via `copilot plugin install` |
| **Can I dev-test without installing?** | `claude --plugin-dir ./plugin` | No — must `/plugin install ./plugin` (in-shell) or `copilot plugin install ./plugin` (outside) |
| **How to reload after changes?** | `/reload-plugins` (hot reload) | Re-install: `/plugin install ./plugin` (restart alone is NOT sufficient) |

---

## 8. Quick Reference Card

| Resource Type | When to use | Typical size | Token cost | Claude Code | Copilot CLI |
|---|---|---|---|---|---|
| **Level-0 file** | Project identity, build commands | ≤ 150 lines | 🔴 ALWAYS | `CLAUDE.md` | `.github/copilot-instructions.md` |
| **Path-scoped instructions** | File-type coding standards | 60–130 lines | 🟡 When matching file open | `.claude/rules/*.md` (`paths:`) | `.github/instructions/*.instructions.md` (`applyTo:`) |
| **Plugin** | Coherent domain with command | N/A | Structural | `.claude-plugin/plugin.json` | `plugin.json` |
| **Command — Pattern A** | Shared namespace, shared sub-procedures | ≤ 66 lines | LOW + skill | `commands/<name>.md` | `commands/<name>.md` |
| **Command — Pattern B** | Independent entry points | ≤ 66 lines | LOW | `commands/<name>.md` | `commands/<name>.md` |
| **Procedural Skill** | Interactive multi-step workflow | 66–200 lines | LOW–MED | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` |
| **Knowledge Skill** | Domain expertise for review | 135–174 lines | MEDIUM | `user-invocable: false` | `user-invocable: false` |
| **Workflow Agent** | Fixed-contract sub-task | 52–100 lines | ZERO→spawn | `agents/<name>.md` | `agents/<name>.agent.md` |
| **Domain Expert Agent** | Specialist with tool access | 80–280 lines | ZERO→spawn | `agents/<name>.md` | `agents/<name>.agent.md` |
| **Reference** | Static lookup, tables | 103–430 lines | ZERO→read | `references/<name>.md` | `references/<name>.md` |
| **Script** | Deterministic computation | 50–200 lines | ZERO always | `scripts/<name>.py` | `scripts/<name>.py` |
| **Template** | Boilerplate generation 🏠 | 30–120 lines | ZERO always | `templates/<name>.*` (plugin-internal) | `templates/<name>.*` (plugin-internal) |
| **Hook** | Lifecycle automation | 20–60 lines | ZERO always | `hooks/hooks.json` (PascalCase) | `hooks.json` (camelCase) |
| **MCP Config** | External API connection | JSON entry | ZERO always | `.mcp.json` | `.mcp.json` |

---

## 9. Plugin and Marketplace Setup

**Sources:** [Creating Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) · [Discover Plugins](https://code.claude.com/docs/en/discover-plugins) · [Creating Plugins (Copilot)](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) · [Plugin Reference (Copilot)](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

---

### 9.1 Local Plugin Install

Install a single plugin directly — no marketplace registry required. Use this for dev work or one-off installs.

**Claude Code:**

The only in-shell entry point is the **`/plugin`** (or **`/plugins`**) wizard — a full-screen TUI with four tabs:

```
  Plugins  Discover   Installed   Marketplaces   Errors
  ╭────────────────────────────────────────────────────╮
  │ ⌕ Search…                                         │
  ╰────────────────────────────────────────────────────╯
   type to search · Space to toggle · Enter to details · Esc to back
```

| Goal | Action |
|------|--------|
| Dev testing (ephemeral, no install) | `claude --plugin-dir ./my-plugin` (outside shell) |
| Install from local marketplace | `/plugin` → **Marketplaces** tab → add path → **Discover** tab → Space to enable |
| View installed plugins | `/plugin` → **Installed** tab |
| Reload after edits | `/reload-plugins` (in-shell hot reload) |

**Copilot CLI:**

Both inside and outside the shell are supported:

| Goal | Outside shell | Inside shell |
|------|--------------|--------------|
| Install from local path | `copilot plugin install ./my-plugin` | `/plugin install ./my-plugin` |
| Re-install after editing | `copilot plugin install ./my-plugin` | `/plugin install ./my-plugin` |
| List installed skills | `copilot skills list` | `/skills list` |

> ⚠️ For Copilot CLI, simply **restarting is not sufficient** after editing — you must re-run the install command to refresh the cache (`~/.copilot/installed-plugins/_direct/<source-id>/`).

---

### 9.2 Marketplace Setup

A marketplace is a directory (local or on any git host — GitHub, Azure DevOps, GitLab, self-hosted, etc.) with a `marketplace.json` descriptor. The structure and registration flow are the same regardless of where it lives; only the path or URL passed to the register command differs.

**Required directory layout:**

```
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json          ← Claude Code marketplace descriptor
├── .github/
│   └── plugin/
│       └── marketplace.json      ← Copilot CLI marketplace descriptor
└── plugins/
    └── my-plugin/
        ├── plugin.json           ← plugin manifest
        ├── commands/
        │   └── my-command.md     ← /my-plugin:my-command
        └── skills/
            └── my-skill/
                ├── SKILL.md      ← auto-discovered by Claude Code; reference via ${CLAUDE_PLUGIN_ROOT}
                └── workflow.md   ← 👁️ used by Copilot CLI command (avoids Copilot auto-discovery)
```

> 🏠 **House convention:** For dual-shell plugins, name the Copilot-facing skill file `workflow.md`
> instead of `SKILL.md`. Copilot CLI only auto-discovers files named `SKILL.md`, so renaming it
> prevents the skill from appearing as a standalone slash command while still letting the command
> file include it. This is NOT officially documented — it is an observed behaviour.
>
> Additionally: Claude Code supports `${CLAUDE_PLUGIN_ROOT}` in command files to reference
> co-located skill content; Copilot CLI has no equivalent — use absolute paths instead.

**marketplace.json:**

```json
{
  "name": "my-marketplace",
  "owner": { "name": "YourName", "email": "you@example.com" },
  "metadata": {
    "description": "Team plugin marketplace",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "description": "What it does",
      "source": "./plugins/my-plugin"
    }
  ]
}
```

> ⚠️ `description` is **not** a top-level field — it lives inside `metadata.description` on both platforms.

**Platform differences in `marketplace.json`:**

| Area | Claude Code | Copilot CLI |
|------|-------------|-------------|
| Relative `source` paths | **Must** start with `./` | `./` is optional — `plugins/my-plugin` also works |
| `strict` on plugin entries | Controls authority: `true` = `plugin.json` wins; `false` = marketplace entry is the sole definition | Controls validation strictness: `true` = full schema validation; `false` = relaxed (for legacy/direct installs) |
| `author` object in plugin entries | `{ name, email? }` | `{ name, email?, url? }` — extra `url` field supported |

Sources: [Claude Code — marketplace schema](https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema) · [Copilot CLI — marketplace.json fields](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#marketplacejson-fields)

**Register and install** — substitute the local path or remote URL as your `SPEC`:

| SPEC examples | |
|---|---|
| Local directory | `./my-marketplace` or `/abs/path/to/my-marketplace` |
| GitHub | `https://github.com/<org>/<repo>` or `owner/repo` (Copilot CLI shorthand) |
| Azure DevOps / other git | `https://dev.azure.com/<org>/<project>/_git/<repo>` |
| GitLab / self-hosted | `https://gitlab.example.com/<group>/<repo>.git` |

| Step | Claude Code | Copilot CLI (outside shell) | Copilot CLI (inside shell) |
|------|-------------|----------------------------|---------------------------|
| Register | `/plugin` → **Marketplaces** tab → add `SPEC` | `copilot plugin marketplace add SPEC` | `/plugin marketplace add SPEC` |
| Discover & install | `/plugin` → **Discover** tab → Space to enable | `copilot plugin install my-plugin@my-marketplace` | `/plugin install my-plugin@my-marketplace` |
| Cache path (local) | `~/.claude/plugins/` | `~/.copilot/installed-plugins/my-marketplace/my-plugin/` | same |

> 💡 The `name` field in `marketplace.json` is the `@name` used in install commands — it does **not** have to match the repo name or directory name.

---

## 10. TODO File Standard

All TODO files produced by marketplace plugin commands are written to `.todos/<plugin>/`
at the marketplace root and tracked in git.

**File name:** `<command>-<scope>-YYYYMMDD.md`

**Severity levels:**

| Marker | Code | Meaning |
|---|---|---|
| 🔴 | `RULE_VIOLATION` | Violates a hard rule — must fix |
| 🟡 | `ANTI_PATTERN` | Matches documented anti-pattern — should fix |
| 🔵 | `IMPROVEMENT` | Optional improvement |
| 🟢 | `OK` | Check passed |

**Rule:** Every command that produces analysis output MUST write to `.todos/<plugin>/`.
Writing TODO files to the repository root is Anti-pattern 13.