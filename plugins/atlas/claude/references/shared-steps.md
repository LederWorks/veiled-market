---
description: >-
  Shared workflow foundations for all atlas skills (init, update, validate).
  Skills load this file by name and execute named anchors as directed.
  Do NOT invoke this file directly — use /atlas [init|update|validate].
---

# Shared Steps — atlas

Common prerequisites executed by every atlas skill before skill-specific steps begin.

## Managed Files

All three skills (init, update, validate) operate on the same file set:

| File | Used by | Location | Notes |
|---|---|---|---|
| `CLAUDE.md` | Claude Code | Project root | AI-generated project context |
| `.github/copilot-instructions.md` | Copilot CLI / VS Code | `.github/` directory | AI-generated project context |
| `.config/atlas.json` | Both platforms | `.config/` directory | Atlas config: enabled IDEs, platforms, languages, git mode |
| `.github/hooks/hooks.json` | Copilot CLI + GitHub | `.github/hooks/` directory | Hook scaffold — created when GitHub platform enabled |
| `.vscode/mcp.json` | VS Code | `.vscode/` directory | MCP server stubs (`"servers"` key) |
| `.claude/mcp.json` | Claude Code | `.claude/` directory | MCP server stubs (`"mcpServers"` key) |
| `.vscode/extensions.json` | VS Code | `.vscode/` directory | Recommended extensions — created when VS Code IDE enabled |
| `.vscode/settings.json` | VS Code | `.vscode/` directory | Workspace settings — created when VS Code IDE enabled |
| `.gitignore` | Git | Project root | Stack-aware ignore patterns |
| `.gitattributes` | Git | Project root | Line endings, binary markers |
| `.github/instructions/*.instructions.md` | Copilot CLI / VS Code | `.github/instructions/` directory | Language/tool-specific instruction stubs |
| `.github/instructions/instructions.md` | Copilot CLI / VS Code | `.github/instructions/` directory | Instructions index |

---

## [find-config] Find Existing Configuration

Locate the atlas configuration and return a parsed config object.

1. **Check for `.config/atlas.json`** (primary):
   - If present: parse and return as config object
   - Extract: `enabled_ides`, `enabled_platforms`, `languages`, `git_mode`, `mcp_servers`, `version`
   - Note the source: `"read from .config/atlas.json"`

2. **Fallback to `.config/platform.yaml`** (backward-compat, if `atlas.json` absent):
   - This is the legacy `project` plugin config
   - Read `platforms[].platform_id` where `enabled=true` → map to `enabled_platforms`
   - Read `repo_mode` → `git_mode`
   - Note the source: `"read from .config/platform.yaml (project plugin legacy)"`
   - Prompt the user to migrate to `.config/atlas.json` after init completes

3. **Fallback to `.ai-platforms`** (backward-compat, if both absent):
   - Read one entry per line → infer `enabled_platforms`
   - Set `git_mode="single"` if `git` is in the list, `"none"` otherwise
   - Note the source: `"read from .ai-platforms (legacy)"`

4. **No configuration found**:
   - Return an empty config object with defaults
   - Suggest running `/atlas init`

5. Report findings:
   - Configuration source used
   - List of `enabled_platforms` and `enabled_ides`
   - `git_mode` if known
   - Which managed files are present or missing on disk

---

## [analyse] Analyse the Codebase

Run these checks concurrently to detect the tech stack and environment:

```
Languages / runtimes
  Go:           go.mod present?
  Python:       pyproject.toml / requirements.txt / setup.py present?
  TypeScript:   package.json with typescript dependency?
  Node:         package.json without typescript?
  Rust:         Cargo.toml present?
  Java/Kotlin:  pom.xml / build.gradle present?

Infrastructure
  Terraform:    *.tf files present?
  Bicep:        *.bicep files present?
  ARM:          *.json files containing "$schema": "https://schema.management.azure.com"?
  Kubernetes:   *.yaml files containing "kind:" Kubernetes resource types?
  Helm:         Chart.yaml present?

CI/CD
  GitHub Actions:   .github/workflows/*.yml present?
  ADO pipelines:    azure-pipelines.yml / .ado/** / .azure-pipelines/** present?
  Jenkins:          Jenkinsfile present?
  Other:            .circleci/ / .travis.yml / Makefile with CI targets?

Version control
  Git single:       .git/ directory at project root → git_mode="single"
  Git workspace:    no .git/ at root, but .git/ in immediate subdirs
                      → git_mode="workspace"; record sub-repo relative paths
  No git:           neither root .git/ nor sub-dir .git/ → git_mode="none"
  Remote URL:       git remote get-url origin → classify as GitHub / ADO / other

IDE configuration
  VS Code:          .vscode/ directory present?
  JetBrains:        .idea/ directory present?
  Cursor:           .cursor/ directory or .cursorrules present?

MCP configuration
  VS Code MCP:      .vscode/mcp.json present with "servers" key?
  Claude MCP:       .claude/mcp.json present with "mcpServers" key?
```

Store all detected values in a context object for use by subsequent steps. If `git_mode` was already resolved by `[find-config]`, skip the Git detection block.

---

## [detect-stubs] Detect Applicable Instruction Stubs

Compare existing `.github/instructions/*.instructions.md` files against available stubs in `references/stubs/`. Return two lists: stubs to **add** (matched but absent) and stubs to **update** (present but stale).

The action taken differs per skill:

- **init**: copy matching stubs to `.github/instructions/` if not present
- **update**: refresh stubs if the marketplace version is newer; add new matches not yet present
- **validate**: report `[MISSING_STUB]` or `[STALE_STUB]` for each discrepancy

Detection mapping:

| Detected condition | Stub file | Target path |
|---|---|---|
| Go (`go.mod`) | `stubs/go.instructions.md` | `.github/instructions/go.instructions.md` |
| TypeScript (`tsconfig.json` or `package.json` + typescript) | `stubs/typescript.instructions.md` | `.github/instructions/typescript.instructions.md` |
| Python (`pyproject.toml` / `requirements.txt`) | `stubs/python.instructions.md` | `.github/instructions/python.instructions.md` |
| Terraform (`*.tf` files) | `stubs/terraform.instructions.md` | `.github/instructions/terraform.instructions.md` |
| GitHub Actions (`.github/workflows/*.yml`) | `stubs/github-actions.instructions.md` | `.github/instructions/github-actions.instructions.md` |
| ADO pipelines (`azure-pipelines.yml` / `.azure-pipelines/`) | `stubs/azure-devops.instructions.md` | `.github/instructions/azure-devops.instructions.md` |
| VS Code IDE (`.vscode/` present or `enabled_ides` includes `vscode`) | `stubs/vscode.instructions.md` | `.github/instructions/vscode.instructions.md` |
| Bash scripts (`*.sh`) | `stubs/bash.instructions.md` | `.github/instructions/bash.instructions.md` |
| PowerShell scripts (`*.ps1`) | `stubs/powershell.instructions.md` | `.github/instructions/powershell.instructions.md` |
| Git detected (`git_mode` is `single` or `workspace`) | `stubs/git.instructions.md` | `.github/instructions/git.instructions.md` |
| Markdown-heavy repo (`docs/` dir or many `*.md` files) | `stubs/markdown.instructions.md` | `.github/instructions/markdown.instructions.md` |

For each matched stub, compare the version comment in the existing file (if any) against the stub source. A stub is **stale** if the version differs or the stub has been modified in the marketplace since the file was last written.

---

## [write-config] Write Configuration

Write or update `.config/atlas.json` with current settings.

1. Collect all values:
   - `enabled_ides` — list of IDE identifiers (e.g., `["vscode", "claude_code"]`)
   - `enabled_platforms` — list of platform identifiers (e.g., `["github"]`)
   - `languages` — list of detected/confirmed language identifiers
   - `git_mode` — `"single"` | `"workspace"` | `"none"`
   - `mcp_servers` — list of MCP server entries (default `[]`)
   - `version` — always `"1.0"`
   - `updated_at` — current date as `YYYY-MM-DD`

2. If `.config/atlas.json` already exists, merge: preserve any keys not listed above (user extensions), overwrite the listed keys with current values.

3. Create `.config/` directory if it does not exist.

4. Write `.config/atlas.json` and report the path written.

---

## [validate-managed] Validate Managed Files

Check all managed files and return a list of issues with severity indicators.

For each managed file applicable to the current config:

1. **Presence check** — does the file exist on disk?
   - Missing required file → 🔴 `[MISSING]`
   - Missing optional file (e.g., stubs for undetected languages) → 🟡 `[OPTIONAL_MISSING]`

2. **Version marker check** — does the file contain an `<!-- ATLAS:` version comment?
   - No version marker found → 🟡 `[NO_MARKER]`

3. **Content drift check** — for files with `<!-- ATLAS:START -->…<!-- ATLAS:END -->` blocks:
   - Re-generate the auto-managed section in memory
   - Compare with the on-disk version
   - Significant difference → 🟡 `[DRIFT]` (include a brief diff summary)

4. **Config consistency** — does the set of present managed files match `enabled_ides` and `enabled_platforms` in `.config/atlas.json`?
   - Mismatch (e.g., `.vscode/mcp.json` exists but `vscode` not in `enabled_ides`) → 🟡 `[CONFIG_MISMATCH]`

Severity legend:
- 🔴 — blocking; required file is absent or corrupt
- 🟡 — advisory; file exists but may be stale or inconsistent
- 🟢 — healthy; file is present, versioned, and consistent

Return the full list of issues. If no issues are found, report `🟢 All managed files are healthy`.

---

## Guidelines

Apply these rules in every skill:

- **Show before write** — always preview generated content before touching any files
- **Never invent** — only include content verifiable from the codebase or confirmed by the user
- **Preserve manual edits** — content above and below `<!-- ATLAS:START/END -->` markers is developer-owned; never overwrite it
- **Atomic updates** — when updating both `CLAUDE.md` and `copilot-instructions.md`, update them in the same operation so they stay in sync
- **Config first** — always run `[find-config]` before any file read/write; never assume defaults
