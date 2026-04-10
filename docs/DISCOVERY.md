# AI Discovery Pipeline

> ⚠️ **Status: SHELVED** — The discovery pipeline generated ~15k issue drafts and is paused.
> Automated triggers (`workflow_run` and `schedule`) have been removed from `01-discovery.yml`.
> The workflow now fires only via `workflow_dispatch` (manual). To re-enable, restore the triggers
> and add appropriate deduplication and rate-limit guards.
> For the active build system, see [docs/PLUGIN-LIFECYCLE.md](PLUGIN-LIFECYCLE.md).

The AI discovery pipeline is a fully automated six-stage GitHub Actions system that discovers
resources (agents, skills, hooks, MCP servers, commands, instructions, workflows) from 8+ external
registries, compiles and AI-evaluates draft plugins via GitHub Models, and promotes finalized
plugins to `plugins/`. All pipeline state flows through `sources/plugins.json` as the single source
of truth; both marketplace manifests are always regenerated together by `finalize.py`.

---

## Pipeline Overview

The pipeline runs in six sequential stages (plus a plugin-proposal pre-stage):

```
PROPOSAL → SETUP → DISCOVER & DRAFT → EVALUATE → ENRICH → FINALIZE
```

| Stage | Workflow | Summary |
|-------|----------|---------|
| Proposal | `05-plugin-proposal.yml` | Issue form → `plugins.json` stub → PR |
| 0 · Setup | `00-setup-plugins.yml` | Schema validation + GitHub Projects v2 creation |
| 1 · Discover | `01-discovery.yml` ⚠️ **SHELVED** | Query 8+ upstream sources → create GitHub Issues |
| 2 · Evaluate | `02-evaluate.yml` | AI-score issues → draft plugin in `drafts/` → draft PR |
| 3 · Enrich | `03-enrich.yml` | AI-enrich best draft → candidate PR |
| 4 · Finalize | `04-finalize-plugin.yml` | Promote `drafts/` → `plugins/` + regenerate manifests |

---

## Workflow Stages

### Plugin Proposal (`05-plugin-proposal.yml`)

- **Triggers:** Issue opened with the `type/plugin` label (created via the **🧩 Plugin Proposal** issue template)
- **What it does:** Parses the issue form fields (`Plugin name`, `Description`), validates kebab-case naming, appends a stub entry to `sources/plugins.json`, and opens a PR on branch `proposal/{plugin}-{timestamp}`. Posts a comment on the issue linking to the PR. If the plugin name already exists, posts an "already exists" comment instead.
- **Output:** PR `feat(plugins): add {plugin} plugin proposal` targeting `main`. Merging it updates `sources/plugins.json`, automatically triggering Stage 0.
- **Permissions:** `contents: write`, `pull-requests: write`, `issues: write`.

### Stage 0 · Setup (`00-setup-plugins.yml`)

- **Triggers:** `push` to `sources/plugins.json` or `sources/marketplaces.json`, or `workflow_dispatch` (manual)
- **What it does:**
  1. **Validates** `sources/plugins.json` against `schemas/plugins.shema.json` and `sources/marketplaces.json` against `schemas/marketplaces.schema.json` — fails fast on schema errors before touching any API.
  2. **GitHub Projects:** Creates (or updates) one GitHub Project in the LederWorks org per plugin — named `veiled-market-{plugin}` — cloning fields and views from the `veiled-market-plugin` org template (project #12, already created). If the project already exists, reviews open issues from previous discovery runs and reconciles them: issues whose `registry.json` entry carries `recommendation: "exclude"` are labeled `status/excluded`.
  3. **Labels:** Calls `00-setup-labels.yml` as a reusable `workflow_call` for each plugin, passing `plugin`, `source_ids`, `lang_tags`, and `platform_tags` so all required GitHub labels exist before discovery begins.
- **Output:** GitHub Projects and labels in place; validation errors abort the run before any downstream workflows fire.
- **Important:** Requires a **GitHub App** (`APP_ID` + `APP_PRIVATE_KEY` secrets) with `Projects: write` org permission and `Contents/Issues/Pull requests: write` repo permissions. The `setup-projects` job uses `actions/create-github-app-token@v1` to mint a short-lived installation token. No long-lived PAT is stored.
- **Permissions:** `contents: read` by default; only the Projects mutation step escalates using the App token.

### Stage 1 · Discover & Draft (`01-discovery.yml`) ⚠️ SHELVED

> **Previously** `01-discover-skills.yml` — renamed because it discovers all resource types (agents, skills, hooks, mcp, commands, instructions, workflows), not only skills.

- **Triggers (original):** `workflow_run` on `00-setup-plugins.yml` (success), `workflow_dispatch` (manual), or weekly schedule — Monday 06:00 UTC
- **Current state:** Automated triggers removed. Only `workflow_dispatch` remains active.
- **What it does:** A `setup` job reads `sources/plugins.json` and emits the ordered plugin list. Discovery runs **sequentially per plugin** — for each plugin a sub-matrix of `(source_id, resource_type)` jobs executes, calling `scripts/discover.py --plugin {name} --source {id} --resource {type}`. Each job scans the source repo via the GitHub Trees API, creates one GitHub Issue per newly discovered resource (assigned to the `veiled-market-{plugin}` GitHub Project via `addProjectV2ItemById` GraphQL), automatically labels each issue `status/draft` to immediately feed Stage 2 without human intervention, and writes a local registry patch via `--registry-output`. When `resource_type` is `plugins`, the script **unwraps** each `plugin.json` and emits its component types as separate issues.
- **Output:** Issues labeled `plugin/{name}` + `status/discovered` + `status/draft` + `type/{resource_type}` + `source/{source_id}` + `ai/discovery`, each assigned to the plugin's GitHub Project.
- **Side effect:** A final `commit-registry` job merges all patches with `registry.py merge-patches` and commits `sources/registry.json` with the message `chore(registry): merge discovery patches [skip ci]` — preventing re-trigger and avoiding parallel write race conditions.
- **Permissions:** `contents: write`, `issues: write`.

### Stage 2 · Evaluate (`02-evaluate.yml`)

- **Triggers:** `workflow_run` on `01-discovery.yml` (success), issue labeled `status/draft`, or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/evaluate.py --plugin {name}` for each plugin — scores all `status/draft` issues and synthesises a draft plugin from the top-scoring resources into `drafts/{plugin}/`; opens a draft PR labeled `status/draft` + `ai/draft`.
- **Output:** One draft PR per plugin on branch `draft/{plugin}-{timestamp}`, labeled `status/draft` + `ai/draft`.
- **Permissions:** `contents: write`, `issues: write`, `pull-requests: write`.

### Stage 3 · Enrich (`03-enrich.yml`)

- **Triggers:** `workflow_run` on `02-evaluate.yml` (success), draft PR opened, or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/enrich.py --plugin {name}` (backed by an AI agent via GitHub Models) on each open draft PR — picks the best base, merges unique features from the others, writes AI evaluation scores (`score.relevance`, `score.quality`, `score.completeness`, `score.platform_fit`, `score.overall`) and `recommendation` to `sources/registry.json`, committed as `chore(registry): write evaluation scores [skip ci]`. Reconciles issues — applies `status/excluded` and closes any where `recommendation == "exclude"`. Closes all draft PRs and opens a single candidate PR.
- **Output:** One candidate PR per plugin on branch `candidate/{plugin}-{timestamp}`, labeled `status/candidate` + `ai/evaluation`.
- **Permissions:** `contents: write`, `issues: write`, `pull-requests: write`.

### Stage 4 · Finalize (`04-finalize-plugin.yml`)

- **Triggers:** A `status/candidate` PR is **merged** to `main` (`pull_request` event, `types: [closed]`, `if: github.event.pull_request.merged == true`), or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/finalize.py --step version` (bumps semver and generates `CHANGELOG.md` in `drafts/{plugin}/`), then `--step promote` (moves `drafts/{plugin}/` → `plugins/{plugin}/`), then `--step marketplace` (reads `sources/plugins.json` as the single source of truth and regenerates both `marketplace.json` files). All automated commits use the format `chore(finalize): promote {plugin} to plugins/ [skip ci]` to prevent re-triggering Stage 0. Opens a release PR.
- **Output:** Release PR on branch `finalize/{plugin}-{timestamp}` that, when merged to `main`, publishes the plugin. `sources/registry.json` and `sources/plugins.json` updated in place.
- **Permissions:** `contents: write`, `pull-requests: write`.

---

## Workflow Trigger Table

| Workflow | Trigger | Key Permissions |
|----------|---------|-----------------|
| `05-plugin-proposal.yml` | Issue labeled `type/plugin` | `contents:write`, `pull-requests:write`, `issues:write` |
| `00-setup-plugins.yml` | Push to `sources/`, manual dispatch | `contents:read` + GitHub App for `projects:write` |
| `00-setup-labels.yml` | Called by `00-setup-plugins.yml` | `issues:write` |
| `01-discovery.yml` ⚠️ **SHELVED** | `workflow_dispatch` only (automated triggers removed) | `issues:write`, `contents:write` |
| `02-evaluate.yml` | After discovery / issue labeled `status/draft`; manual | `contents:write`, `issues:write`, `pull-requests:write` |
| `03-enrich.yml` | Draft PR opened; after evaluate; manual | `contents:write`, `issues:write`, `pull-requests:write` |
| `04-finalize-plugin.yml` | Candidate PR merged to `main`; manual | `contents:write`, `pull-requests:write` |
| `06-build-platforms.yml` | Push to `main` or PR touching `plugins/*/commons/**`; manual | `contents:write` (build job) |
| `ci.yml` | PR touching `sources/`, `schemas/`, or `plugins/*/commons/**` | `contents:read` |

---

## Queried Sources

| Source | Type | Platform |
|--------|------|----------|
| [github/copilot-plugins](https://github.com/github/copilot-plugins) | GitHub marketplace | Copilot CLI |
| [github/awesome-copilot](https://github.com/github/awesome-copilot) | GitHub list | Copilot CLI |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | Official plugins | Claude Code |
| [anthropics/skills](https://github.com/anthropics/skills) | Official skills | Claude Code |
| [antigravityskills.org](https://antigravityskills.org) | Curated list | Claude, Gemini, Cursor, Copilot |
| [buildwithclaude.com](https://buildwithclaude.com) | Claude plugins | Claude Code |
| [clawhub.ai](https://clawhub.ai) | Skill hub | Claude Code |
| [openclawskill.ai](https://openclawskill.ai) | Prompts + skills | Claude Code |

All sources are defined in `sources/marketplaces.json`. Discovery is done entirely via the **GitHub Trees API** — no custom fetchers are needed. Sources use `"type": "marketplace"` for GitHub-hosted plugin repos or `"type": "git"` for plain git repos. The `"repo"` field (`owner/repo`) is required for both types.

---

## Label Namespace

| Prefix | Example | Meaning |
|--------|---------|---------|
| `plugin/` | `plugin/terraformer` | Scopes issue/PR to a named plugin |
| `status/` | `status/draft`, `status/candidate`, `status/finalized`, `status/excluded` | Pipeline stage |
| `type/` | `type/skill`, `type/agent`, `type/hook`, `type/mcp`, `type/plugin` | Artefact type |
| `lang/` | `lang/hcl`, `lang/bash` | Primary language |
| `platform/csp/` | `platform/csp/aws` | Cloud provider target |
| `platform/ci/` | `platform/ci/github-actions` | CI platform target |
| `platform/saas/` | `platform/saas/terraform-cloud` | SaaS platform target |
| `ai/` | `ai/discovery`, `ai/draft`, `ai/evaluation` | AI pipeline step that produced the item |
| `source/` | `source/<source-id>` | Upstream discovery source |

Full status progression: `discovered` → `draft` → `candidate` → `finalized` (or `excluded`).

Labels are created by `00-setup-labels.yml` before discovery begins. Every issue created by `01-discovery.yml` carries: `plugin/{name}` + `status/discovered` + `status/draft` + `type/{resource_type}` + `source/{source_id}` + `ai/discovery`.

---

## Security Posture

- `permissions: {}` declared at workflow level; minimum scopes granted per-job only.
- **GitHub App** (`APP_ID` + `APP_PRIVATE_KEY` secrets) used exclusively for GitHub Projects v2 write access via `actions/create-github-app-token@v1` — produces short-lived installation tokens.
- No long-lived PATs anywhere in the pipeline.
- All bot commits carry `[skip ci]` to prevent cascade trigger loops.
- Any dynamic secret values are masked with `::add-mask::` before logging.

---

## Running the Pipeline Locally

### Prerequisites

```bash
python3 --version   # 3.10+
export GITHUB_TOKEN="your-github-token"   # PAT or token with repo scope (read/write)
export GITHUB_REPOSITORY="LederWorks/veiled-market"
# For GitHub Projects v2 mutations (Stage 0 only), the workflow uses a GitHub App
# (APP_ID + APP_PRIVATE_KEY secrets) — no long-lived PAT required in CI.
```

### Run individual scripts

```bash
# Discover — creates issues (--dry-run prints without calling the API)
python3 scripts/discover.py --plugin terraformer --dry-run
python3 scripts/discover.py --plugin terraformer --langs bash,hcl --platforms aws,azure

# Limit to a single source or resource type (mirrors matrix job inputs)
python3 scripts/discover.py --plugin terraformer --source github-awesome-copilot --resource skills
python3 scripts/discover.py --plugin terraformer --keywords terraform --registry-output patches/patch.json

# Compile & evaluate a draft (Stage 2)
python3 scripts/evaluate.py --plugin terraformer --dry-run --output my-draft/
python3 scripts/enrich.py   --plugin terraformer --dry-run

# Inspect the skill registry
python3 scripts/registry.py stats --plugin terraformer
python3 scripts/registry.py list  --plugin terraformer
python3 scripts/registry.py check <source-id> owner/repo path/SKILL.md <sha>

# Merge registry patch files produced by parallel discover jobs
python3 scripts/registry.py merge-patches patches/*.json
```

### Trigger workflows via GitHub CLI

```bash
gh workflow run 01-discovery.yml        -f plugin=terraformer
gh workflow run 02-evaluate.yml         -f plugin=terraformer
gh workflow run 03-enrich.yml           -f plugin=terraformer
gh workflow run 04-finalize-plugin.yml  -f plugin=terraformer
```

---

## Data Flows

```
sources/plugins.json               Single source of truth for all plugins
                                   Updated by: plugin-proposal PR, finalize.py [skip ci], manual edit

sources/marketplaces.json          Registry of discovery sources queried by discover.py
                                   Triggers 00-setup-plugins.yml on change

sources/registry.json              SHA-based dedup store + evaluation scores + finalized plugin index
                                   Updated by: discovery patches [skip ci], evaluate scores [skip ci]

drafts/{plugin}/                   Temporary staging area created by workflow 02
                                   Deleted and promoted to plugins/ by workflow 04

plugins/{plugin}/                  Finalized, published plugins

.github/plugin/marketplace.json    Copilot CLI marketplace manifest  ─┐ generated by
.claude-plugin/marketplace.json    Claude Code marketplace manifest   ─┘ finalize.py from sources/plugins.json
```

### Central config: `sources/plugins.json`

`sources/plugins.json` (validated against `schemas/plugins.shema.json`) is the **single source of truth** for all plugins. It holds marketplace-level metadata and the canonical plugin list. `finalize.py --step marketplace` reads this file and regenerates both `marketplace.json` output files — neither manifest is ever edited manually.

The file is updated in three ways:
- **Manual edit** — adding new plugins like `easy-github`, `easy-kubernetes`
- **Plugin-proposal issue template** → PR that updates `plugins.json`
- **`finalize.py --step marketplace`** commit, using `[skip ci]` to avoid re-triggering Stage 0

### Resource registry deduplication

`sources/registry.json` (validated against `schemas/registry.schema.json`) tracks every evaluated resource by `source → plugin_ref → skill_ref`. Every leaf entry records `resource_type`, `sha` (content hash), AI evaluation scores (`score.*`), `recommendation`, and `issue_number`. The `Registry.needs_evaluation()` method returns `False` (skip) when the stored SHA matches the current one, and `True` (evaluate) when changed or new.

Because discovery runs as a parallel matrix, each job writes a local patch file via `--registry-output` rather than committing directly. The `commit-registry` job merges all patches with `registry.py merge-patches` and commits with `[skip ci]` — preventing re-trigger and avoiding race conditions.

### Commit convention: `[skip ci]`

Any workflow step that commits files back to `main` **must** include `[skip ci]` in the commit message. All automated commits follow [Conventional Commits](https://www.conventionalcommits.org/) with `[skip ci]` appended:

```
chore(registry): merge discovery patches [skip ci]
chore(registry): write evaluation scores [skip ci]
chore(finalize): promote terraformer to plugins/ [skip ci]
chore(marketplace): regenerate manifests [skip ci]
```

### Script dependency graph

```
discover.py  ──┐
evaluate.py  ──┤── registry.py  (Registry class, content_sha, parse_tags, platform_label)
compose.py   ──┤
enrich.py    ──┘
finalize.py     (standalone; --step promote | --step marketplace)
```

`finalize.py` is the only script that modifies `plugins/` and both marketplace manifests. Always run both steps (`promote` then `marketplace`) together.

---

## Issue and PR Lifecycle

```
[Stage 1: Discovery] ─ creates issues labeled status/draft (automatic)
        │
        │  triggers workflow 02 (on issue labeled status/draft)
        ▼
[Stage 2: Evaluate] ──────────────────▶  [Draft PR: status/draft]
                                                                  │
                                              triggers workflow 03 (on PR opened)
                                                                  │
                                                                  ▼
                                              [Candidate PR: status/candidate]
                                                                  │
                                                    PR merge triggers workflow 04
                                                                  │
                                                                  ▼
                                                    [Release PR: status/finalized]
                                                                  │
                                                              merge to main
                                                                  │
                                                                  ▼
                                                       plugins/{plugin}/ published
```

---

## Adding a New Plugin via Pipeline

1. Open an issue using the **🧩 Plugin Proposal** template, or trigger discovery directly:
   ```bash
   gh workflow run 01-discovery.yml -f plugin=<your-plugin>
   ```
2. Discovery automatically labels every found resource `status/draft` — no manual labeling needed.
3. Workflow 02 (Evaluate) auto-triggers and compiles a draft PR per plugin.
4. Workflow 03 (Enrich) auto-triggers and enriches the draft into a candidate PR.
5. Review and merge the candidate PR to trigger workflow 04 (finalize).

To add a scheduled weekly discovery run for the new plugin, add a `cron` entry to `.github/workflows/01-discovery.yml`.

---

## Adding a Discovery Source

1. Edit `sources/marketplaces.json`:
   ```json
   {
     "id": "my-source",
     "name": "My Source Name",
     "type": "marketplace",
     "repo": "owner/repo",
     "url": "https://example.com",
     "description": "What this source offers",
     "resources": ["agents", "skills", "plugins"]
   }
   ```
   - Use `"type": "marketplace"` for GitHub-hosted plugin repos (e.g. `github/awesome-copilot`) or `"type": "git"` for plain git repos.
   - The `"repo"` field (`owner/repo`) is required for both types — discovery is done entirely via the GitHub Trees API.
   - List every resource type the repo contains in `"resources"`. When `plugins` is listed, component types are also automatically unwrapped.
2. No custom fetcher function is needed — the Trees API handler covers all `marketplace` and `git` sources.
3. Open a PR explaining the source and how it was validated.

Committing to `sources/marketplaces.json` automatically triggers `00-setup-plugins.yml` (Stage 0) which will validate the new entry and set up labels before the next discovery run.

---

## Plugin Status

### Pipeline-Finalized Plugins

Plugins that have been fully discovered, enriched, and promoted from `drafts/` to `plugins/`:

| Plugin | Status | Notes |
|--------|--------|-------|
| `terraformer` | ✅ Finalized | Fully promoted to `plugins/`; 8 skills, agent, hooks, MCP config |

### Draft Plugins (AI Pipeline Stubs)

These plugins exist in `drafts/` but require enrichment before promotion. All 7 are stubs produced when AI (GitHub Models) was unavailable during Stage 2 evaluation:

| Plugin | Status | Notes |
|--------|--------|-------|
| `easy-aws` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |
| `easy-azure` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |
| `easy-azuredevops` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |
| `easy-gcp` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |
| `easy-github` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |
| `easy-kubernetes` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |
| `easy-oci` | ⚠️ Stub | AI unavailable during evaluation; needs manual enrichment |

Stubs contain `"description": "Auto-generated easy-<name> plugin (AI unavailable)"` in `plugin.json` and `ENRICHMENT_NOTES.md` stating `"AI evaluation was unavailable; manual enrichment required."`.

**These must not be promoted to `plugins/` in their current stub state.**

**To re-evaluate stubs:** Trigger `02-evaluate.yml` manually via GitHub Actions (`workflow_dispatch`) for each stub plugin. Alternatively, manually enrich `ENRICHMENT_NOTES.md` and the draft `plugin.json`, then open a candidate PR following the format of the `terraformer` promotion.

---

## Known Issues and Constraints

### 4. Most `drafts/` entries are AI-unavailable stubs

Only `terraformer` has been fully enriched and promoted via the AI pipeline. The 7 remaining drafts (`easy-*`) require manual enrichment or re-triggering `02-evaluate.yml`. They must not be promoted to `plugins/` in their current stub state.

### 5. `[skip ci]` is required on all bot commits

Any automated commit missing this tag re-enters the pipeline at `01-discovery.yml` or `02-evaluate.yml`, causing a cascade loop that consumes workflow minutes and creates duplicate issues. **This is a hard operational rule, not a preference.**

### 6. `01-discovery.yml` is shelved (the deduplication problem)

Automated triggers (`workflow_run` and `schedule`) have been removed from `01-discovery.yml` after it generated approximately **15,000 issue drafts**. The root cause was absent per-source deduplication: the pipeline created a new issue for every discovered resource on every run, with no guard against re-discovering resources that were already tracked.

The workflow now fires only via `workflow_dispatch`. To resume automated discovery, the following guards must be added first:
- Per-source issue deduplication (check for existing open issues with the same `source/` + `plugin/` label before creating a new one)
- A rate-limit or maximum-issues-per-run guard
- Review of the `setup` job trigger condition to avoid re-running on non-source-changing pushes

---

## Resuming the Pipeline

### Discovery Pipeline Resumption

`01-discovery.yml` is currently shelved (see constraint #6 above). Before re-enabling automated triggers, the following must be implemented:

1. **Per-source deduplication:** Before creating an issue, query open issues with the same `source/{source_id}` and `plugin/{name}` labels. Skip creation if a matching issue already exists.
2. **Rate-limiting guard:** Add a maximum-issues-per-run cap (e.g., 50–100 issues per workflow run) to prevent runaway creation.
3. **Trigger review:** Audit the `setup` job trigger condition to ensure it only fires when `sources/` changes are meaningful.
4. **Re-add triggers:** Restore `workflow_run` (on `00-setup-plugins.yml`) and `schedule` (Monday 06:00 UTC) to `.github/workflows/01-discovery.yml`.

To re-enable: move `01-discovery.yml` back to `.github/workflows/` if it was moved to `dev/`, and restore the trigger block:
```yaml
on:
  workflow_run:
    workflows: ["00 · Setup"]
    types: [completed]
  schedule:
    - cron: '0 6 * * 1'   # Monday 06:00 UTC
  workflow_dispatch:
    inputs:
      plugin:
        description: 'Plugin name to discover for'
        required: false
```

### Draft Plugin Enrichment

The 7 `easy-*` stub plugins in `drafts/` need manual enrichment or re-evaluation via `02-evaluate.yml` before they can be promoted to `plugins/`. Options:

**Option A — Re-trigger AI evaluation:**
```bash
gh workflow run 02-evaluate.yml -f plugin=easy-github
gh workflow run 02-evaluate.yml -f plugin=easy-aws
# ... repeat for each stub
```

**Option B — Manual enrichment:**
1. Open `drafts/<plugin>/ENRICHMENT_NOTES.md` and follow the instructions.
2. Edit `drafts/<plugin>/plugin.json` with accurate metadata.
3. Add/improve skills in `drafts/<plugin>/skills/`.
4. Open a candidate PR following the `terraformer` promotion format (label: `status/candidate` + `ai/evaluation`).
5. Merge the candidate PR to trigger Stage 4 (finalize).

### Completed Pipeline Items (TODO audit)

All pipeline design items have been implemented. The following cross-cutting tasks are complete:

- [x] Plugin-proposal issue template → `05-plugin-proposal.yml` workflow opens a PR updating `sources/plugins.json`
- [x] Schema validation job in `ci.yml` — runs on all PRs that touch `sources/` or `schemas/`
- [x] `concurrency:` group on every workflow to prevent cascade overlaps
- [x] `permissions: {}` (deny-all) at workflow top level with minimum per-job grants
- [x] `::add-mask::` on all dynamic secret values before logging
- [x] GitHub App strategy: `APP_ID` + `APP_PRIVATE_KEY` — short-lived installation tokens via `actions/create-github-app-token@v1`
- [x] `commit-registry` uses `[skip ci]` to prevent cascade trigger loops
- [x] Issue reconciliation: `status/excluded` applied where `recommendation == "exclude"`

---

## GitHub Actions Workflows

All discovery workflows live in `.github/workflows/` (active) or have been moved to `.github/workflows/dev/` (archived). The full list:

| Workflow File | Purpose | Status |
|---------------|---------|--------|
| `05-plugin-proposal.yml` | Issue form (type/plugin) → `plugins.json` stub → PR | ✅ Active |
| `00-setup-plugins.yml` | Schema validation + GitHub Projects v2 creation + label setup | ✅ Active |
| `00-setup-labels.yml` | Reusable: create/validate GitHub label namespace | ✅ Active (called by setup) |
| `01-discovery.yml` | Query 8+ upstream sources via GitHub Trees API → create GitHub Issues | ⚠️ Shelved (`workflow_dispatch` only) |
| `02-evaluate.yml` | AI-score `status/draft` issues → synthesise draft plugin → open draft PR | ✅ Active |
| `03-enrich.yml` | AI-enrich best-scored draft → open candidate PR | ✅ Active |
| `04-finalize-plugin.yml` | Promote `drafts/{plugin}/` → `plugins/` + regenerate both marketplace manifests | ✅ Active |

Supporting workflows (not part of the discovery pipeline):

| Workflow File | Purpose |
|---------------|---------|
| `06-build-platforms.yml` | Commons build: `commons/` → `claude/` + `copilot/` per plugin |
| `ci.yml` | PR guard: schema-validate `sources/`, `schemas/`, `plugins/*/commons/` |

To re-enable discovery: restore automated triggers in `01-discovery.yml` (see [Resuming the Pipeline](#resuming-the-pipeline)).
