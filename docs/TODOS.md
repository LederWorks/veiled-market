# TODOs

## MARKETPLACE.md

- **Tabbed code blocks for platform/shell variants** — Replace the current side-by-side comparison
  tables (Claude Code vs Copilot CLI, inside shell vs outside shell) with tabbed code blocks as
  used on major documentation sites (e.g. MkDocs Material `=== "Tab"`, Docusaurus `<Tabs>`,
  VitePress `::: code-group`). Requires choosing and setting up a documentation renderer first —
  plain GitHub Markdown does not support this natively. Good candidates: §9.1 install commands,
  §9.2 register/install table, §6 plugin architecture comparisons.

## veiled-market Plugin Architecture

- **Implement `scripts/build-platforms.py`** — Takes `plugins/*/commons/` as input and generates
  `plugins/*/claude/` and `plugins/*/copilot/` output trees. Transformations required:
  - Hidden skills (`user-invocable: false`): copy as `workflow.md` for Copilot output
  - Agents: add `.agent` before `.md` extension for Copilot output
  - Commands: substitute `${PLUGIN_ROOT}` → `${CLAUDE_PLUGIN_ROOT}` for Claude; resolve
    absolute path for Copilot (TBD — see open question in FINDINGS.md)
  - Manifests: merge `plugin.base.json` with platform-specific fields into each `plugin.json`
  - Update both `marketplace.json` files to point `source` at generated subdirs
  Integrate into `scripts/finalize.py` finalization step. Also runnable standalone.

- **Define `plugin.base.json` JSON schema** — Add `schemas/plugin.base.schema.json`.
  Covers shared metadata + per-skill `user-invocable` marker. Required before any new
  plugin is authored using the commons layout.

- **Migrate `terraformer` plugin** to commons layout — Current single-dir layout has no
  `commons/`. Run build script against it to generate `claude/` and `copilot/` subdirs,
  then update both marketplace.json files accordingly.

