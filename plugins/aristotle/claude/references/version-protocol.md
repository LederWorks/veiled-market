# Version Protocol — veiled-market

Reference for semver conventions, propagation targets, manual bump steps, and git commit
conventions used by the `aristotle-bump` skill and `scripts/sync_versions.py`.

---

## 1. Semver Conventions

| Increment | When to use | Example |
|-----------|-------------|---------|
| `patch` | Content fixes: typo corrections, description rewrites, step clarifications, reference updates | `1.2.3` → `1.2.4` |
| `minor` | Additive changes: new skill, new agent, new command action, new reference doc | `1.2.3` → `1.3.0` |
| `major` | Breaking changes: command rename, removed skill, restructured `plugin.base.json` schema, incompatible workflow changes | `1.2.3` → `2.0.0` |

> **Rule:** When in doubt, prefer `patch`. Escalate to `minor` only when a new resource is
> added. Escalate to `major` only when existing integrations would break.

---

## 2. Files to Update on Version Change

Every version bump must propagate to all three of these files:

| File | Field | Notes |
|------|-------|-------|
| `plugins/<name>/commons/plugin.base.json` | `"version"` | Source of truth |
| `plugins/<name>/claude/plugin.json` | `"version"` | Generated; must match |
| `plugins/<name>/copilot/plugin.json` | `"version"` | Generated; must match |

Both marketplace manifests are regenerated automatically by `finalize.py`:
- `veiled-market/.github/plugin/marketplace.json`
- `veiled-market/.claude-plugin/marketplace.json`

---

## 3. Automated Bump (preferred)

```bash
python3 scripts/sync_versions.py --plugin <name> --bump patch|minor|major
```

This script updates all three plugin files and regenerates both marketplace manifests in one
step. Prefer this over manual edits to avoid version drift.

---

## 4. Manual Bump (fallback)

If `scripts/sync_versions.py` is not available, apply edits manually in this order:

1. Edit `version` in `plugins/<name>/commons/plugin.base.json`
2. Edit `version` in `plugins/<name>/claude/plugin.json`
3. Edit `version` in `plugins/<name>/copilot/plugin.json`
4. Regenerate manifests:
   ```bash
   python3 scripts/finalize.py --step regen
   ```
5. Verify both marketplace manifests reflect the new version.

> **Warning:** Never edit only one file. All three must stay in sync.
> If they diverge, `validate_commons.py` will flag a version mismatch.

---

## 5. Git Commit Convention

All version bump commits must follow this message format:

```
chore: bump <plugin> to v<new-version>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

Examples:
- `chore: bump aristotle to v1.0.1`
- `chore: bump atlas to v1.1.0`
- `chore: bump daedalus to v2.0.0`

> The `Co-authored-by` trailer is required for all Copilot-assisted commits per workspace
> convention (see `CLAUDE.md`).

---

## 6. Version Validation

After any bump, verify with:

```bash
python3 scripts/validate_commons.py --plugin <name>
```

This checks that `commons/plugin.base.json`, `claude/plugin.json`, and `copilot/plugin.json`
all report the same version string.
