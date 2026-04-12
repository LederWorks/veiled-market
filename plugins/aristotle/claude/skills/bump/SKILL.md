---
name: aristotle-bump
description: 'Bump a plugin semver version (patch/minor/major), run sync_versions.py or apply manual edits as fallback, then report changed files and the commit command.'
user-invocable: false
---

# Bump Workflow

Increment a plugin's semver version and propagate it to all component files.

## Step 1 — Parse arguments

Arguments passed: `$ARGUMENTS`

- **Plugin name** (required — first token). Error if missing.
- **Increment type** (second token): `patch` (default), `minor`, or `major`.

## Step 2 — Read current version

Read `plugins/<name>/commons/plugin.base.json` and extract the `version` field.

## Step 3 — Calculate new version

Apply semver rules:

| Increment | Rule | Example |
|-----------|------|---------|
| `patch` | z + 1 | `1.2.3` → `1.2.4` |
| `minor` | y + 1, z = 0 | `1.2.3` → `1.3.0` |
| `major` | x + 1, y = 0, z = 0 | `1.2.3` → `2.0.0` |

## Step 4 — Propagate version

**Primary path:** Run the shared sync script:

```bash
python3 scripts/sync_versions.py --plugin <name> --bump <patch|minor|major>
```

**Fallback** (if `scripts/sync_versions.py` does not exist): apply manual edits:
1. Edit `version` field in `plugins/<name>/commons/plugin.base.json`
2. Edit `version` field in `plugins/<name>/claude/plugin.json`
3. Edit `version` field in `plugins/<name>/copilot/plugin.json`
4. Regenerate marketplace manifests: `python3 scripts/finalize.py --step regen`

## Step 5 — Report

```
🔖 <plugin>: <old-version> → <new-version>
Updated files:
  - plugins/<name>/commons/plugin.base.json
  - plugins/<name>/claude/plugin.json
  - plugins/<name>/copilot/plugin.json
```

## Step 6 — Handoff

End with: "Commit: `git add -A && git commit -m 'chore: bump <plugin> to v<new-version>'`"
