# AGENTS.md — veiled-market

veiled-market is an AI-curated plugin marketplace for [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [Claude Code](https://code.claude.com/docs/en/plugins). The repository runs a fully automated six-stage pipeline (Stages 0–4 plus a plugin-proposal workflow) that discovers resources from 8+ external registries, compiles and evaluates draft plugins via AI, and promotes finalized plugins to `plugins/`.

For format standards, naming conventions, and quality requirements see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

> **For AI assistants:** At the end of every task, update this file (`AGENTS.md`), `.github/copilot-instructions.md`, and any relevant `README.md` files to reflect the changes made. Maintain a task list in the conversation to track progress and tick off completed items before finishing.

---

## Pipeline lifecycle

```
PROPOSAL → SETUP → DISCOVER & DRAFT → EVALUATE → ENRICH → FINALIZE
```

### Plugin Proposal (`05-plugin-proposal.yml`)

- **Triggers:** Issue opened with the `type/plugin` label (created via the **🧩 Plugin Proposal** issue template)
- **What it does:** Parses the issue form fields (`Plugin name`, `Description`), validates kebab-case naming, appends a stub entry to `sources/plugins.json`, and opens a PR on branch `proposal/{plugin}-{timestamp}`. Posts a comment on the issue linking to the PR. If the plugin name already exists, posts an "already exists" comment instead.
- **Output:** PR `feat(plugins): add {plugin} plugin proposal` targeting `main`. Merging it updates `sources/plugins.json`, automatically triggering Stage 0.
- **Permissions:** `permissions: contents: write, pull-requests: write, issues: write`.

### Stage 0 · Setup (`00-setup-plugins.yml`)

- **Triggers:** `push` to `sources/plugins.json` or `sources/marketplaces.json`, or `workflow_dispatch` (manual)
- **What it does:**
  1. **Validates** `sources/plugins.json` against `schemas/plugins.shema.json` and `sources/marketplaces.json` against `schemas/marketplaces.schema.json` — fails fast on schema errors before touching any API.
  2. **GitHub Projects:** Creates (or updates) one GitHub Project in the LederWorks org per plugin — named `veiled-market-{plugin}` — cloning fields and views from the `veiled-market-plugin` org template (project #12, already created). If the project already exists, reviews open issues from previous discovery runs and reconciles them: issues whose `registry.json` entry carries `recommendation: "exclude"` are labeled `status/excluded`.
  3. **Labels:** Calls `00-setup-labels.yml` as a reusable `workflow_call` for each plugin, passing `plugin`, `source_ids`, `lang_tags`, and `platform_tags` so all required GitHub labels exist before discovery begins.
- **Output:** GitHub Projects and labels in place; validation errors abort the run before any downstream workflows fire.
- **Important:** Requires a **GitHub App** (`APP_ID` + `APP_PRIVATE_KEY` secrets) with `Projects: write` org permission and `Contents/Issues/Pull requests: write` repo permissions. The `setup-projects` job uses `actions/create-github-app-token@v1` to mint a short-lived installation token, which is then passed as `env: GITHUB_TOKEN:` to the GraphQL steps. No long-lived PAT is stored.
- **Permissions:** Job-level `permissions: contents: read` by default; only the Projects mutation step escalates to the PAT.

### Stage 1 · Discover & Draft (`01-discovery.yml`)

> **Previously** `01-discover-skills.yml` — renamed because it discovers all resource types (agents, skills, hooks, mcp, commands, instructions, workflows), not only skills.

- **Triggers:** `workflow_run` on `00-setup-plugins.yml` (success), or `workflow_dispatch` (manual), or weekly schedule — Monday 06:00 UTC
- **What it does:** A `setup` job reads `sources/plugins.json` and emits the ordered plugin list. Discovery runs **sequentially per plugin** — for each plugin a sub-matrix of `(source_id, resource_type)` jobs executes, calling `scripts/discover.py --plugin {name} --source {id} --resource {type}`. Each job scans the source repo via the GitHub Trees API, creates one GitHub Issue per newly discovered resource (assigned to the `veiled-market-{plugin}` GitHub Project via `addProjectV2ItemById` GraphQL), automatically labels each issue `status/draft` to immediately feed Stage 2 without human intervention, and writes a local registry patch via `--registry-output`. When `resource_type` is `plugins`, the script **unwraps** each `plugin.json` and emits its component types as separate issues.
- **Output:** Issues labeled `plugin/{name}` + `status/discovered` + `status/draft` + `type/{resource_type}` + `source/{source_id}` + `ai/discovery`, each assigned to the plugin's GitHub Project.
- **Side effect:** A final `commit-registry` job merges all patches with `registry.py merge-patches` and commits `sources/registry.json` with the message `chore(registry): merge discovery patches [skip ci]` — preventing re-trigger and avoiding parallel write race conditions.
- **Permissions:** `permissions: contents: write, issues: write` — all other GitHub API calls use the default token.

### Stage 2 · Evaluate (`02-evaluate.yml`)

- **Triggers:** `workflow_run` on `01-discovery.yml` (success), issue labeled `status/draft`, or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/evaluate.py --plugin {name}` for each plugin — scores all `status/draft` issues and synthesises a draft plugin from the top-scoring resources into `drafts/{plugin}/`; opens a draft PR labeled `status/draft` + `ai/draft`.
- **Output:** One draft PR per plugin on branch `draft/{plugin}-{timestamp}`, labeled `status/draft` + `ai/draft`.
- **Permissions:** `permissions: contents: write, issues: write, pull-requests: write`.

### Stage 3 · Enrich (`03-enrich.yml`)

- **Triggers:** `workflow_run` on `02-evaluate.yml` (success), draft PR opened, or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/enrich.py --plugin {name}` (backed by an AI agent via GitHub Models) on each open draft PR — picks the best base, merges unique features from the others, writes AI evaluation scores (`score.relevance`, `score.quality`, `score.completeness`, `score.platform_fit`, `score.overall`) and `recommendation` to `sources/registry.json`, committed as `chore(registry): write evaluation scores [skip ci]`. Reconciles issues — applies `status/excluded` and closes any where `recommendation == "exclude"`. Closes all draft PRs and opens a single candidate PR.
- **Output:** One candidate PR per plugin on branch `candidate/{plugin}-{timestamp}`, labeled `status/candidate` + `ai/evaluation`.
- **Permissions:** `permissions: contents: write, issues: write, pull-requests: write`.

### Stage 4 · Finalize (`04-finalize-plugin.yml`)

- **Triggers:** A `status/candidate` PR is **merged** to `main` (`pull_request` event, `types: [closed]`, `if: github.event.pull_request.merged == true`), or `workflow_dispatch` (manual)
- **What it does:** Runs `scripts/finalize.py --step version` (bumps semver and generates `CHANGELOG.md` in `drafts/{plugin}/`), then `--step promote` (moves `drafts/{plugin}/` → `plugins/{plugin}/`), then `--step marketplace` (reads `sources/plugins.json` as the single source of truth and regenerates both `marketplace.json` files). All automated commits use the format `chore(finalize): promote {plugin} to plugins/ [skip ci]` to prevent re-triggering Stage 0. Opens a release PR.
- **Output:** Release PR on branch `finalize/{plugin}-{timestamp}` that, when merged to `main`, publishes the plugin. `sources/registry.json` and `sources/plugins.json` updated in place.
- **Permissions:** `permissions: contents: write, pull-requests: write`.

---

## Running the pipeline locally

### Prerequisites

```bash
python3 --version   # 3.10+
export GITHUB_TOKEN="your-github-token"          # PAT or token with repo scope (read/write)
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
python3 scripts/discover.py --plugin terraformer --keywords terraform --registry-output /tmp/patch.json

# Compile & evaluate a draft (Stage 2)
python3 scripts/evaluate.py --plugin terraformer --dry-run --output /tmp/my-draft
python3 scripts/enrich.py   --plugin terraformer --dry-run

# Inspect the skill registry
python3 scripts/registry.py stats --plugin terraformer
python3 scripts/registry.py list  --plugin terraformer
python3 scripts/registry.py check <source-id> owner/repo path/SKILL.md <sha>

# Merge registry patch files produced by parallel discover jobs
python3 scripts/registry.py merge-patches /tmp/patches/*.json
```

### Trigger workflows via GitHub CLI

```bash
gh workflow run 01-discovery.yml        -f plugin=terraformer
gh workflow run 02-evaluate.yml         -f plugin=terraformer
gh workflow run 03-enrich.yml           -f plugin=terraformer
gh workflow run 04-finalize-plugin.yml  -f plugin=terraformer
```

---

## Data flows

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

Any workflow step that commits files back to `main` (registry patches, marketplace regeneration, finalization) **must** include `[skip ci]` in the commit message. GitHub Actions recognises this string and skips all workflow triggers for that commit — preventing cascade loops.

All automated commits must also follow [Conventional Commits](https://www.conventionalcommits.org/) with `[skip ci]` appended to the subject:

```
chore(registry): merge discovery patches [skip ci]
chore(registry): write evaluation scores [skip ci]
chore(finalize): promote terraformer to plugins/ [skip ci]
chore(marketplace): regenerate manifests [skip ci]
```

(`[no ci]` is the GitHub-documented equivalent; `[skip ci]` is preferred here for consistency with Conventional Commits tooling.)

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

## Adding a new plugin

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

## Adding a discovery source

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

---

## TODO — items required to complete the new pipeline design

The pipeline design above is the **target state**. The following items track what still needs to be built to reach it.

### Stage 0 · `00-setup-plugins.yml` (new workflow)

- [x] Create `00-setup-plugins.yml` — triggers on `push` to `sources/plugins.json` or `sources/marketplaces.json`
- [x] JSON schema validation step: validate both source files against their schemas (e.g. `ajv-cli` or Python `jsonschema`)
- [x] Create `APP_ID` and `APP_PRIVATE_KEY` secrets — register a `veiled-market-pipeline` GitHub App in the LederWorks org with `Projects: write` (org) and `Contents/Issues/Pull requests: write` (repo), install it on `veiled-market`, then add the App ID and private key as repository secrets
- [x] ~~Create the `veiled-market-plugin` template project in the LederWorks org~~ — created as project #12
- [x] GitHub Projects v2 GraphQL mutations: create/upsert `veiled-market-{plugin}` project per plugin, cloning fields and views from template #12
- [x] Implement "reconcile previous draft issues" logic — query open issues by `plugin/{name}` label, cross-reference `registry.json` `recommendation` field, apply `status/excluded` where `recommendation == "exclude"`
- [x] Call `00-setup-labels.yml` as `workflow_call` for each plugin's `plugin` + `lang_tags` + `platform_tags`
- [x] Add `concurrency: group: setup-${{ github.ref }}` to prevent overlapping runs on rapid pushes

### Stage 1 · `01-discovery.yml` (rename + sequential-per-plugin + auto-draft)

- [x] Rename `01-discover-skills.yml` → `01-discovery.yml`
- [x] Add `workflow_run` trigger on `00-setup-plugins.yml` success
- [x] `setup` job: parse `sources/plugins.json`, output plugin list as JSON array for sequential iteration
- [x] Run discovery **sequentially per plugin** — loop over plugins; inner `(source_id, resource_type)` matrix runs per plugin
- [x] Auto-label every new issue `status/draft` at creation time — no human labeling step needed
- [x] Add GitHub Projects v2 `addProjectV2ItemById` GraphQL mutation to assign each new issue to `veiled-market-{plugin}`
- [x] Replace `--expertise` flag with `--plugin` throughout `discover.py` CLI for consistency
- [x] `commit-registry` commit message: `chore(registry): merge discovery patches [skip ci]`
- [x] Set `permissions: contents: write, issues: write` on the discovery job; all other jobs default to `read-all`

### Stage 2 · `02-evaluate.yml`

- [x] Create `02-evaluate.yml` — triggers on `workflow_run` from Stage 1 or issue labeled `status/draft`
- [x] Run `scripts/evaluate.py --plugin {name}` to score `status/draft` issues and synthesise a draft plugin
- [x] Output: one draft PR per plugin on branch `draft/{plugin}-{timestamp}`, labeled `status/draft` + `ai/draft`
- [x] Set `permissions: contents: write, issues: write, pull-requests: write`

### Stage 3 · `03-enrich.yml`

- [x] Create `03-enrich.yml` — triggers on `workflow_run` from Stage 2 or draft PR opened
- [x] Run `scripts/enrich.py --plugin {name}` via GitHub Models (`gpt-4o` or equivalent)
- [x] Write scores (`score.relevance`, `score.quality`, `score.completeness`, `score.platform_fit`, `score.overall`) and `recommendation` to `sources/registry.json`; commit as `chore(registry): write evaluation scores [skip ci]`
- [x] Implement issue reconciliation: close issues where `recommendation == "exclude"` with label `status/excluded`
- [x] Output: one candidate PR per plugin, labeled `status/candidate` + `ai/evaluation`
- [x] Set `permissions: contents: write, issues: write, pull-requests: write`

### Stage 4 · `04-finalize-plugin.yml`

- [x] Switch trigger from PR *approval* to PR *merge* (`pull_request` event with `types: [closed]` + `if: github.event.pull_request.merged == true`)
- [x] All commits use format `chore(finalize): promote {plugin} to plugins/ [skip ci]` and `chore(marketplace): regenerate manifests [skip ci]`
- [x] Implement changelog / version bump logic — `finalize.py --step version` bumps semver in `drafts/{plugin}/plugin.json` and prepends an entry to `drafts/{plugin}/CHANGELOG.md` before promotion
- [x] ~~Verify `finalize.py --step marketplace` reads from `sources/plugins.json`~~ — already implemented
- [x] Set `permissions: contents: write, pull-requests: write`

### Cross-cutting

- [x] Plugin-proposal issue template → `05-plugin-proposal.yml` workflow opens a PR updating `sources/plugins.json` with the new plugin stub
- [x] Add schema validation job to a general CI workflow (`ci.yml` — runs on all PRs that touch `sources/` or `schemas/`)
- [x] Add `concurrency:` group to every workflow to prevent cascade overlaps
- [x] Add `permissions: {}` (deny-all) at workflow top level and grant only the minimum per-job permissions
- [x] Mask any dynamic secret values with `::add-mask::` before logging
- [x] Confirm `PIPELINE_TOKEN` secret strategy: use a **GitHub App** (`APP_ID` + `APP_PRIVATE_KEY`) — short-lived installation tokens via `actions/create-github-app-token@v1`, no long-lived PAT stored
