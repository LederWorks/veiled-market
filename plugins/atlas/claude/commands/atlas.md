---
name: anchor
description: 'local workspace and project setup — init, update, and validate AI context files, IDE settings, and project scaffolding'
argument-hint: '[init|update|validate] [owner/repo]'
---

# /anchor

Route to the Atlas skill for the requested action.

## Arguments

The user provided: `$ARGUMENTS`

Parse the first token as **action**. Default: `init`.

Optional second token: a GitHub `owner/repo` reference — enables remote repo mode (reads/writes via GitHub MCP tools instead of local file operations).

## Routing

| Action | Skill |
|---|---|
| `init` (default) | `${CLAUDE_PLUGIN_ROOT}/skills/init/SKILL.md` |
| `update` | `${CLAUDE_PLUGIN_ROOT}/skills/update/SKILL.md` |
| `validate` | `${CLAUDE_PLUGIN_ROOT}/skills/validate/SKILL.md` |

Load the skill file for the matched action and follow its workflow. If the action is unrecognised or no arguments are given, show the table above as a usage guide and stop.

**Remote repo mode**: If an `owner/repo` argument is present, pass it to the loaded skill so it uses GitHub MCP tools for all reads and writes.
