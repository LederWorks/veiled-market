---
name: atlas-init
description: 'Full workspace setup: detect stack, configure AI context files, write IDE settings, and populate instruction stubs for both Copilot CLI and Claude Code.'
user-invocable: false
---

# Init Workflow

Full workspace setup for the atlas plugin. Detects the project stack, gathers configuration from the user, writes AI context files, IDE config files, and instruction stubs for all enabled platforms.

If called with an `[owner/repo]` argument, use `mcp__github__*` tools for all file operations instead of the Write tool.

## Shared Prerequisites

Load `../../references/shared-steps.md` and execute these anchors in order before the skill-specific steps below:

1. **[analyse]** — full codebase detection (languages, git mode, remote URL, CI/CD, IDE markers, existing AI config, MCP). Display a summary table of all findings to the user.

## Step 1 — Ask setup questions

Ask the user four configuration questions in a single message, numbered:

1. **Which IDEs / AI tools does the team use?** (multi-select — pre-check any detected from `[analyse]`)
   - `vscode` — VS Code
   - `copilot_cli` — GitHub Copilot CLI
   - `claude_code` — Claude Code
   - `jetbrains` — JetBrains IDEs
   - `cursor` — Cursor

2. **Which platforms does this project use?** (multi-select — pre-check from git remote detection)
   - `github` — GitHub
   - `azure_devops` — Azure DevOps
   - `gitlab` — GitLab

3. **Git mode** — how should changes be applied?
   - `commit` — commit directly to the current branch
   - `pr` — open a pull request for each change
   - `local` — write files locally only (no git operations)

4. **Short project description** — one or two sentences describing the project. Used to populate the `CLAUDE.md` and `copilot-instructions.md` headers.

Wait for all four answers before proceeding.

## Step 2 — Write configuration

Execute **[write-config]** with the confirmed values from Step 1:

- `enabled_ides` — selected IDEs/AI tools
- `enabled_platforms` — selected platforms
- `languages` — detected languages from `[analyse]`
- `git_mode` — selected git mode
- `mcp_servers` — detected MCP servers from `[analyse]` (default `[]`)

## Step 3 — Create tracked task list

Use `TodoWrite` to register all remaining steps as tracked tasks:

- Generate AI context files (`CLAUDE.md`, `.github/copilot-instructions.md`)
- Write IDE config files (`.vscode/`, `.claude/`, `.github/hooks/`)
- Write base files (`.gitignore`, `.gitattributes`, `.config/features.yaml`, `.config/repository.yaml`, `project.code-workspace`)
- Detect and copy instruction stubs
- Update `.github/instructions/instructions.md` index
- Final validation

## Step 4 — Generate AI context files

Generate the AI context files based on `enabled_ides`. For each file, render the managed block between `<!-- ATLAS:START -->` and `<!-- ATLAS:END -->` markers. Include: project description, detected languages, CI/CD, IDE list, and stub list (populated after Step 5).

- If `claude_code` in `enabled_ides`: render `CLAUDE.md.j2` → write `CLAUDE.md` at the project root.
- If `copilot_cli` in `enabled_ides` or `github` in `enabled_platforms`: render `copilot-instructions.md.j2` → write `.github/copilot-instructions.md`.

If the file already exists, append the managed block at the end of the file (preserving developer-owned content above the markers).

## Step 5 — Write IDE and platform config files

Write config files based on `enabled_ides` and `enabled_platforms`. Preview each generated file to the user before writing.

**Always (when git_mode is `single` or `workspace`):**
- `.gitignore` — if not present, create with stack-appropriate patterns
- `.gitattributes` — if not present, create with `* text=auto` as minimum
- `.config/features.yaml` — atlas-managed feature flags
- `.config/repository.yaml` — atlas-managed repository metadata

**If `vscode` in `enabled_ides`:**
- `.vscode/extensions.json` — recommended extensions for detected stack
- `.vscode/settings.json` — workspace settings stub
- `.vscode/tasks.json` — common task definitions stub
- `.vscode/launch.json` — debugger configuration stub
- `project.code-workspace` — VS Code multi-root workspace file

**If `mcp_servers` is non-empty:**
- `.vscode/mcp.json` — if `vscode` in `enabled_ides`; write under `"servers"` key
- `.claude/mcp.json` — if `claude_code` in `enabled_ides`; write under `"mcpServers"` key

**If `copilot_cli` in `enabled_ides` AND `github` in `enabled_platforms`:**
- `.github/hooks/hooks.json` — hook scaffold with `sessionStart`, `preToolUse`, `postToolUse`, `sessionEnd` arrays

## Step 6 — Copy instruction stubs

Execute **[detect-stubs]** with action **copy**: for each matched stub not already present, write the stub to `.github/instructions/<name>.instructions.md`.

After all stubs are written, update `.github/instructions/instructions.md` to list every active `*.instructions.md` file.

Go back to Step 4 and update the stub list inside the `<!-- ATLAS:START/END -->` managed blocks in `CLAUDE.md` and `.github/copilot-instructions.md` to reflect the final stub set.

## Step 7 — Confirm completion

Print a summary table:

| Category | Files written |
|---|---|
| AI context | `CLAUDE.md`, `.github/copilot-instructions.md` |
| IDE config | `.vscode/extensions.json`, `.vscode/settings.json`, … |
| Platform config | `.github/hooks/hooks.json`, `.vscode/mcp.json`, … |
| Base files | `.gitignore`, `.gitattributes`, `.config/features.yaml`, … |
| Instruction stubs | `go.instructions.md`, `typescript.instructions.md`, … |
| Atlas config | `.config/atlas.json` |

Report any files skipped and the reason (e.g., "already exists", "IDE not enabled").

---

See **Guidelines** in `../../references/shared-steps.md`.
