# veiled-market — Architecture Findings

## Principle: Always Think in Plugins

veiled-market is **plugin-first**. There are no standalone `skills/`, `agents/`, or `instructions/`
directories at the repo root. Every resource lives inside `plugins/<name>/`. This is a deliberate
divergence from the `awesome-copilot` community repo, which maintains a legacy flat layout
alongside plugins for backward compatibility with older consumers.

**Why plugins-only:**
- Plugins are the installable unit on both Claude Code and Copilot CLI
- Grouping by domain (all terraform skills together, all azure skills together) is more useful
  than a flat list of hundreds of individual resources
- The marketplace infrastructure (discovery, evaluation, finalization pipeline) operates on plugins,
  not individual files
- Users install a plugin once and get all related skills, agents, hooks, and MCP config in one step

---

## Dual-Platform Compatibility

Both Claude Code and Copilot CLI share the same plugin directory and manifest format (`plugin.json`),
but differ in enough ways that a naive single-layout approach requires undocumented workarounds.

### Platform divergence table

| Area | Claude Code | Copilot CLI |
|------|-------------|-------------|
| Skill auto-discovery | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` (same) |
| Hide skill from user | `user-invocable: false` in frontmatter | Rename to `workflow.md` (🏠 undocumented) |
| Agent file extension | `agents/<name>.md` | `agents/<name>.agent.md` (preferred) |
| Command path variable | `${CLAUDE_PLUGIN_ROOT}` supported | No equivalent — requires absolute path |
| Plugin manifest lookup | `.claude-plugin/plugin.json` (preferred) | `plugin.json`, `.claude-plugin/plugin.json`, `.github/plugin/plugin.json` |
| Marketplace descriptor | `.claude-plugin/marketplace.json` | `.github/plugin/marketplace.json` |

### Key confirmed fact: marketplace.json source supports subdirectory paths

Both platforms allow the `source` field to point to any subdirectory within the marketplace repo —
not just the top of `plugins/`. This is confirmed in official documentation:

- Claude Code: _"Paths resolve relative to the marketplace root, which is the directory containing
  `.claude-plugin/`. Must start with `./`."_
  Source: [Creating Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces#plugin-sources)

- Copilot CLI: _"The value of the source field for each plugin is the path to the plugin's
  directory, relative to the root of the repository. It is not necessary to use `./`."_
  Source: [CLI Plugin Reference — marketplace.json](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference#marketplacejson)

This means each platform's marketplace descriptor can independently point to a different
subdirectory of the same plugin:

```json
// .claude-plugin/marketplace.json
{ "name": "terraformer", "source": "./plugins/terraformer/claude" }

// .github/plugin/marketplace.json
{ "name": "terraformer", "source": "plugins/terraformer/copilot" }
```

---

## Chosen Architecture: commons/ + Build Automation

### Layout

```
plugins/<name>/
├── commons/                        ← single source of truth (human-authored)
│   ├── plugin.base.json            ← shared metadata + per-skill visibility markers
│   ├── skills/
│   │   └── <skill-name>/
│   │       └── SKILL.md           ← written once, shared content
│   ├── agents/
│   │   └── <agent-name>.md        ← written once, shared content
│   └── commands/
│       └── <command-name>.md      ← written once, use ${PLUGIN_ROOT} placeholder
├── claude/                         ← GENERATED — do not edit manually
│   ├── plugin.json
│   ├── skills/<skill-name>/SKILL.md
│   ├── agents/<agent-name>.md
│   └── commands/<command-name>.md
└── copilot/                        ← GENERATED — do not edit manually
    ├── plugin.json
    ├── skills/<skill-name>/SKILL.md         (user-invocable skills)
    ├── skills/<skill-name>/workflow.md      (hidden skills — renamed)
    ├── agents/<agent-name>.agent.md         (extension added)
    └── commands/<command-name>.md
```

Generated `claude/` and `copilot/` directories are **committed to the repo** — not gitignored.
This keeps the marketplace self-contained and installable without running the build.

### Build transformations (commons → platform outputs)

| Resource type | commons/ source | → claude/ output | → copilot/ output |
|---------------|----------------|-----------------|------------------|
| User-invocable skill | `SKILL.md` | `SKILL.md` unchanged | `SKILL.md` unchanged |
| Hidden skill | `SKILL.md` + `user-invocable: false` | `SKILL.md` with frontmatter | `workflow.md` (renamed) |
| Agent | `<name>.md` | `<name>.md` unchanged | `<name>.agent.md` (`.agent` inserted) |
| Command | `<name>.md` with `${PLUGIN_ROOT}` | `${CLAUDE_PLUGIN_ROOT}` substituted | absolute path to `copilot/<name>` substituted |
| Manifest | `plugin.base.json` | merged + Claude-specific fields → `plugin.json` | merged + Copilot-specific fields → `plugin.json` |

### Integration with existing pipeline

The build step runs as part of the finalization stage:

```
commons/ → scripts/build-platforms.py → claude/ + copilot/ → marketplace manifests updated
```

`scripts/build-platforms.py` is responsible for applying all transformations and writing both
output trees. It can also be run standalone during local plugin development.

### plugin.base.json schema (proposed)

```json
{
  "name": "terraformer",
  "description": "...",
  "version": "0.1.0",
  "author": { "name": "veiled-market contributors" },
  "skills": [
    { "path": "skills/terraform-plan", "user-invocable": true },
    { "path": "skills/terraform-state", "user-invocable": false }
  ],
  "agents": [
    { "path": "agents/terraformer.md" }
  ],
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json"
}
```

The `user-invocable` flag per skill drives the `workflow.md` rename for Copilot CLI output.

---

## Open Questions

- **`plugin.base.json` schema**: needs formal definition and JSON schema in `schemas/`
- **Command path resolution**: how to handle `${PLUGIN_ROOT}` → absolute path for Copilot CLI
  (absolute path depends on install location, which varies per user)
- **Existing `terraformer` plugin**: currently uses the single-dir layout with no `commons/`
  — needs migration once the build script is implemented
- **CI trigger**: should `build-platforms.py` run on every push to `plugins/*/commons/` or
  only at finalization time?
