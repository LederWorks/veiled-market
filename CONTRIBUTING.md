# Contributing to veiled-market

Thank you for helping grow the AI plugin marketplace! This document explains how to contribute plugins, skills, and discovery sources.

## Table of contents

- [Code of conduct](#code-of-conduct)
- [Ways to contribute](#ways-to-contribute)
- [Proposing a new expertise](#proposing-a-new-expertise)
- [Improving an existing plugin](#improving-an-existing-plugin)
- [Adding a discovery source](#adding-a-discovery-source)
- [Running workflows locally](#running-workflows-locally)
- [Plugin quality standards](#plugin-quality-standards)
- [Commit conventions](#commit-conventions)

---

## Code of conduct

Be kind and constructive. This is a community-driven project; contributions at all skill levels are welcome.

---

## Ways to contribute

| How | When to use |
|-----|-------------|
| Open a **🔍 Skill Discovery** issue | You found a useful skill/plugin on an external marketplace |
| Open a **🧩 Plugin Proposal** issue | You want a new expertise added to the marketplace |
| Submit a **PR to `plugins/`** | You want to directly improve an existing plugin |
| Run the **01-discover** workflow | You want to trigger an automated search for a new expertise |
| Edit `sources/marketplaces.json` | You know of a new skill marketplace to query |

---

## Proposing a new expertise

1. **Check** whether an expertise already exists: browse [`plugins/`](plugins/) and open [Issues](https://github.com/LederWorks/veiled-market/issues?q=label%3Atype%2Fplugin).

2. **Open a proposal issue** using the [🧩 Plugin Proposal](.github/ISSUE_TEMPLATE/plugin-proposal.yml) template.

3. **Trigger discovery** (optional, requires write access or a maintainer to run):
   ```bash
   gh workflow run 01-discover-skills.yml \
     -f expertise=<your-expertise>
   ```

4. **Review discovered issues** — the workflow creates one issue per discovered resource, labeled `expertise/<name>` + `status/discovered`.

5. **Label good discoveries** with `status/draft` to include them in the next compile run.

6. The **02-compile-draft** workflow will auto-trigger and open a draft PR.

---

## Improving an existing plugin

1. Fork the repository and create a branch: `git checkout -b fix/terraformer-plan-skill`.

2. Edit files in `plugins/<expertise>/`.

3. Follow the [plugin quality standards](#plugin-quality-standards) below.

4. Open a PR with a clear description of what changed and why.

### Adding a new skill

1. Create a new directory: `plugins/<expertise>/skills/<skill-name>/`
2. Add a `SKILL.md` file with the required frontmatter:
   ```markdown
   ---
   name: skill-name
   description: Brief description (max 200 chars)
   ---

   ## Instructions

   Step-by-step instructions for the AI...
   ```
3. Update `plugins/<expertise>/plugin.json` if the `skills` path needs changing (usually not needed).

### Adding a new agent

1. Create `plugins/<expertise>/agents/<name>.agent.md`:
   ```markdown
   ---
   name: agent-name
   description: What this agent specialises in
   tools: ["bash", "view", "edit"]
   ---

   You are a specialist in...
   ```

---

## Adding a discovery source

1. Edit [`sources/marketplaces.json`](sources/marketplaces.json) and add an entry:
   ```json
   {
     "id": "my-source",
     "name": "My Source Name",
     "type": "web",
     "url": "https://example.com",
     "search_url": "https://example.com/search?q={expertise}",
     "platform": ["claude", "copilot"],
     "description": "What this source offers"
   }
   ```

2. If the source has a non-standard format, add a parser function in `scripts/discover.py`.

3. Open a PR explaining the source and how it was tested.

---

## Running workflows locally

You can test the discovery and evaluation scripts locally with `--dry-run`.

### Prerequisites

```bash
python3 --version  # 3.10+
export GITHUB_TOKEN="your-token-with-repo-scope"
export GITHUB_REPOSITORY="LederWorks/veiled-market"
```

### Run discovery

```bash
python3 scripts/discover.py --expertise terraformer --dry-run
```

### Run evaluation

```bash
python3 scripts/evaluate.py --expertise terraformer --dry-run --output /tmp/my-draft
```

### Run the full workflow via GitHub CLI

```bash
# Step 1: discover
gh workflow run 01-discover-skills.yml -f expertise=terraformer

# Step 2: compile a draft (after reviewing discovered issues)
gh workflow run 02-compile-draft.yml -f expertise=terraformer

# Step 3: evaluate (after multiple drafts exist)
gh workflow run 03-evaluate-enrich.yml -f expertise=terraformer

# Step 4: finalize (after approving the candidate PR)
gh workflow run 04-finalize-plugin.yml -f expertise=terraformer
```

---

## Plugin quality standards

All plugins must meet these standards to be merged:

### Required
- [ ] `plugin.json` with `name`, `version`, `description`, `license`
- [ ] At least one skill or agent
- [ ] Every `SKILL.md` has valid frontmatter (`name`, `description`)
- [ ] No hard-coded secrets, credentials, or personal data
- [ ] Works with both Copilot CLI and Claude Code

### Recommended
- [ ] Hooks only use `bash` type commands with safe, side-effect-free logic
- [ ] MCP server configs use environment variables for API keys (not hard-coded)
- [ ] Skills include error handling guidance
- [ ] Agent system prompt includes safety behaviour (e.g. "ask before destroying")
- [ ] Keywords and tags are relevant (not spammy)

### Naming conventions

| Item | Convention |
|------|-----------|
| Plugin name | `kebab-case`, max 64 chars |
| Skill name | `kebab-case` (matches directory name) |
| Agent file | `name.agent.md` |
| Version | Semantic versioning: `MAJOR.MINOR.PATCH` |

---

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(terraformer): add terraform-test skill
fix(terraformer): correct terraform-apply confirmation prompt
docs: update contributing guide
chore(sources): add skillsmp.com to marketplaces.json
```

---

## Questions?

Open a [Discussion](https://github.com/LederWorks/veiled-market/discussions) or an issue with your question.
