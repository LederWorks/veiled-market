# Copilot Instructions — veiled-market

An AI-curated plugin marketplace for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [Claude Code](https://code.claude.com/docs/en/plugins). For how the pipeline works, workflow triggers, and how to run things locally, see [`AGENTS.md`](../AGENTS.md).

---

## Plugin format

Every plugin must be compatible with both Copilot CLI and Claude Code.

### Directory structure

```
plugins/{plugin}/
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
plugin/{name}              e.g. plugin/terraformer
status/{discovered|draft|candidate|finalized}
type/skill                    SKILL.md files
type/agent                    *.agent.md files
type/hook                     hooks.json files
type/mcp                      .mcp.json files
type/instruction              *.instructions.md | *.prompt.md | *.command.md | *.workflow.md
type/plugin                   plugin.json (complete plugin manifest + bundle)
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

---

## Pipeline stages (quick reference)

The automated six-stage pipeline (Stages 0–4 plus a plugin-proposal workflow) runs entirely via GitHub Actions. For full detail see [`AGENTS.md`](../AGENTS.md).

| Stage | Workflow file | Trigger | Purpose |
|-------|--------------|---------|---------|
| Proposal | `05-plugin-proposal.yml` | Issue opened with `type/plugin` label | Parse issue form; add plugin stub to `sources/plugins.json`; open proposal PR; comment on issue |
| 0 | `00-setup-plugins.yml` | Push to `sources/plugins.json` or `sources/marketplaces.json`; manual | Validate schemas, create GitHub Projects per plugin, ensure all labels exist |
| 1 | `01-discovery.yml` | After Stage 0 succeeds; weekly schedule; manual | Discover resources from all registered sources sequentially per plugin; create GitHub Issues labeled `status/draft` automatically; commit registry patches with `chore(registry): merge discovery patches [skip ci]` |
| 2 | `02-evaluate.yml` | After Stage 1 succeeds; issue labeled `status/draft`; manual | Score `status/draft` issues with `evaluate.py`; synthesise a draft plugin into `drafts/{plugin}/`; open a draft PR |
| 3 | `03-enrich.yml` | Draft PR opened; after Stage 2 succeeds; manual | AI-score resources via GitHub Models; write scores to `registry.json` with `[skip ci]`; close excluded issues; open a single candidate PR |
| 4 | `04-finalize-plugin.yml` | Candidate PR **merged** to `main`; manual | Promote `drafts/{plugin}/` → `plugins/{plugin}/`; regenerate both marketplace manifests from `sources/plugins.json`; all commits use `[skip ci]` |

### Key invariants

- **`sources/plugins.json`** is the single source of truth for all plugins. Never edit `marketplace.json` files manually — they are regenerated by `finalize.py --step marketplace`.
- **`[skip ci]`** must appear in every automated commit message to prevent cascade trigger loops. Use full Conventional Commits format: `chore(scope): message [skip ci]`.
- **`APP_ID` + `APP_PRIVATE_KEY`** secrets are required for Stage 0 GitHub Projects v2 mutations. The `setup-projects` job uses `actions/create-github-app-token@v1` to mint a short-lived installation token from these secrets. Register the `veiled-market-pipeline` GitHub App in the LederWorks org with `Projects: write` (org) and `Contents/Issues/Pull requests: write` (repo) permissions.
- **Permissions** must be declared at job level (principle of least privilege): default `permissions: {}` at workflow top level, then only the minimum per job.
- All script CLI flags use `--plugin` (not `--expertise`) after the Stage 1 rename.
