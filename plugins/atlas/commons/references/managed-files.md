---
description: >-
  Reference catalogue of all files managed by the atlas plugin.
  Used by init, update, and validate skills to know what to create, refresh, and check.
---

# Managed Files — atlas

This document lists every file the atlas plugin creates and maintains, along with
the conditions under which each file is rendered and the criteria used by `validate`
to assess its health.

---

## Managed Files Table

| File | Platform(s) | Render condition | Check criteria |
|---|---|---|---|
| `CLAUDE.md` | Claude Code | Always; `claude_code` in `enabled_ides` | Present; contains `<!-- ATLAS:START/END -->` block; auto-generated section not drifted |
| `.github/copilot-instructions.md` | Copilot CLI / VS Code | Always; `github` in `enabled_platforms` | Present; contains `<!-- ATLAS:START/END -->` block; auto-generated section not drifted |
| `.config/atlas.json` | Both | Always (primary config) | Present; valid JSON; `version`, `enabled_ides`, `enabled_platforms`, `languages`, `git_mode`, `updated_at` keys exist |
| `.github/hooks/hooks.json` | Copilot CLI + GitHub | `github` in `enabled_platforms` | Present; valid JSON; `version` and `hooks` keys exist with `sessionStart`, `preToolUse`, `postToolUse`, `sessionEnd` arrays |
| `.vscode/mcp.json` | VS Code | `vscode` in `enabled_ides` | Present; valid JSON; top-level `"servers"` key exists |
| `.claude/mcp.json` | Claude Code | `claude_code` in `enabled_ides` | Present; valid JSON; top-level `"mcpServers"` key exists |
| `.vscode/extensions.json` | VS Code | `vscode` in `enabled_ides` | Present; valid JSON; `"recommendations"` array exists |
| `.vscode/settings.json` | VS Code | `vscode` in `enabled_ides` | Present; valid JSON; no required keys (user-owned after init) |
| `.gitignore` | Git | `git_mode` is `single` or `workspace` | Present; contains atlas-managed section or stack-appropriate patterns |
| `.gitattributes` | Git | `git_mode` is `single` or `workspace` | Present; contains at minimum `* text=auto` |
| `.github/instructions/*.instructions.md` | Copilot CLI / VS Code | One per detected language/tool (see `[detect-stubs]`) | Each expected stub present; version comment matches marketplace source |
| `.github/instructions/instructions.md` | Copilot CLI / VS Code | `github` in `enabled_platforms` and at least one stub written | Present; lists all active `*.instructions.md` files |

---

## Auto-Generated Section Format

`CLAUDE.md` and `.github/copilot-instructions.md` are **partially managed** files.
The developer owns the content outside the managed block; atlas owns the block inside the markers.

### Marker format

```
<!-- ATLAS:START -->
... auto-generated content ...
<!-- ATLAS:END -->
```

**Rules:**
- The markers must appear on their own lines with no leading/trailing content.
- All content between the markers is owned by atlas and may be overwritten by `update`.
- All content outside the markers is owned by the developer and must never be modified.
- If no markers are present in an existing file, atlas appends the block at the end of the file (init) or reports `[NO_MARKER]` drift (validate).

### Typical managed block content

```markdown
<!-- ATLAS:START -->
<!-- atlas v1.0 | updated: YYYY-MM-DD -->

## Stack

- **Languages:** TypeScript, Python
- **CI/CD:** GitHub Actions
- **IDE:** VS Code, Claude Code

## Configured Tools

- MCP servers: (none configured)
- Instruction stubs: go.instructions.md, typescript.instructions.md

<!-- ATLAS:END -->
```

---

## Config Schema — `.config/atlas.json`

```json
{
  "version": "1.0",
  "enabled_ides": ["vscode", "claude_code"],
  "enabled_platforms": ["github"],
  "languages": ["typescript", "python"],
  "git_mode": "single",
  "mcp_servers": [],
  "updated_at": "YYYY-MM-DD"
}
```

### Field reference

| Field | Type | Values | Description |
|---|---|---|---|
| `version` | string | `"1.0"` | Config schema version; always `"1.0"` for the current atlas release |
| `enabled_ides` | string[] | `vscode`, `claude_code`, `jetbrains`, `cursor` | IDEs for which atlas writes IDE-specific files |
| `enabled_platforms` | string[] | `github`, `azure-devops`, `other` | Git/CI platforms determining which platform files to write |
| `languages` | string[] | `typescript`, `python`, `go`, `rust`, `java`, etc. | Detected or confirmed primary languages; drives stub selection |
| `git_mode` | string | `single`, `workspace`, `none` | Repository structure: single `.git/` root, multi-repo workspace, or no git |
| `mcp_servers` | object[] | — | MCP server entries to seed into `.vscode/mcp.json` and `.claude/mcp.json` |
| `updated_at` | string | `YYYY-MM-DD` | ISO date of last atlas write; set by `[write-config]` |

### `mcp_servers` entry shape

```json
{
  "name": "my-server",
  "command": "npx",
  "args": ["-y", "my-mcp-server"]
}
```

Each entry is written into both `.vscode/mcp.json` (`"servers"` key) and `.claude/mcp.json` (`"mcpServers"` key) using the appropriate platform schema.

---

## Validate Severity Reference

Used by `[validate-managed]` when checking managed files:

| Code | Severity | Meaning |
|---|---|---|
| `[MISSING]` | 🔴 | Required file absent; re-run `/atlas init` or `/atlas update` |
| `[OPTIONAL_MISSING]` | 🟡 | Optional file absent but expected given current config |
| `[NO_MARKER]` | 🟡 | File exists but lacks `<!-- ATLAS:START/END -->` markers; run `/atlas update` |
| `[DRIFT]` | 🟡 | Auto-generated section differs from what atlas would write today |
| `[CONFIG_MISMATCH]` | 🟡 | File exists but corresponding IDE/platform not in `.config/atlas.json` |
| `[MISSING_STUB]` | 🟡 | Expected instruction stub absent for detected language/tool |
| `[STALE_STUB]` | 🟢 | Stub present but marketplace has a newer version |
| `[HEALTHY]` | 🟢 | File present, versioned, and consistent |

The validate skill writes its full report to `.todos/atlas/validate-YYYYMMDD.md`.
