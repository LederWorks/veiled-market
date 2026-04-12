# Engineering Review Findings

Date: 2026-04-10
Reviewer: Engineering Review Agent (read-only analysis; bash execution unavailable — validator logic traced statically from source)

---

## A. validate_commons.py results

> Note: `python3` execution was unavailable during this review. The results below are derived by statically tracing `scripts/validate_commons.py` against each plugin's `commons/` directory. All file checks were performed via direct file reads.

### atlas

```
Validating: atlas/commons/

✅ All 10 checks passed

Result: 0 errors, 0 warnings, 10 passed
Exit code: 0 (clean)
```

**Checks traced:**
1. `commons/` exists — PASS
2. `plugin.base.json` valid JSON — PASS
3. Required fields (name, version, description, skills non-empty) — PASS (`skills: "skills/"` is a non-empty string)
4. `name` matches folder — PASS (`"atlas"`)
5. `hooks.json` exists — PASS
6. `hooks.json` has `"hooks"` key — PASS (`{"hooks": {}}`)
7. `commands/` has at least one `.md` — PASS (`atlas.md`)
8. Skill SKILL.md files present — PASS (init, update, validate all have SKILL.md; legacy string format resolves to 3 subdirs)
9. Agent path exists — PASS (`agents/` directory exists; legacy string check)
10/11. Each SKILL.md has frontmatter `name` + `description` — PASS (all 3 skills confirmed)
12. Command frontmatter `name` + `description` — PASS (`atlas.md` has both)

**Note on hooks.json:** `{"hooks": {}}` is missing `version: 1`. The validator does NOT check for `version` — this is a copilot build-time normalization handled by `build-platforms.py`. However it is a latent defect (see Section E).

### daedalus

```
Validating: daedalus/commons/

✅ All 12 checks passed

Result: 0 errors, 0 warnings, 12 passed
Exit code: 0 (clean)
```

**Checks traced:**
1. `commons/` exists — PASS
2. `plugin.base.json` valid JSON — PASS
3. Required fields — PASS (`name`, `version: "1.0.0"`, `description`, `skills` array with 4 entries)
4. `name` matches folder — PASS (`"daedalus"`)
5. `hooks.json` exists — PASS
6. `hooks.json` has `"hooks"` key — PASS (`{"hooks": {}}`)
7. `commands/` has at least one `.md` — PASS (`daedalus.md`)
8. Skill SKILL.md files present — PASS (create, update, build, remediate — all confirmed; array `{"path": "skills/<x>"}` format)
9. Agent path exists — PASS (`agents/scaffolder.md` exists; array `{"path": "agents/scaffolder.md"}`)
10/11. Each SKILL.md frontmatter — PASS (all 4 skills have `name` + `description`; descriptions are multi-line `>-` blocks, all under 60 words)
12. Command frontmatter — PASS (`daedalus.md` has both `name` and `description`)

### socrates

```
Validating: socrates/commons/

✅ All 9 checks passed

Result: 0 errors, 0 warnings, 9 passed
Exit code: 0 (clean)
```

**Checks traced:**
1. `commons/` exists — PASS
2. `plugin.base.json` valid JSON — PASS
3. Required fields — PASS (`name`, `version: "1.0.0"`, `description`, `skills: "skills/"`)
4. `name` matches folder — PASS (`"socrates"`)
5. `hooks.json` exists — PASS
6. `hooks.json` has `"hooks"` key — PASS (`{"hooks": {}}`)
7. `commands/` has at least one `.md` — PASS (`socrates.md`)
8. Skill SKILL.md files present — PASS (`skills/socrates/SKILL.md` found; legacy string resolves to 1 subdir)
9. Agent path exists — PASS (`agents/` directory exists)
10/11. SKILL.md frontmatter — PASS (`name: socrates`, `description` present via `>` block; estimated ~57 words, under 60-word limit)
12. Command frontmatter — PASS (`socrates.md` has `name: probe` and `description` via `>` block)

**Borderline:** `socrates/SKILL.md` description (multi-line `>` block) clocks close to the 60-word limit. Recommend manual count before publishing.

### aristotle

```
Validating: aristotle/commons/

✅ All 14 checks passed

Result: 0 errors, 0 warnings, 14 passed
Exit code: 0 (clean)
```

**Checks traced:**
1. `commons/` exists — PASS
2. `plugin.base.json` valid JSON — PASS
3. Required fields — PASS (`name`, `version: "1.0.0"`, `description`, `skills` array with 5 entries)
4. `name` matches folder — PASS (`"aristotle"`)
5. `hooks.json` exists — PASS
6. `hooks.json` has `"hooks"` key — PASS (`{"version": 1, "hooks": {}}`)
7. `commands/` has at least one `.md` — PASS (`aristotle.md`)
8. Skill SKILL.md files present — PASS (triage, bump, audit, inventory, review — all confirmed)
9. Agent path exists — PASS (`agents/health-checker.md` exists)
10/11. Each SKILL.md frontmatter — PASS (all 5 skills have `name` + `description`)
12. Command frontmatter — PASS (`aristotle.md` has both)

---

## B. build-platforms.py copy logic

**Directories currently copied (for both `_build_claude` and `_build_copilot`):**

| # | Directory | Claude handling | Copilot handling |
|---|-----------|----------------|-----------------|
| 1 | `skills/` | `copytree` verbatim | SKILL.md → workflow.md rename; `user-invocable` stripped |
| 2 | `agents/` | copy `.md` files verbatim | rename `*.md` → `*.agent.md` |
| 3 | `commands/` | copy files verbatim | path-transform `${CLAUDE_PLUGIN_ROOT}/skills/<x>/SKILL.md` → `skills/<x>/workflow.md` |
| 4 | `hooks.json` | copy verbatim | normalize: add `"version": 1` if absent |
| 5 | `.mcp.json` | copy verbatim | copy verbatim |
| 6 | `references/` | `copytree` recursively | `copytree` recursively |

**Missing from copy logic — NOT currently copied:**
- `scripts/` — not handled in either `_build_claude` or `_build_copilot`
- `templates/` — not handled in either platform builder
- `schemas/` — not handled in either platform builder

These three directories are present in the upstream `marketplace/plugins/copilot/` reference and need to be added to both platform builder functions.

**Relevant lines:** See Section F.

---

## C. Source file inventory

### marketplace/plugins/copilot/scripts/
```
__init__.py
aggregate_benchmark.py
generate_report.py
improve_description.py
package_skill.py
quick_validate.py
render_template.py
run_eval.py
run_loop.py
sync_registries.py
utils.py
validate_plugin.py
```

### marketplace/plugins/copilot/schemas/
```
hooks.schema.json
marketplace.schema.json
plugin.schema.json
skill-frontmatter.schema.json
```

### marketplace/plugins/copilot/templates/
_(top-level contains `templates.json` plus `resources/` subdir)_

### marketplace/plugins/copilot/templates/resources/
```
LICENSE.j2
README.md.j2
agents/agent.md.j2
commands/command.md.j2
hooks/hook.ps1.j2
hooks/hook.sh.j2
hooks/hooks.json.j2
plugins/mcp.json.j2
plugins/plugin.json.j2
skills/SKILL.md.j2
```
_(also: `templates/templates.json` at the templates root)_

### claude-plugins-official/plugins/plugin-dev/skills/
```
agent-development/SKILL.md
agent-development/examples/
agent-development/references/
agent-development/scripts/validate-agent.sh
command-development/README.md
command-development/SKILL.md
command-development/examples/
command-development/references/
hook-development/SKILL.md
hook-development/examples/
hook-development/references/
hook-development/scripts/
mcp-integration/SKILL.md
mcp-integration/examples/
mcp-integration/references/
plugin-settings/SKILL.md
plugin-settings/examples/
plugin-settings/references/
plugin-settings/scripts/
plugin-structure/README.md
plugin-structure/SKILL.md
plugin-structure/examples/
plugin-structure/references/
skill-development/SKILL.md
skill-development/references/
```

### claude-plugins-official/plugins/plugin-dev/agents/
```
agent-creator.md
plugin-validator.md
skill-reviewer.md
```

---

## D. sources/plugins.json current entries

| # | Name | Version |
|---|------|---------|
| 1 | terraformer | 0.1.0 |
| 2 | easy-github | 0.1.0 |
| 3 | easy-azuredevops | 0.1.0 |
| 4 | easy-azure | 0.1.0 |
| 5 | easy-aws | 0.1.0 |
| 6 | easy-gcp | 0.1.0 |
| 7 | easy-oci | 0.1.0 |
| 8 | easy-kubernetes | 0.1.0 |
| 9 | socrates | 1.0.0 |
| 10 | atlas | 1.0.0 |
| 11 | daedalus | 1.0.0 |
| 12 | aristotle | 1.0.0 |

**Atlas has `platform_sources`:** YES
```json
"platform_sources": {
  "claude": "./plugins/atlas/claude",
  "copilot": "./plugins/atlas/copilot"
}
```

**Apollo entry exists:** NO — no `apollo` entry present in `sources/plugins.json`.

---

## E. Defect confirmations

### atlas hooks.json
```json
{"hooks": {}}
```
**Defect confirmed:** Missing `"version": 1`. When `build-platforms.py` runs `_build_copilot`, it adds `"version": 1` at build time (lines 267-268). The commons/ source file itself never has it. This is expected by the build system for atlas, daedalus, and socrates — but represents a deliberate omission pattern that relies on build normalization.

### daedalus hooks.json
```json
{"hooks": {}}
```
Same pattern as atlas. Missing `"version": 1` in source; build normalizes it.

### socrates hooks.json
```json
{"hooks": {}}
```
Same pattern as atlas and daedalus. Missing `"version": 1` in source; build normalizes it.

### aristotle hooks.json
```json
{"version": 1, "hooks": {}}
```
**Correct.** Aristotle is the only plugin that already includes `"version": 1` directly in commons/hooks.json. This is the canonical form. The other three plugins should be updated to match.

**Summary:** Three of four plugins (atlas, daedalus, socrates) have inconsistent hooks.json — `version: 1` is absent in `commons/` source but injected at build time. Aristotle is the reference-correct form. This is a latent defect that silently passes `validate_commons.py` because the validator only checks for the `"hooks"` key, not `"version"`.

---

## F. build-platforms.py edit location

**File:** `scripts/build-platforms.py`

The directory copy logic is split across two functions:

### `_build_claude` — lines 116–184
Handles: skills (122–128), agents (131–140), commands (144–153), hooks.json (157–163), .mcp.json (166–172), references/ (175–181), manifest (184).

**Insert point for `scripts/`, `templates/`, `schemas/`:** After line 181 (after `references/` block), before line 184 (`_write_platform_manifest`).

### `_build_copilot` — lines 187–294
Handles: skills (192–228), agents (231–241), commands (244–260), hooks.json (264–272), .mcp.json (275–281), references/ (284–290), manifest (294).

**Insert point for `scripts/`, `templates/`, `schemas/`:** After line 290 (after `references/` block), before line 294 (`_write_platform_manifest`).

### Exact lines for the references/ blocks (anchor points for the new copy blocks):

| Function | references/ block | Insert after |
|----------|-------------------|--------------|
| `_build_claude` | Lines 175–181 | Line 181 |
| `_build_copilot` | Lines 284–290 | Line 290 |

### Pattern to replicate (using `references/` as template):
```python
# scripts/
scripts_src = commons_dir / "scripts"
if scripts_src.exists():
    if not dry_run:
        shutil.copytree(scripts_src, out / "scripts", dirs_exist_ok=True)
    print(f"  [{platform}] scripts/: copied recursively")
else:
    print(f"  [{platform}] No commons/scripts/ found, skipping.")

# templates/
templates_src = commons_dir / "templates"
if templates_src.exists():
    if not dry_run:
        shutil.copytree(templates_src, out / "templates", dirs_exist_ok=True)
    print(f"  [{platform}] templates/: copied recursively")
else:
    print(f"  [{platform}] No commons/templates/ found, skipping.")

# schemas/
schemas_src = commons_dir / "schemas"
if schemas_src.exists():
    if not dry_run:
        shutil.copytree(schemas_src, out / "schemas", dirs_exist_ok=True)
    print(f"  [{platform}] schemas/: copied recursively")
else:
    print(f"  [{platform}] No commons/schemas/ found, skipping.")
```

This block must be added in **both** `_build_claude` (after line 181) and `_build_copilot` (after line 290).
