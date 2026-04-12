# Three-Way Plugin Architecture Comparison

> **Subjects:**
> - `claude-plugins-official/plugins/plugin-dev` — Anthropic's official Claude Code plugin toolkit
> - `marketplace/plugins/copilot` v1.5.1 — Internal Copilot CLI plugin management monolith
> - `veiled-market/plugins/` — Daedalus / Socrates / Aristotle philosopher trio
>
> **Ruleset applied:** `veiled-market/docs/MARKETPLACE.md` (our authoritative multi-platform ruleset).
> **Last reviewed:** April 2026

---

## 1. Contestants at a Glance

### plugin-dev (Anthropic)

| Resource | Count | Details |
|----------|-------|---------|
| Command | 1 | `create-plugin.md` — 449 lines, 8-phase guided workflow |
| Skills | 7 | `agent-development` (415), `command-development` (884), `hook-development` (712), `mcp-integration` (554), `plugin-settings` (544), `plugin-structure` (476), `skill-development` (637) |
| Agents | 3 | `plugin-validator`, `skill-reviewer`, `agent-creator` |
| Scripts | 5 | Bash: `validate-agent.sh`, `test-hook.sh`, `validate-hook-schema.sh`, `hook-linter.sh`, `parse-frontmatter.sh` |
| References | 21 | Across all skill `references/` dirs |
| Examples | 16 | Across all skill `examples/` dirs |
| Platform | **Claude Code only** | |

Scope: plugin creation (guided), skill/agent/hook/MCP/settings authoring, structure validation, skill quality review.

### copilot monolith (Internal, v1.5.1)

| Resource | Count | Details |
|----------|-------|---------|
| Skills | 10 | All 53–242 lines: `plugin-management` (136), `skill-management` (242), `command-management` (101), `agent-management` (66), `hook-management` (79), `mcp-management` (86), `reference-management` (68), `script-management` (88), `template-management` (120), `update-resource` (53) |
| Commands | 5 | `/create` (64), `/validate` (53), `/bump` (53), `/update` (45), `/analyze` (61) — all ≤64 lines |
| Agents | 7 | `scaffolder`, `validator`, `compliance-analyzer`, `grader`, `comparator`, `analyzer`, `registry-syncer` |
| Scripts | 11 | Python: `validate_plugin.py`, `sync_registries.py`, `run_eval.py`, `aggregate_benchmark.py`, `improve_description.py`, `render_template.py`, `generate_report.py`, `package_skill.py`, `quick_validate.py`, `run_loop.py`, `utils.py` |
| References | 9 | `shared-steps.md`, `template-variables.md`, `skill-schemas.md`, `eval-benchmark.md`, `hooks-configuration.md`, `plugin-schema.md`, `registry-management.md`, `todo-schema.md`, `ci-steps.md` |
| Templates | 10 | Jinja2 for all 9 resource types |
| JSON Schemas | 3 | `plugin.schema.json`, `skill-frontmatter.schema.json`, `hooks.schema.json` |
| Hooks | Empty | `hooks/hooks.json` declared, nothing wired |
| Platform | **Copilot CLI only** | |

Scope: full plugin lifecycle (create, validate, bump, analyze, update), eval loop, template scaffolding, registry sync.

### Daedalus / Socrates / Aristotle (veiled-market)

| Resource | Count | Details |
|----------|-------|---------|
| Plugins | 3 | Separate: Daedalus (forge), Socrates (probe), Aristotle (steward) |
| Skills | 10 | All 47–168 lines across 3 plugins |
| Commands | 4 | All 25–44 lines: `daedalus.md`, `socrates.md`, `aristotle.md`, `atlas.md` |
| Agents | 3 | `scaffolder.md` (Daedalus), `scanner.md` (Socrates), `health-checker.md` (Aristotle) |
| Scripts | 3 | Python: `validate_commons.py`, `build-platforms.py`, `sync_versions.py` |
| References | 5 | `resource-types.md`, `rules-compact.md`, `version-protocol.md`, `shared-steps.md` |
| Templates | 0 | Not yet implemented |
| JSON Schemas | 0 | Not yet implemented |
| Hooks | Empty | `hooks.json` declared in each plugin |
| Platform | **Both** | Claude Code + Copilot CLI via commons build |

Scope: plugin creation/update/build/remediate (Daedalus), compliance scanning → TODO (Socrates), triage/bump/audit/inventory/review (Aristotle).

---

## 2. MARKETPLACE.md Scorecard: plugin-dev

### ❌ Critical Violations

**Rule 2 (command ≤ 66 lines) + Anti-pattern 2**

`create-plugin.md` = **449 lines** — 6.8× over the limit. The full 8-phase workflow is inlined into a command file. Anti-pattern 2 names this exactly: *"A command file with workflow branches, numbered steps, or inline sub-procedures."*

**Rule 4 + Rule 20 (SKILL.md ≤ 500 lines; > 4,000 tokens → split)**

| Skill | Lines | Est. tokens | Status |
|-------|-------|-------------|--------|
| `command-development` | 884 | ~10,608 | ❌ Must split |
| `hook-development` | 712 | ~8,544 | ❌ Must split |
| `skill-development` | 637 | ~7,644 | ❌ Must split |
| `mcp-integration` | 554 | ~6,648 | ❌ Must split |
| `plugin-settings` | 544 | ~6,528 | ❌ Must split |
| `plugin-structure` | 476 | ~5,712 | ❌ Must split |
| `agent-development` | 415 | ~4,980 | ❌ Must split |

Every single skill fails the 4,000-token mandatory split threshold. At the compaction budget ceiling of 5,000 tokens per skill (Rule 23), `command-development` alone at ~10,608 tokens busts the limit on its own.

Cruel irony: `skill-development` — the skill that teaches progressive disclosure — has only 1 reference file but 637 lines of body. It preaches a practice it does not follow.

**Platform gap:** Claude Code only. Copilot CLI users get nothing.

### ✅ Compliant Areas

Rule 1 (Pattern B — multiple focused entry points) ✅ · Rule 3 (one concern per skill) ✅ · Rule 8 (references/ per skill) ✅ · Rule 10 (scripts in scripts/) ✅ · Rule 11 (tables → references) ✅ · Rule 21 (descriptions specific with triggers) ✅ · Rule 22 (hooks config present) ✅

---

## 3. MARKETPLACE.md Scorecard: copilot monolith

### ✅ Compliant (the good news first)

| Rule | Result |
|------|--------|
| Rule 1 (Pattern A — thin router + skills) | ✅ Exact correct implementation: 5 thin routers, 10 domain skills |
| Rule 2 (command ≤ 66 lines) | ✅ All 5 commands 45–64 lines |
| Rule 4 (SKILL.md ≤ 500 lines) | ✅ All 10 skills 53–242 lines |
| Rule 20 (> 4,000 tokens → split) | ✅ Max ~2,904 tokens (skill-management at 242 lines) |
| Rule 7 (Workflow Agents declare ## Inputs) | ✅ `validator`, `scaffolder`, `compliance-analyzer` all declare typed inputs |
| Rule 10 (scripts in scripts/) | ✅ 11 Python scripts, zero inlined |
| Rule 11 (> 20-line lookup → Reference) | ✅ Large content in 9 reference files |
| Rule 12 (boilerplate → J2 template) | ✅ Full Jinja2 set for all 9 resource types |
| Rule 22 (hooks config present) | ✅ `hooks/hooks.json` exists (empty — nothing wired, which is correct) |

### ❌ Violations

**Platform gap:** Copilot CLI only. No `.claude-plugin/` directory, no Claude Code conventions in skills or templates.

**Minor — skill-management description breadth (Rule 21):** The `skill-management` description covers creating, editing, evaluating, and optimizing skills in one description. This is broad — it may trigger in any skill-adjacent context, not just the specific workflow it covers. Could be split into narrower trigger phrases.

**Net verdict:** The copilot monolith is MARKETPLACE.md compliant on every structural rule. The single gap is platform coverage. This is the best-designed monolith of the three contestants.

---

## 4. Three-Way Head-to-Head

### Architecture

| Dimension | plugin-dev | copilot monolith | Daedalus/Socrates/Aristotle |
|-----------|-----------|-----------------|----------------------------|
| Plugin count | 1 | 1 | 3 |
| Platform | Claude Code only ❌ | Copilot CLI only ❌ | Both platforms ✅ |
| Lifecycle coverage | Create + Validate | Create + Validate + Bump + Analyze | Create → Validate → Maintain ✅ |
| Inter-plugin handoffs | None | N/A (monolith) | `fix-type` routing ✅ |
| Commons build system | None | None | `build-platforms.py` ✅ |
| Pattern A routing | ❌ Pattern B | ✅ Pattern A | ✅ Pattern A |
| Persistent TODO schema | None | `.todos/copilot/` | `.todos/socrates/` with `fix-type` ✅ |

### Resource sizing (MARKETPLACE.md compliance)

| Metric | plugin-dev | copilot monolith | Our trio |
|--------|-----------|-----------------|----------|
| Command max size | 449 lines ❌ | 64 lines ✅ | 44 lines ✅ |
| Skill max size | 884 lines ❌ | 242 lines ✅ | 168 lines ✅ |
| Skills failing token limit | 7/7 ❌ | 0/10 ✅ | 0/10 ✅ |
| Cost per skill invocation | 4,980–10,608 tokens ❌ | 636–2,904 tokens ✅ | 564–2,016 tokens ✅ |

### Functional depth

| Capability | plugin-dev | copilot monolith | Our trio |
|-----------|-----------|-----------------|----------|
| Plugin creation (guided) | ✅ 8-phase | ✅ /create + scaffolder | ✅ Daedalus create |
| Plugin update | ✅ | ✅ /update | ✅ Daedalus update |
| Commons/dual-platform build | ❌ | ❌ | ✅ Daedalus build |
| Compliance validation | ✅ plugin-validator | ✅ /analyze → compliance-analyzer | ✅ Socrates scanner |
| Skill quality review | ✅ skill-reviewer | ⚠️ grader (eval-based) | ⚠️ Not yet separated |
| Agent creation (meta) | ✅ agent-creator | ❌ | ❌ |
| Hook authoring knowledge | ✅ + 4 scripts | ✅ hook-management skill | ❌ Not built |
| MCP integration knowledge | ✅ | ✅ mcp-management skill | ❌ Not built |
| Plugin settings pattern | ✅ | ❌ | ❌ |
| Version bumping | ❌ | ✅ /bump + sync_registries.py | ✅ Aristotle bump |
| Cross-plugin health audit | ❌ | ❌ | ✅ Aristotle audit |
| Plugin inventory dashboard | ❌ | ❌ | ✅ Aristotle inventory |
| Remediation routing | ❌ | ❌ | ✅ Aristotle triage + fix-type |
| Proactive post-create trigger | ✅ plugin-validator | ❌ | ❌ |
| **Eval loop** | ❌ | ✅ run_eval → aggregate → improve_description | ❌ |
| JSON Schema validation | ❌ | ✅ 3 schemas | ❌ |
| Jinja2 templates | ❌ | ✅ All 9 resource types | ❌ |
| Description optimizer | ❌ | ✅ improve_description.py | ❌ |
| Bash validators | ✅ 5 scripts | ❌ | ❌ |

---

## 5. Honest Verdict

**plugin-dev** is architecturally broken by our standards. Every skill fails the token budget, and the command file is Anti-pattern 2 by definition. Its saving graces are granular bash validators, proactive triggering, and deep domain knowledge (hooks, MCP, settings). These are worth extracting; the structure is not worth emulating.

**copilot monolith** is the best-designed of the three on our rules. It follows Pattern A, respects all size limits, uses references, and has the richest tooling: an eval loop, JSON schemas, Jinja2 templates, a description optimizer. Its only gap is platform: Copilot CLI only.

**Daedalus/Socrates/Aristotle** is the most architecturally sophisticated on lifecycle and inter-plugin coordination: `fix-type` routing, commons build, dual-platform output, and the full Create→Validate→Maintain cycle. But it lacks the tooling depth of the copilot monolith (no eval loop, no JSON schemas, no templates, no description optimizer).

**Overall ranking by dimension:**

| Dimension | Winner |
|-----------|--------|
| MARKETPLACE.md compliance | copilot monolith ≈ our trio (both clean); plugin-dev fails |
| Platform coverage | Our trio only |
| Tooling depth (scripts, schemas, templates, eval) | copilot monolith |
| Lifecycle completeness | Our trio |
| Domain coverage (hooks, MCP, settings) | plugin-dev (depth) ≈ copilot monolith (breadth) |
| Inter-plugin coordination | Our trio (unique) |

---

## 6. Architecture Question: Monolith + Multi-Platform?

> *"If we take the copilot monolith architecture and add commons build (multi-platform support), would that be the best approach?"*

**Short answer: Yes, for a net-new plugin. No, for the existing trio.**

### The case for a unified multi-platform plugin

The copilot monolith demonstrates that a single plugin can cover the full lifecycle (create, validate, bump, analyze) while staying inside every size limit. Adding the commons build would give it dual-platform output, closing its only gap. One install = complete toolset. No inter-plugin handoffs to wire. Shared template registry. Single version to track.

This is the right architecture for **starting from scratch today** — a single well-structured plugin using `commons/` as the source of truth, generating both Claude Code and Copilot CLI output.

### The case for keeping the trio

At our current scale (10 total skills across 3 plugins), the Level-1 token cost difference between one plugin and three is negligible — you pay the description frontmatter of every installed skill regardless. The real benefit of the split is not token cost; it is **independent versioning** and **install à la carte**. A team that validates plugins but never creates them installs only Socrates.

More importantly, the trio's specialist cycle — Daedalus → Socrates → Aristotle via `fix-type` routing — is a capability that disappears in a monolith. The cycle means Socrates findings carry structured metadata that Aristotle reads to auto-dispatch remediation to Daedalus. In a monolith, this becomes implicit state management inside one plugin, which is harder to maintain and impossible to install independently.

### Verdict

Do not merge the trio. Instead:

1. **Enrich each specialist** with the copilot monolith's strongest tools (see §7 below).
2. **For any new plugin you build today** — start with a single `commons/`-based plugin. The monolith architecture is correct at inception; the split makes sense only when the domain boundary is clear and independent install is a real use case.
3. **The copilot monolith itself** should be ported to a `commons/`-based dual-platform plugin as a future project — it already has the right structure; adding commons build is the only change needed.

---

## 7. Items to Borrow

### From plugin-dev

**7.1 Granular bash validators** (high priority)

5 executable scripts: `validate-agent.sh`, `validate-hook-schema.sh`, `test-hook.sh`, `hook-linter.sh`, `parse-frontmatter.sh`. Our `validate_commons.py` validates structure only — it says nothing about agent frontmatter correctness, hook schema validity, or description quality.

Add to `veiled-market/scripts/`:
- `validate-agents.sh` — check name, description examples, model, color, tools
- `validate-hooks.sh` — check hooks.json schema, event names, script references

**7.2 Proactive post-create trigger** (medium priority)

`plugin-validator` fires after creation without being asked. Add a `PostToolUse` hook in Daedalus that fires the Socrates scanner after the `create` skill completes.

**7.3 "Positive findings" section in Socrates reports** (medium priority)

Four-tier output (Critical / Warnings / Positive Findings / Recommendations) is more actionable than our current two-tier. Add `## ✅ Compliant` section to the TODO schema.

**7.4 Domain knowledge skills: hooks, MCP, settings** (low priority)

Future Daedalus skills, properly sized (≤200 lines, depth in `references/`):
- `skills/hook-authoring/SKILL.md`
- `skills/mcp-authoring/SKILL.md`
- `skills/settings-authoring/SKILL.md`

**7.5 Agent-creator pattern** (low priority)

Meta-agent that generates agent system prompts from a description, scoped to both platform conventions.

### From copilot monolith

**7.6 Eval loop** (high priority — unique, no equivalent exists elsewhere)

The `skill-management` skill describes a full write→run→grade→iterate cycle backed by:
- `run_eval.py` — executes test prompts against the skill
- `aggregate_benchmark.py` — variance analysis across runs
- `improve_description.py` — automated trigger-phrase optimization

No other plugin has this. It is the single most valuable capability to port. Add an `eval` skill to Daedalus backed by equivalent Python scripts.

**7.7 JSON Schema validation** (high priority)

`validate_plugin.py` runs against `plugin.schema.json`, `skill-frontmatter.schema.json`, `hooks.schema.json`. Our `validate_commons.py` uses Python assertions — no machine-readable schema. Port the three schema files to `veiled-market/schemas/` and update `validate_commons.py` to validate against them.

**7.8 Jinja2 template set** (medium priority)

The copilot monolith has J2 templates for all 9 resource types (plugin manifest, SKILL.md, agent.md, command.md, hook.sh, hook.ps1, hooks.json, mcp.json, README.md). Our Daedalus scaffolder writes files from scratch via AI. Jinja2 templates make scaffolding repeatable and testable.

Add `templates/` to Daedalus commons with templates for each resource type.

**7.9 Description optimizer** (medium priority)

`improve_description.py` applies automated trigger-phrase optimization to skill descriptions. This is directly relevant to Socrates's quality review mission — the `review` skill in Aristotle currently does this manually. Automating it (via script + Aristotle orchestration) would make description improvement a first-class, repeatable operation.

**7.10 Shared step anchors** (low priority)

The copilot monolith requires `shared/STEPS.md` for any plugin with ≥2 skills, extracting reused step blocks into named anchors. Our trio uses `references/shared-steps.md` already — but the anchor naming convention (`## [anchor-name]`) is a cleaner pattern worth adopting explicitly.

---

## Summary

| | plugin-dev | copilot monolith | Daedalus/Socrates/Aristotle |
|-|-----------|-----------------|----------------------------|
| **MARKETPLACE.md** | ❌ 7 critical violations | ✅ Clean | ✅ Clean |
| **Platform** | Claude Code only | Copilot CLI only | **Both** ✅ |
| **Architecture** | Oversized monolith | Well-structured monolith | Specialist cycle |
| **Lifecycle** | Create + Validate | Create + Validate + Bump | Create → Validate → Maintain |
| **Tooling** | Bash validators ✅ | Eval loop ✅, schemas ✅, templates ✅ | Commons build ✅ |
| **Unique win** | Proactive trigger | Eval loop + description optimizer | fix-type routing + dual-platform |
| **Biggest gap** | Cost compliance | Platform coverage | Eval loop, schemas, templates |

**Recommended path forward:** Keep the trio. Borrow the eval loop and JSON schemas from the copilot monolith (items 7.6–7.7) as the highest-leverage additions. The copilot monolith is the best model for any net-new plugin you create today — start with a single `commons/`-based plugin and split only when domain boundaries require it.


---

## 1. What plugin-dev Is

plugin-dev is the official Anthropic plugin that teaches Claude Code how to create Claude Code plugins. It ships:

| Resource | Count | Details |
|----------|-------|---------|
| Command | 1 | `create-plugin.md` — 449 lines, 8-phase guided workflow |
| Skills | 7 | `agent-development`, `command-development`, `hook-development`, `mcp-integration`, `plugin-settings`, `plugin-structure`, `skill-development` |
| Agents | 3 | `plugin-validator`, `skill-reviewer`, `agent-creator` |
| Scripts | 5 | `validate-agent.sh`, `test-hook.sh`, `validate-hook-schema.sh`, `hook-linter.sh`, `parse-frontmatter.sh` |
| References | 21 | Across all skill `references/` directories |
| Examples | 16 | Across all skill `examples/` directories |
| Platform | 1 | **Claude Code only** |

Its functional scope covers: plugin creation (guided workflow), skill/agent/hook/MCP/settings authoring, structure validation, skill quality review.

---

## 2. MARKETPLACE.md Scorecard

Rules from `docs/MARKETPLACE.md` applied to plugin-dev. Each violation is scored.

### ❌ Critical Violations

**Rule 2: Command file MUST be ≤ 66 lines** (Anti-pattern 2 explicitly named)

`create-plugin.md` = **449 lines** — 6.8× over the limit.

The entire 8-phase workflow (Discovery → Component Planning → Detailed Design → Structure → Implementation → Validation → Testing → Documentation) is inlined into a command file. Anti-pattern 2 describes this exactly: *"A command file with workflow branches, numbered steps, or inline sub-procedures. Every invocation loads all content regardless of which action the user typed."*

This is a procedural skill masquerading as a command. It should be a `SKILL.md` with `disable-model-invocation: true` (user-invocable), or split into per-phase skills referenced from a thin command router.

**Rule 4 + Rule 20: SKILL.md ≤ 500 lines; >4,000 tokens → split**

| Skill | Lines | Est. tokens | Status |
|-------|-------|-------------|--------|
| `command-development` | 884 | ~10,608 | ❌ Must split |
| `hook-development` | 712 | ~8,544 | ❌ Must split |
| `skill-development` | 637 | ~7,644 | ❌ Must split |
| `mcp-integration` | 554 | ~6,648 | ❌ Must split |
| `plugin-settings` | 544 | ~6,528 | ❌ Must split |
| `plugin-structure` | 476 | ~5,712 | ❌ Must split |
| `agent-development` | 415 | ~4,980 | ❌ Must split |

**Every single skill in plugin-dev fails the 4,000-token split threshold.** The worst offender (`command-development` at ~10,608 tokens) pays that cost every time a user asks about slash commands. At the compaction budget ceiling of 5,000 tokens per skill (Rule 23), `command-development` alone at 10,608 tokens busts the limit before the session even runs.

**Cruel irony:** `skill-development` — the skill that teaches progressive disclosure — has only 1 reference file but 637 lines of SKILL.md body. It is the worst practitioner of the discipline it teaches.

**Platform gap: Claude Code only**

No Copilot CLI support. plugin-dev's `create-plugin.md` workflow, all 7 skills, and all 3 agents are scoped exclusively to Claude Code conventions. A plugin-dev user on Copilot CLI gets nothing — the plugin is essentially invisible.

---

### ✅ Compliant Areas

| Rule | Assessment |
|------|-----------|
| Rule 1 (Pattern A or B — no hybrid) | Uses Pattern B (multiple focused entry points + skills) ✅ |
| Rule 3 (each skill one concern) | Each skill addresses exactly one component type ✅ |
| Rule 8 (shared steps → Reference) | `references/` directories per skill with 2–7 files each ✅ |
| Rule 10 (loops/transforms → Script) | 5 bash scripts in `scripts/` (not inlined into SKILL.md) ✅ |
| Rule 11 (>20-line lookup → Reference) | Most tables and schemas moved to `references/` ✅ |
| Rule 21 (description ≤ 60 words) | Skill descriptions are specific with strong trigger phrases ✅ |
| Manifest `name` field | `"name": "plugin-dev"` matches folder name ✅ |
| Agent `## Inputs` | agent-creator has implicit contract (agents are explicit: tools, color, model) ✅ |
| Progressive disclosure support files | Rich `examples/` and `references/` per skill — concept understood ✅ |

---

## 3. Head-to-Head: plugin-dev vs Daedalus / Socrates / Aristotle

### Architecture

| Dimension | plugin-dev | Daedalus / Socrates / Aristotle |
|-----------|-----------|--------------------------------|
| Plugin count | 1 (monolith) | 3 (separation of concerns) |
| Platform | Claude Code only | Claude Code **+** Copilot CLI |
| Lifecycle coverage | Create + Validate | Create → Validate → Maintain (full cycle) |
| Inter-plugin handoffs | None | Explicit `> Next:` callouts + `fix-type` routing |
| Version management | None | Aristotle `bump` skill + `sync_versions.py` |
| Commons build | None | `build-platforms.py` generates dual-platform output |
| Persistent TODO schema | None | `.todos/socrates/<plugin>-YYYYMMDD.md` with `fix-type` |

### Resource sizing (MARKETPLACE.md compliance)

| Metric | plugin-dev | Our trio |
|--------|-----------|----------|
| Command max size | 449 lines ❌ | 44 lines ✅ |
| Skill max size | 884 lines ❌ | 168 lines ✅ |
| Skills failing token limit | 7 of 7 ❌ | 0 of 10 ✅ |
| Cost per skill invocation | 4,980–10,608 tokens | 564–2,016 tokens |

### Functional depth

| Capability | plugin-dev | Our trio |
|-----------|-----------|---------|
| Plugin creation (guided) | ✅ 8-phase workflow | ✅ Daedalus `create` skill |
| Plugin update | ✅ (implied via phases) | ✅ Daedalus `update` skill |
| Commons/dual-platform build | ❌ Not covered | ✅ Daedalus `build` skill |
| Compliance validation | ✅ plugin-validator agent | ✅ Socrates `scanner` agent |
| Skill quality review | ✅ skill-reviewer agent | ⚠️ Not yet separated |
| Agent creation (meta) | ✅ agent-creator agent | ❌ Not built |
| Hook authoring knowledge | ✅ 712-line skill + 4 scripts | ❌ Not built |
| MCP integration knowledge | ✅ 554-line skill + 3 refs | ❌ Not built |
| Plugin settings pattern | ✅ 544-line skill | ❌ Not built |
| Version bumping | ❌ Not covered | ✅ Aristotle `bump` + `sync_versions.py` |
| Health audit (cross-plugin) | ❌ Not covered | ✅ Aristotle `audit` skill |
| Plugin inventory dashboard | ❌ Not covered | ✅ Aristotle `inventory` skill |
| Remediation routing | ❌ Not covered | ✅ Aristotle `triage` + `fix-type` |
| Proactive trigger (post-create) | ✅ plugin-validator auto-fires | ⚠️ Scanner is reactive only |
| Executable bash validators | ✅ 5 granular scripts | ⚠️ 1 structural Python script |

---

## 4. Honest Verdict

**plugin-dev is architecturally inferior to our trio by our own standards — but it is substantively deeper in domain coverage.**

Our rules exist for a reason: a 10,608-token skill is a context budget catastrophe. A 449-line command file is Anti-pattern 2 by name. Anthropic built plugin-dev without a cost-efficiency ruleset; we did the opposite. By our MARKETPLACE.md, plugin-dev would fail Socrates review with multiple critical findings and no easy remediation path — all 7 skills require structural surgery to split.

At the same time, **we should not mistake compliance for completeness.** Our skills are lean and cheap because they are also narrow. plugin-dev covers hooks, MCP, plugin settings, and agent creation — areas our trio simply does not address yet. The knowledge inside plugin-dev's bloated skills is real and valuable. The problem is the delivery vehicle, not the cargo.

**The split question:** is one big plugin better than three specialized ones?

No — not at our scale. The monolith makes every session that invokes any plugin-dev skill pay for all the frontmatter of all 7 skills (Level 1). The 3-plugin split means a user invoking only Socrates doesn't pay Daedalus or Aristotle Level-1 costs. As the skill count grows, the monolith compounds the Level-1 tax.

---

## 5. Items to Borrow from plugin-dev

These are genuine improvements plugin-dev gets right that our trio should adopt:

### 5.1 Granular bash validators (high priority)

plugin-dev ships 5 executable validators: `validate-agent.sh`, `validate-hook-schema.sh`, `test-hook.sh`, `hook-linter.sh`, `parse-frontmatter.sh`. Our `validate_commons.py` only validates structure — it says nothing about agent frontmatter correctness, hook schema validity, or description trigger quality.

**Recommendation:** Add to `veiled-market/scripts/`:
- `validate-agents.sh` — check name, description examples, model, color, tools
- `validate-hooks.sh` — check hooks.json schema, event names, script references

### 5.2 Proactive agent trigger pattern (medium priority)

plugin-validator triggers *after* the user creates or modifies any plugin component — without being asked. Our Socrates scanner waits to be explicitly invoked (`/probe`). This is a missed opportunity: a post-create trigger would catch issues immediately.

**Recommendation:** Add a `PostToolUse` hook in Daedalus that fires the Socrates scanner agent after the `create` skill completes, surfacing findings before the user even asks.

### 5.3 Structured validation output (medium priority)

plugin-validator reports findings in four tiers: Critical / Warnings / Positive Findings / Recommendations. Our Socrates TODO schema has `priority` and `fix-type` but no "positive findings" section. Adding a positive findings section would make Socrates reports more actionable and less adversarial.

### 5.4 Domain knowledge roadmap: hooks, MCP, settings (low priority)

plugin-dev's most useful hidden assets are its references — deep content about hook events, MCP transport types, authentication patterns. These belong in Daedalus as future knowledge skills (properly sized, ≤200 lines, with depth pushed to `references/`):
- `skills/hook-authoring/SKILL.md` — hook event catalogue + patterns
- `skills/mcp-authoring/SKILL.md` — transport types, auth, portability
- `skills/settings-authoring/SKILL.md` — `.local.md` pattern, frontmatter, gitignore

### 5.5 Agent-creator pattern (low priority)

The concept of a meta-agent that generates *other* agents from a description is powerful. Daedalus's `scaffolder` agent handles directory structure — it does not generate agent system prompts. An `agent-creator` variant inside Daedalus, scoped to our platform-specific conventions (including Copilot CLI agent format), would close this gap.

---

## Summary Table

| Verdict | plugin-dev | Daedalus / Socrates / Aristotle |
|---------|-----------|--------------------------------|
| MARKETPLACE.md compliance | ❌ Fails (7 critical violations) | ✅ Clean |
| Dual-platform | ❌ Claude Code only | ✅ Both platforms |
| Architecture soundness | ❌ Monolith, oversized resources | ✅ Separated concerns, within budget |
| Full lifecycle | ❌ Create + validate only | ✅ Create → validate → maintain |
| Domain depth | ✅ Hooks, MCP, settings covered | ❌ Gaps in hooks/MCP/settings |
| Validation tooling | ✅ Granular bash scripts | ⚠️ Structural Python only |
| Proactive triggering | ✅ Post-create auto-validate | ❌ Reactive only |

**Overall verdict: Our trio wins on architecture and compliance. plugin-dev wins on depth. The right answer is to adopt the 5 borrowable items above to close the depth gap while keeping our cost-efficient structure.**
