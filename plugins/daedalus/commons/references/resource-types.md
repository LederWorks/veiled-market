---
description: >-
  Reference table of all 9 resource types supported in the veiled-market commons/ build system.
  Lists commons/ path pattern, size limits, required frontmatter fields, and examples.
  Read by: scaffolder agent, daedalus-create skill. Do not invoke directly.
---

# Resource Types — Daedalus Reference

All resources live in `commons/`. The build script transforms them per platform.
Source of truth: `docs/PLUGIN-LIFECYCLE.md` §3 and `docs/MARKETPLACE.md` §2.

---

## Type Table

| Type | `commons/` path | Required frontmatter | Size limit | Notes |
|------|----------------|---------------------|-----------|-------|
| `plugin` | `plugin.base.json` | `name`, `version`, `description`, `license` | No body | JSON manifest — not markdown |
| `command` | `commands/<verb>.md` | `name`, `description`, `argument-hint` | ≤66 lines | Pattern A router only; no inline logic |
| `skill` (user) | `skills/<name>/SKILL.md` | `name`, `description` | 66–113 lines (procedural), 135–174 lines (knowledge) | `user-invocable: true` or omit |
| `skill` (hidden) | `skills/<name>/SKILL.md` | `name`, `description`, `user-invocable: false` | 66–174 lines | Description stays in context passively |
| `agent` (workflow) | `agents/<name>.md` | `name`, `description` | 52–280 lines | MUST have `## Inputs` section |
| `agent` (domain) | `agents/<name>.md` | `name`, `description` | 52–280 lines | May hold MCP config references |
| `reference` | `references/<name>.md` | `description` (no `name`) | 103–430 lines | Zero passive cost — read on demand |
| `template` | `templates/<path>/<name>.j2` | None | No limit | Jinja2; zero token cost — rendered by OS |
| `script` | `scripts/<name>.py` | None | No limit | Zero token cost — executed by OS |
| `hook` | `hooks.json` + script files | — | Minimal JSON | Must be wired; scripts in `hooks/` dir |
| `mcp` | `.mcp.json` | — | Minimal JSON | Zero token cost — connection metadata |

---

## Build Output Mapping

| Resource | `commons/` source | `claude/` output | `copilot/` output |
|----------|-------------------|-----------------|------------------|
| `plugin` | `plugin.base.json` | `plugin.json` | `plugin.json` |
| `command` | `commands/<verb>.md` | `commands/<verb>.md` | `commands/<verb>.md` |
| `skill` (user-invocable) | `skills/<n>/SKILL.md` | `skills/<n>/SKILL.md` | `skills/<n>/SKILL.md` |
| `skill` (hidden) | `skills/<n>/SKILL.md` + `user-invocable: false` | `skills/<n>/SKILL.md` | `skills/<n>/workflow.md` |
| `agent` | `agents/<n>.md` | `agents/<n>.md` | `agents/<n>.agent.md` |
| `hook` | `hooks.json` + scripts | verbatim | adds `"version": 1` |
| `template` | `templates/<path>/<n>.j2` | verbatim copy | verbatim copy |
| `reference` | `references/<n>.md` | verbatim copy | verbatim copy |
| `script` | `scripts/<n>.py` | verbatim | verbatim |
| `mcp` | `.mcp.json` | verbatim | verbatim |

---

## Required Frontmatter by Type

### `command`

```yaml
---
name: <verb>
description: '<one sentence, ≤60 words, single-quoted>'
argument-hint: <action> [args]
---
```

### `skill` (user-invocable)

```yaml
---
name: <plugin>-<skill>
description: '<one sentence, ≤60 words, single-quoted>'
---
```

### `skill` (hidden)

```yaml
---
name: <plugin>-<skill>
description: '<one sentence, ≤60 words, single-quoted>'
user-invocable: false
---
```

### `agent` (workflow or domain)

```yaml
---
name: <name>
description: '<one sentence, ≤60 words, single-quoted>'
---
```

Workflow agents MUST have `## Inputs` section in the body (Rule 7).

### `reference`

```yaml
---
description: >-
  One or two sentences. No name field. Skills reference this file explicitly.
  Do NOT invoke this file directly.
---
```

---

## Size Budget Summary (from `docs/MARKETPLACE.md` §1)

| Resource | Target range | Hard cap | Token cost |
|----------|-------------|---------|-----------|
| Command file | ≤66 lines | 66 lines (Rule 2) | ~792 tokens/invocation |
| Procedural skill | 66–113 lines | 500 lines (Rule 4) | 792–1,356 tokens/trigger |
| Knowledge skill | 135–174 lines | 500 lines (Rule 4) | 1,620–2,088 tokens/trigger |
| Agent | 52–280 lines | None documented | 624–3,360 tokens/spawn |
| Reference | 103–430 lines | None (off-band) | 0 tokens passive |
| Template / Script | Any | None | 0 tokens always |

> **Rule 20 from MARKETPLACE.md:** If a skill exceeds 300 lines, measure tokens. If >4,000 tokens, split it.

---

## Naming Conventions

- All file and folder names: **lowercase with hyphens** (e.g., `my-skill`, `forge-command`)
- `plugin.json` `name` field must **exactly match** the containing folder name
- `description` values in frontmatter: wrapped in **single quotes**
- Skill names: `<plugin-name>-<skill-name>` (e.g., `daedalus-create`, `atlas-init`)
- Command name: the philosopher **verb** (e.g., `forge`, `probe`, `anchor`), not the plugin name

---

## Inter-Plugin Reference Convention

Skills and agents reference shared docs by direct path — no symlinks, no build-time copying:

```
Read `docs/PLUGIN-LIFECYCLE.md` — authoritative commons/ and build spec.
Read `docs/MARKETPLACE.md` §3 — the 22 rules every plugin must comply with.
```
