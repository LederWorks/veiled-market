---
name: atlas-update
description: 'Refresh auto-generated sections in AI context files and sync instruction stubs with the current codebase state.'
---

# Update Workflow

Refresh the auto-generated sections of existing AI context files and sync instruction stubs with the current codebase state. Preserves all developer-owned content outside `<!-- ATLAS:START/END -->` markers.

## Shared References

Load `../../references/shared-steps.md` and `../../references/managed-files.md` before proceeding.

## Step 1 — [find-config]

Execute the `[find-config]` anchor from `../../references/shared-steps.md`.

If `.config/atlas.json` is not found and no legacy config exists, suggest running `/atlas init` first and stop.

## Step 2 — [analyse]

Execute the `[analyse]` anchor from `../../references/shared-steps.md` to re-detect the current tech stack.

Languages, tools, and IDE configuration may have changed since `init` ran — always re-scan rather than relying solely on the stored config.

## Step 3 — Regenerate auto-generated sections

For each AI context file applicable to the current config (`CLAUDE.md`, `.github/copilot-instructions.md`):

1. Read the file from disk (or via `mcp__github__*` tools in remote mode)
2. Locate the `<!-- ATLAS:START -->` and `<!-- ATLAS:END -->` markers
3. Generate the updated block in memory using the freshly analysed stack data:
   - Languages, CI/CD tools, IDE configuration, MCP servers, active instruction stubs
   - Set the version comment to today's date: `<!-- atlas v1.0 | updated: YYYY-MM-DD -->`
4. Compare the generated block to the existing block byte-for-byte:
   - **Changed**: write the file back, replacing only the content between the markers
   - **Identical**: skip the write and note "no changes" for this file
5. If markers are absent: append the managed block at the end of the file (after a `---` rule) and report `[NO_MARKER]`

**Never modify content outside the `<!-- ATLAS:START/END -->` markers.**

## Step 4 — [detect-stubs]

Execute the `[detect-stubs]` anchor from `../../references/shared-steps.md` with action **update**:

- **New stubs**: language/tool now detected but stub not present → mark for addition
- **Stale stubs**: stub present but marketplace version is newer → mark for update
- **Obsolete stubs**: stub present but language/tool no longer detected → mark for removal (requires confirmation)

## Step 5 — Sync stubs

Apply changes identified in Step 4:

1. **Add** new stubs — write each to `.github/instructions/<name>.instructions.md`
2. **Update** stale stubs — overwrite with the current marketplace version
3. **Remove** obsolete stubs — ask the user to confirm before deleting each one; skip if declined
4. **Regenerate** `.github/instructions/instructions.md` — update the index to reflect the current stub list

## Step 6 — Update `.config/atlas.json`

Merge current values back into `.config/atlas.json`:

- Update `updated_at` to today's date (`YYYY-MM-DD`)
- Update `languages` to the list detected in Step 2
- Preserve all other keys (including user-extended fields)

Use `[write-config]` from `../../references/shared-steps.md` for the merge-and-write logic.

## Step 7 — Report

Print a diff summary:

```
atlas update — summary
──────────────────────────────────────
AI context files:
  CLAUDE.md                  ✅ regenerated
  .github/copilot-instructions.md  ─ no changes

Instruction stubs:
  rust.instructions.md       ✅ added
  typescript.instructions.md ✅ updated
  java.instructions.md       ─ skipped (removal declined)

Config:
  .config/atlas.json         ✅ updated_at refreshed
──────────────────────────────────────
```

---

**Remote mode**: If an `owner/repo` argument was passed, use `mcp__github__*` tools for all file reads and writes instead of local file operations.

See **Guidelines** in `../../references/shared-steps.md`.
