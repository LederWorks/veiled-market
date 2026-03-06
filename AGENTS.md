# AGENTS.md — veiled-market

veiled-market is an AI-curated plugin marketplace for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [Claude Code](https://code.claude.com/docs/en/plugins). The repository runs a fully automated four-stage pipeline that discovers skills from 14+ external registries, compiles them into draft plugins via AI, evaluates and enriches drafts, and promotes finalized plugins to `plugins/`.

For format standards, naming conventions, and quality requirements see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

---

## Pipeline lifecycle

```
DISCOVER → COMPILE DRAFT → EVALUATE & ENRICH → FINALIZE
```

### Stage 1 · Discover (`01-discover-skills.yml`)

- **Triggers:** `workflow_dispatch` (manual) or weekly schedule — Monday 06:00 UTC
- **What it does:** Queries GitHub code search, GitHub repo search, and `awesome-copilot` for SKILL.md files and plugin repos matching a given `expertise`. Creates one GitHub Issue per discovered resource.
- **Output:** Issues labeled `expertise/{name}` + `status/discovered` + `ai/discovery`
- **Side effect:** Updates `sources/skill-registry.json` with SHA hashes to skip unchanged resources on future runs.

### Stage 2 · Compile Draft (`02-compile-draft.yml`)

- **Triggers:** An issue is labeled `status/draft` (auto), or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/evaluate.py` to score discovery issues and synthesise a draft plugin into `drafts/{expertise}/`.
- **Output:** A draft PR on branch `draft/{expertise}-{timestamp}`, labeled `status/draft` + `ai/draft`

### Stage 3 · Evaluate & Enrich (`03-evaluate-enrich.yml`)

- **Triggers:** A PR is labeled `status/draft` (auto), or `workflow_dispatch` (manual)
- **What it does:** Collects all open draft PRs for the expertise, checks out each branch, runs `scripts/enrich.py` to pick the best base and merge unique features from the others, closes the draft PRs, and opens a single candidate PR.
- **Output:** A candidate PR on branch `candidate/{expertise}-{timestamp}`, labeled `status/candidate` + `ai/evaluation`

### Stage 4 · Finalize (`04-finalize-plugin.yml`)

- **Triggers:** A `status/candidate` PR is approved (auto), or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/finalize.py --step promote` (moves `drafts/{expertise}/` → `plugins/{expertise}/`) then `--step marketplace` (updates both marketplace manifests). Opens a release PR and closes the candidate PR.
- **Output:** Release PR on branch `finalize/{expertise}-{timestamp}` that, when merged to `main`, publishes the plugin.

---

## Running the pipeline locally

### Prerequisites

```bash
python3 --version   # 3.10+
export GITHUB_TOKEN="your-token-with-repo-scope"
export GITHUB_REPOSITORY="LederWorks/veiled-market"
```

### Run individual scripts

```bash
# Discover — creates issues (--dry-run prints without calling the API)
python3 scripts/discover.py --expertise terraformer --dry-run
python3 scripts/discover.py --expertise terraformer --langs bash,hcl --platforms aws,azure

# Evaluate / compile a draft
python3 scripts/evaluate.py --expertise terraformer --dry-run --output /tmp/my-draft

# Inspect the skill registry
python3 scripts/registry.py stats --expertise terraformer
python3 scripts/registry.py list  --expertise terraformer
python3 scripts/registry.py check github-search owner/repo path/SKILL.md <sha>
```

### Trigger workflows via GitHub CLI

```bash
gh workflow run 01-discover-skills.yml -f expertise=terraformer
gh workflow run 02-compile-draft.yml   -f expertise=terraformer
gh workflow run 03-evaluate-enrich.yml -f expertise=terraformer
gh workflow run 04-finalize-plugin.yml -f expertise=terraformer
```

---

## Data flows

```
sources/marketplaces.json          Registry of sources queried by discover.py
sources/skill-registry.json        SHA-based dedup store; updated by each discovery run
                                   Prevents re-evaluating unchanged skills across runs

drafts/{expertise}/                Temporary staging area created by workflow 02/03
                                   Deleted and promoted to plugins/ by workflow 04

plugins/{expertise}/               Finalized, published plugins

.github/plugin/marketplace.json    Copilot CLI marketplace manifest  ─┐ always updated
.claude-plugin/marketplace.json    Claude Code marketplace manifest   ─┘ together by finalize.py
```

### Skill registry deduplication

`sources/skill-registry.json` stores a SHA-256 of each evaluated resource's content, keyed by `source → plugin_ref → skill_ref`. The `Registry.needs_evaluation()` method returns `False` (skip) when the stored SHA matches the current one, and `True` (evaluate) when the content has changed or the entry is new. The registry is committed back to `main` after each discovery run.

---

## Script dependency graph

All scripts in `scripts/` are standalone Python modules. `registry.py` is a shared utility:

```
discover.py  ──┐
evaluate.py  ──┤── registry.py  (Registry class, content_sha, parse_tags, platform_label)
compose.py   ──┤
enrich.py    ──┘
finalize.py     (standalone; --step promote | --step marketplace)
```

`finalize.py` is the only script that modifies `plugins/` and both marketplace manifests. Always run both steps (`promote` then `marketplace`) together.

---

## Issue and PR lifecycle

```
[Issue: status/discovered]
        │
        │  Human (or automation) applies status/draft label
        ▼
[Issue: status/draft]  ──── triggers workflow 02 ────▶  [Draft PR: status/draft]
                                                                  │
                                                    triggers workflow 03 (on PR label)
                                                                  │
                                                                  ▼
                                              [Candidate PR: status/candidate]
                                                                  │
                                                       PR approval triggers workflow 04
                                                                  │
                                                                  ▼
                                                    [Release PR: status/finalized]
                                                                  │
                                                              merge to main
                                                                  │
                                                                  ▼
                                                       plugins/{expertise}/ published
```

---

## Adding a new expertise

1. Open an issue using the **🧩 Plugin Proposal** template, or trigger discovery directly:
   ```bash
   gh workflow run 01-discover-skills.yml -f expertise=<your-expertise>
   ```
2. Review created issues; label promising ones `status/draft`.
3. Workflow 02 auto-triggers and opens a draft PR.
4. Once multiple drafts exist, run workflow 03 to produce a candidate.
5. Review and approve the candidate PR to trigger workflow 04.

To add a scheduled weekly discovery run for the new expertise, add a `cron` entry to `.github/workflows/01-discover-skills.yml`.

---

## Adding a discovery source

1. Edit `sources/marketplaces.json`:
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
2. If the source has a non-standard format, add a fetcher function in `scripts/discover.py` (following the pattern of `search_github_code`, `fetch_awesome_copilot`, etc.).
3. Open a PR explaining the source and how it was validated.
