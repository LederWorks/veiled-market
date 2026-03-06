# Copilot Instructions — veiled-market

An AI-curated plugin marketplace for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [Claude Code](https://code.claude.com/docs/en/plugins). For how the pipeline works, workflow triggers, and how to run things locally, see [`AGENTS.md`](../AGENTS.md).

---

## Plugin format

Every plugin must be compatible with both Copilot CLI and Claude Code.

### Directory structure

```
plugins/{expertise}/
├── plugin.json           # Required manifest
├── agents/
│   └── {name}.agent.md   # Agent definition files
├── skills/
│   └── {skill-name}/
│       └── SKILL.md      # One directory per skill
├── hooks.json            # PreToolUse / PostToolUse hooks
└── .mcp.json             # MCP server configurations
```

### `plugin.json` required fields

```json
{
  "name": "kebab-case-name",
  "version": "MAJOR.MINOR.PATCH",
  "description": "...",
  "license": "MIT",
  "agents": "agents/",
  "skills": "skills/",
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json"
}
```

### `SKILL.md` frontmatter

```markdown
---
name: skill-name           # must match the containing directory name
description: Brief description (max 200 chars)
platforms: [aws, azure]    # optional
languages: [hcl, bash]     # optional
---
```

### Agent file frontmatter

```markdown
---
name: agent-name
description: What this agent specialises in
tools: ["bash", "view", "edit"]
platforms: [aws, azure]    # optional
languages: [hcl, bash]     # optional
---
```

### `hooks.json` format

Hooks use `bash` type commands only. Access `$TOOL_INPUT` to inspect what triggered the hook. Hooks fire on `PreToolUse` and `PostToolUse` with a `matcher` specifying the tool (e.g., `"bash"`).

### MCP servers in `.mcp.json`

Use environment variables for API keys — never hard-code credentials.

---

## Key conventions

### Naming

| Item | Convention |
|------|-----------|
| Plugin name | `kebab-case`, max 64 chars |
| Skill name (frontmatter + directory) | `kebab-case`; these must match |
| Agent file | `{name}.agent.md` |
| Version | Semantic versioning: `MAJOR.MINOR.PATCH` |

### GitHub label scheme

Labels follow a strict hierarchical namespace:

```
expertise/{name}              e.g. expertise/terraformer
status/{discovered|draft|candidate|finalized}
type/{skill|agent|hook|plugin}
lang/{tag}                    e.g. lang/hcl
platform/csp/{tag}            e.g. platform/csp/aws, platform/csp/azure
platform/ci/{tag}             e.g. platform/ci/github-actions
platform/saas/{tag}           e.g. platform/saas/terraform-cloud
ai/{discovery|draft|evaluation}
source/{source-id}            e.g. source/awesome-copilot
```

The `platform_label()` helper in `registry.py` selects the correct sub-namespace (`csp/`, `ci/`, `saas/`, or bare) for a given tag. Always use this function rather than constructing label names manually.

### Commit conventions

Uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(terraformer): add terraform-test skill
fix(terraformer): correct terraform-apply confirmation prompt
docs: update contributing guide
chore(sources): add new-source.com to marketplaces.json
```

### Plugin quality checklist (before merging to `plugins/`)

- `plugin.json` has `name`, `version`, `description`, `license`
- Every `SKILL.md` has valid `name` and `description` frontmatter; `name` matches its directory
- No hard-coded secrets, credentials, or personal data
- MCP server configs use environment variables for API keys
- Agent system prompt includes safety behaviour for destructive operations
- Works with both Copilot CLI and Claude Code
