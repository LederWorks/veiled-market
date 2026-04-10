---
name: forge
description: >
  Plugin craftsman for veiled-market. Creates new plugins or resources, updates existing
  content, builds generated outputs, and applies Socrates remediation findings.
  Trigger on: /forge, "create a plugin", "scaffold a skill", "build daedalus", "apply fixes".
argument-hint: <create|update|build|remediate> [plugin] [type] [name]
---

# /forge

Route to the Daedalus skill for the requested action.

## Arguments

The user provided: `$ARGUMENTS`

Parse the first token as **action**. Remaining tokens are passed to the routed skill.

## Routing

| Action | Skill |
|---|---|
| `create` | `${CLAUDE_PLUGIN_ROOT}/skills/create/SKILL.md` |
| `update` | `${CLAUDE_PLUGIN_ROOT}/skills/update/SKILL.md` |
| `build` | `${CLAUDE_PLUGIN_ROOT}/skills/build/SKILL.md` |
| `remediate` | `${CLAUDE_PLUGIN_ROOT}/skills/remediate/SKILL.md` |

Load the skill file for the matched action and follow its workflow exactly.

Pass to the loaded skill:
- **Action arguments:** everything after the first token (e.g., plugin name, resource type, resource name)
- **Plugin root:** `${CLAUDE_PLUGIN_ROOT}`

## Usage (no action given)

If the action is missing or unrecognised, show this table and stop:

| Command | What it does |
|---|---|
| `/forge create [plugin]` | Scaffold a new plugin or add a resource to an existing one |
| `/forge update [plugin]` | Edit an existing resource in a plugin's `commons/` directory |
| `/forge build [plugin|all]` | Run the build pipeline to generate `claude/` and `copilot/` outputs |
| `/forge remediate [plugin]` | Apply auto-fixable findings from a Socrates TODO file |
