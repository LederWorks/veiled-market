# veiled-market

> **The market behind the curtain** — an AI-curated plugin marketplace for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [Claude Code](https://code.claude.com/docs/en/plugins).

[![00 · Setup](https://github.com/LederWorks/veiled-market/actions/workflows/00-setup-plugins.yml/badge.svg)](https://github.com/LederWorks/veiled-market/actions/workflows/00-setup-plugins.yml)

---

## 🧭 What is veiled-market?

veiled-market automatically discovers, evaluates, and packages skills, agents, and hooks from dozens of sources into **dual-compatible plugins** that work seamlessly with both GitHub Copilot CLI and Claude Code.

### Key features

| Feature | Description |
|---------|-------------|
| 🤖 **AI evaluation** | GitHub Models (GPT-4o) scores each discovered resource for relevance, quality, and platform fit |
| 📦 **Dual-compatible plugins** | Every plugin works with both Copilot CLI and Claude Code via shared `plugin.json` / `.claude-plugin/` format |
| 🔄 **Lifecycle management** | Issues → drafts → evaluation → enrichment → finalization, all tracked via GitHub Issues and PRs |
| 🌐 **Open marketplace** | `marketplace.json` in both `.github/plugin/` and `.claude-plugin/` for one-command installation |

---

## 📦 Available plugins

| Plugin | Status | Version | Description |
|--------|--------|---------|-------------|
| [terraformer](plugins/terraformer/) | 🟢 Published | 0.1.0 | Terraform & OpenTofu workflow automation |
| easy-github | 🔵 Planned | — | GitHub repos, PRs, issues, Actions, releases |
| easy-azuredevops | 🔵 Planned | — | Azure DevOps pipelines, boards, repos, artifacts |
| easy-azure | 🔵 Planned | — | Azure CLI, Bicep/ARM, networking, identity |
| easy-aws | 🔵 Planned | — | AWS CLI, CloudFormation, IAM, S3, EC2 |
| easy-gcp | 🔵 Planned | — | gcloud, Deployment Manager, GKE, Cloud Run |
| easy-oci | 🔵 Planned | — | OCI CLI, compartments, compute, storage |
| easy-kubernetes | 🔵 Planned | — | kubectl, Helm, manifest management, debugging |

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
│   │   ├── ci.yml                  # Schema validation
│   │   ├── 06-build-platforms.yml  # Commons build: generate claude/ + copilot/
│   │   └── dev/                    # 7 archived discovery workflows (shelved)
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


> **AI Discovery Pipeline:** This workflow is currently shelved. See [docs/DISCOVERY.md](docs/DISCOVERY.md) for full documentation.

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

[Apache V2.0](LICENSE) — see the LICENSE file for details.
