---
name: daedalus-create
description: 'Scaffold a new veiled-market plugin or add a resource to an existing one. Collects
  inputs, confirms with the user, then spawns the scaffolder agent to create the correct
  commons/ files. Trigger on: "create a plugin", "add a skill", "scaffold a resource".'
user-invocable: false
---

# Create Workflow

Guide the user through creating a new plugin or adding a resource to an existing plugin.
Always edit `commons/` only — never `claude/` or `copilot/`.

## Step 1 — Read the spec

Read `docs/PLUGIN-LIFECYCLE.md` to understand the `commons/` layout and all 9 resource types.
Read `references/resource-types.md` for the full resource type table with size limits.

## Step 2 — Clarify the intent

Ask the user ONE question:

> Are you creating a **new plugin** (full `commons/` tree) or adding a **resource** to an
> existing plugin (a skill, agent, command, hook, template, reference, script, or MCP config)?

Wait for the answer before proceeding.

## Step 3 — Collect inputs

### If creating a **new plugin**

Collect these fields in a single message:

1. **Plugin name** — kebab-case (e.g., `my-plugin`)
2. **Description** — one sentence, ≤60 words, wrap in single quotes for frontmatter
3. **Command verb** — the philosopher verb (e.g., `forge`, `probe`, `anchor`)
4. **Skills** — comma-separated list of skill names (e.g., `init,update,validate`)
5. **Agents needed?** — yes/no; if yes, list agent names
6. **Author name**

### If adding a **resource**

Collect these fields in a single message:

1. **Parent plugin name** — which existing plugin receives the resource
2. **Resource type** — one of: `skill`, `agent`, `command`, `hook`, `template`, `reference`, `script`, `mcp`
3. **Resource name** — kebab-case
4. **Description** — one sentence ≤60 words
5. **user-invocable** — yes/no (only for skills)
6. Any type-specific fields (e.g., command verb, template path pattern)

## Step 4 — Confirm

Show a summary of what will be created:

```
Creating: <new plugin | resource type "name" in plugin "parent">
Files to be created:
  commons/plugin.base.json
  commons/hooks.json
  commons/commands/<verb>.md
  commons/skills/<name>/SKILL.md
  ...
```

Ask: "Proceed? (yes/no)"

Wait for confirmation before continuing.

## Step 5 — Spawn the scaffolder

Spawn the **scaffolder** agent (`agents/scaffolder.md`) with all collected inputs as variables:

- `MODE`: `plugin` or `resource`
- `PLUGIN_NAME`: plugin name
- `RESOURCE_TYPE`: resource type (for resource mode)
- `RESOURCE_NAME`: resource name
- `COMMAND_VERB`: command verb (for plugin mode or command resource)
- `SKILLS`: comma-separated skill names (for plugin mode)
- `DESCRIPTION`: description string
- `AUTHOR`: author name
- `MARKETPLACE_ROOT`: absolute path to the veiled-market root

Wait for the scaffolder to complete before proceeding.

## Step 6 — Report and hand off

List every file created. Then say:

> **Next:** `/forge build <plugin-name>`
