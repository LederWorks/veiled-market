# veiled-market

> **The market behind the curtain** — an AI-curated plugin marketplace for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [Claude Code](https://code.claude.com/docs/en/plugins).

[![01 · Discover Skills](https://github.com/LederWorks/veiled-market/actions/workflows/01-discover-skills.yml/badge.svg)](https://github.com/LederWorks/veiled-market/actions/workflows/01-discover-skills.yml)
[![02 · Compile Draft](https://github.com/LederWorks/veiled-market/actions/workflows/02-compile-draft.yml/badge.svg)](https://github.com/LederWorks/veiled-market/actions/workflows/02-compile-draft.yml)
[![03 · Evaluate & Enrich](https://github.com/LederWorks/veiled-market/actions/workflows/03-evaluate-enrich.yml/badge.svg)](https://github.com/LederWorks/veiled-market/actions/workflows/03-evaluate-enrich.yml)
[![04 · Finalize Plugin](https://github.com/LederWorks/veiled-market/actions/workflows/04-finalize-plugin.yml/badge.svg)](https://github.com/LederWorks/veiled-market/actions/workflows/04-finalize-plugin.yml)

---

## 🧭 What is veiled-market?

veiled-market automatically discovers, evaluates, and packages skills, agents, and hooks from dozens of sources into **dual-compatible plugins** that work seamlessly with both GitHub Copilot CLI and Claude Code.

### Key features

| Feature | Description |
|---------|-------------|
| 🔍 **Automated discovery** | GitHub Actions workflows query 14+ skill marketplaces and registries |
| 🤖 **AI evaluation** | GitHub Models (GPT-4o) scores each discovered resource for relevance, quality, and platform fit |
| 📦 **Dual-compatible plugins** | Every plugin works with both Copilot CLI and Claude Code via shared `plugin.json` / `.claude-plugin/` format |
| 🔄 **Lifecycle management** | Issues → drafts → evaluation → enrichment → finalization, all tracked via GitHub Issues and PRs |
| 🌐 **Open marketplace** | `marketplace.json` in both `.github/plugin/` and `.claude-plugin/` for one-command installation |

---

## 📦 Available plugins

| Plugin | Expertise | Version | Skills | Description |
|--------|-----------|---------|--------|-------------|
| [terraformer](plugins/terraformer/) | Infrastructure as Code | 0.1.0 | 8 | Terraform & OpenTofu workflow automation |

---

## 🚀 Quick start

### Add veiled-market as a marketplace

**GitHub Copilot CLI:**
```bash
copilot plugin marketplace add LederWorks/veiled-market
copilot plugin marketplace browse veiled-market
```

**Claude Code:**
```bash
/plugin marketplace add LederWorks/veiled-market
/plugin marketplace browse veiled-market
```

### Install a plugin

**GitHub Copilot CLI:**
```bash
copilot plugin install terraformer@veiled-market
```

**Claude Code:**
```bash
/plugin install terraformer@veiled-market
```

### Or install directly from GitHub

```bash
# Copilot CLI
copilot plugin install LederWorks/veiled-market:plugins/terraformer

# Claude Code
/plugin install LederWorks/veiled-market:plugins/terraformer
```

---

## 🗂 Repository structure

```
veiled-market/
├── .github/
│   ├── plugin/
│   │   └── marketplace.json        # Copilot CLI marketplace manifest
│   ├── workflows/
│   │   ├── 00-setup-labels.yml     # Create GitHub labels
│   │   ├── 01-discover-skills.yml  # Discover skills from sources
│   │   ├── 02-compile-draft.yml    # AI-compile a draft plugin
│   │   ├── 03-evaluate-enrich.yml  # Evaluate drafts, enrich best one
│   │   └── 04-finalize-plugin.yml  # Promote candidate to plugins/
│   └── ISSUE_TEMPLATE/
│       ├── skill-discovery.yml     # Issue template for discoveries
│       └── plugin-proposal.yml     # Issue template for proposals
├── .claude-plugin/
│   └── marketplace.json            # Claude Code marketplace manifest
├── plugins/
│   └── terraformer/                # 🟢 Finalized plugin: Terraform/OpenTofu
│       ├── plugin.json             # Plugin manifest
│       ├── agents/
│       │   └── terraformer.agent.md
│       ├── skills/
│       │   ├── terraform-plan/SKILL.md
│       │   ├── terraform-apply/SKILL.md
│       │   ├── terraform-validate/SKILL.md
│       │   ├── terraform-format/SKILL.md
│       │   ├── terraform-destroy/SKILL.md
│       │   ├── terraform-state/SKILL.md
│       │   ├── terraform-import/SKILL.md
│       │   └── terraform-workspace/SKILL.md
│       ├── hooks.json
│       └── .mcp.json
├── drafts/                         # 🟡 Work-in-progress drafts (auto-managed)
├── sources/
│   └── marketplaces.json           # Registry of queried skill sources
└── scripts/
    ├── discover.py                 # Discovery helper script
    └── evaluate.py                 # AI evaluation helper script
```

---

## 🔄 Automated workflow lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│  LIFECYCLE: expertise → plugin                                       │
│                                                                     │
│  1. DISCOVER (01-discover-skills.yml)                               │
│     ├─ Query 14+ skill marketplaces and GitHub search               │
│     ├─ Create GitHub Issues for each discovery                      │
│     └─ Label: expertise/{name} + status/discovered + source/{src}  │
│                                                                     │
│  2. COMPILE DRAFT (02-compile-draft.yml)                            │
│     ├─ Triggered by: workflow_dispatch or issue labeling            │
│     ├─ AI evaluates & scores each discovery issue                   │
│     ├─ Synthesises a draft plugin from top-scoring resources        │
│     └─ Opens a draft PR: drafts/{expertise}/                        │
│                                                                     │
│  3. EVALUATE & ENRICH (03-evaluate-enrich.yml)                      │
│     ├─ Collects all draft PRs for the expertise                     │
│     ├─ AI picks the best base + enriches with others' features      │
│     ├─ Closes draft PRs and opens a candidate PR                    │
│     └─ Label: status/candidate                                      │
│                                                                     │
│  4. FINALIZE (04-finalize-plugin.yml)                               │
│     ├─ Triggered by: PR approval or workflow_dispatch               │
│     ├─ Promotes drafts/{expertise}/ → plugins/{expertise}/          │
│     ├─ Updates marketplace.json (Copilot + Claude)                  │
│     └─ Opens a release PR → merges to main                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Trigger a discovery run

```bash
# Via GitHub CLI
gh workflow run 01-discover-skills.yml -f expertise=terraformer

# Or visit:
# https://github.com/LederWorks/veiled-market/actions/workflows/01-discover-skills.yml
```

### Scheduled discovery

The discovery workflow runs automatically **every Monday at 06:00 UTC** for the `terraformer` expertise. Add additional scheduled runs in `.github/workflows/01-discover-skills.yml` as the marketplace grows.

---

## 🌐 Queried sources

| Source | Type | Platform |
|--------|------|----------|
| [github/copilot-plugins](https://github.com/github/copilot-plugins) | GitHub marketplace | Copilot CLI |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | GitHub list | Copilot CLI |
| [skillsmp.com](https://skillsmp.com) | Web marketplace | Claude, Codex, ChatGPT |
| [agenticskills.org](https://agenticskills.org) | Open-source dir | Claude, Copilot, Codex |
| [openskills.app](https://openskills.app) | Web marketplace | Claude, Copilot |
| [openagentskills.dev](https://openagentskills.dev) | Community hub | Claude, Copilot, Codex |
| [agentskills.to](https://agentskills.to) | Web marketplace | Claude, Copilot, Codex |
| [antigravityskills.org](https://antigravityskills.org) | Curated list | Claude, Gemini, Cursor, Copilot |
| [skills.sh](https://skills.sh) | CLI sync tool | Universal |
| [buildwithclaude.com](https://buildwithclaude.com) | Claude plugins | Claude Code |
| [claude-plugins.dev](https://claude-plugins.dev) | Community reg | Claude Code |
| [mcpmarket.com/tools/skills](https://mcpmarket.com/tools/skills) | MCP + skills | Claude, Codex, ChatGPT |
| [agentskills.io](https://agentskills.io) | Open standard | Universal |
| GitHub code search | GitHub API | Universal |

---

## 🧩 Plugin format

Every plugin in veiled-market is compatible with both Copilot CLI and Claude Code.

### `plugin.json` (Copilot CLI / Claude Code shared format)

```json
{
  "name": "my-plugin",
  "description": "What this plugin does",
  "version": "1.0.0",
  "author": { "name": "Your Name" },
  "license": "MIT",
  "keywords": ["tag1", "tag2"],
  "agents": "agents/",
  "skills": "skills/",
  "hooks": "hooks.json",
  "mcpServers": ".mcp.json"
}
```

> **Note:** Copilot CLI looks for `plugin.json` in `.github/plugin/plugin.json` or `.claude-plugin/plugin.json` as well as the root. Both tools support the same manifest format.

### Plugin directory structure

```
my-plugin/
├── plugin.json           # Required manifest
├── agents/               # .agent.md files
├── skills/               # Each skill in its own subdirectory with SKILL.md
│   └── my-skill/
│       └── SKILL.md
├── hooks.json            # Pre/PostToolUse hooks
└── .mcp.json             # MCP server configurations
```

### `SKILL.md` format

```markdown
---
name: my-skill
description: Brief description of what this skill does
---

Instructions for the AI to follow when this skill is invoked...
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Proposing new expertises
- Improving existing plugins
- Adding new discovery sources
- Running the workflows locally

### Propose a new expertise

1. Open an issue using the **🧩 Plugin Proposal** template
2. Or trigger the discovery workflow directly: `gh workflow run 01-discover-skills.yml -f expertise=<your-expertise>`

---

## 📄 License

[MIT](LICENSE) — see the LICENSE file for details.
