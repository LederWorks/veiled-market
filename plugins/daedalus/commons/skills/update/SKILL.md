---
name: daedalus-update
description: 'Edit an existing resource in a plugin''s commons/ directory. Reads the current file,
  applies the requested change, and reminds the user to build. Trigger on: "update a skill",
  "edit a command", "modify a plugin resource", "change commons/ content".'
user-invocable: false
---

# Update Workflow

Edit an existing resource inside a plugin's `commons/` directory.
Always edit `commons/` only — never `claude/` or `copilot/`.

## Step 1 — Clarify the target

Ask the user in one message:

1. **Plugin name** — which plugin contains the resource (e.g., `atlas`, `daedalus`)
2. **Resource type** — `skill`, `agent`, `command`, `hook`, `template`, `reference`, `script`, or `plugin` (for `plugin.base.json`)
3. **Resource name** — file or directory name (e.g., `init`, `scaffolder`, `forge`)
4. **What to change** — describe the edit in plain language

If the plugin name is already known from `$ARGUMENTS`, skip asking for it.

## Step 2 — Locate the file

Resolve the file path from the resource type:

| Resource type | Path in `commons/` |
|---|---|
| `plugin` | `plugin.base.json` |
| `command` | `commands/<name>.md` |
| `skill` | `skills/<name>/SKILL.md` |
| `agent` | `agents/<name>.md` |
| `reference` | `references/<name>.md` |
| `template` | `templates/<path>/<name>.j2` |
| `script` | `scripts/<name>.py` |
| `hook` | `hooks.json` |
| `mcp` | `.mcp.json` |

Read the resolved file before editing.

## Step 3 — Apply the change

Edit the file in `commons/` exactly as requested. Follow these constraints:

- Skill descriptions must be ≤60 words
- Command files must stay ≤66 lines (Pattern A router)
- Do not add numbered steps or interactive prompts to Knowledge Skills
- Preserve existing frontmatter fields not mentioned in the change request

## Step 4 — Report and hand off

Show a one-line diff summary (e.g., "Updated `description` in `skills/init/SKILL.md`"). Then say:

> **Next:** `/forge build <plugin-name>`
