# Rules Compact Reference

> **Authoritative source:** `docs/MARKETPLACE.md`. This compact reference is for quick lookup during Phase 3. Always load MARKETPLACE.md first.

Distilled from `docs/MARKETPLACE.md`. Use this as your verdict checklist during Phase 3.

---

## The 22 Standard Rules

| # | Rule | Violation signal | Severity |
|---|---|---|---|
| 1 | Plugin uses Pattern A OR Pattern B — never hybrid. Platform plugins (copilot, project) may have multiple commands, each independently following A or B. | Command file has inline steps AND a routing table | 🔴 |
| 2 | Command file contains ONLY routing logic and argument parsing. No conditional domain logic, numbered procedures, or sub-procedure blocks. | Command file > 66 lines OR contains numbered steps | 🔴 |
| 3 | Every skill addresses exactly one concern. If the name requires "and", split it. | Skill name contains "and" | 🔴 |
| 4 | SKILL.md body MUST NOT exceed 500 lines. | SKILL.md > 500 lines | 🔴 |
| 5 | Knowledge Skill (user-invocable: false) MUST NOT contain numbered steps or interactive prompts. | Knowledge Skill has numbered steps | 🔴 |
| 6 | Procedural Skill (user-invocable: true) MUST NOT rely on passive description-based triggering. | Skill should logically be user-invocable: false | 🟡 |
| 7 | Workflow Agent MUST declare `## Inputs` with typed parameters. Domain Expert Agent MUST NOT have `## Inputs`. | Agent has wrong Inputs presence for its type | 🔴 |
| 8 | Same setup steps appearing in 2+ skills within one plugin MUST be extracted to a Reference. | Duplicate steps across skills in same plugin | 🟡 |
| 9 | Same setup steps appearing across 2+ plugins MUST be extracted to copilot. | Duplicate steps across plugins | 🟡 |
| 10 | Logic with loops, data transformation, or file parsing MUST be a script in `scripts/`, not inline AI instructions. | Inline loop/transform instructions in SKILL.md | 🔴 |
| 10a | Scripts used by 2+ plugins MUST live in `plugins/copilot/scripts/`. Plugin-local scripts only for single-plugin use. | Cross-plugin script buried in domain plugin | 🟡 |
| 11 | Lookup content > 20 lines (tables, catalogues, schema docs) MUST live in a Reference. | Large inline table/catalogue in SKILL.md | 🟡 |
| 12 | File-generation boilerplate with predictable variable slots MUST use Jinja2 templates in `templates/`. | AI-generated boilerplate inline in skill steps | 🟡 |
| 13 | Every hook script MUST be wired in `hooks.json`. Orphaned hook scripts are defects. | Script in `hooks/` not in `hooks.json` | 🔴 |
| 14 | `preToolUse` hook MUST be used for guards blocking destructive operations. Using `postToolUse` as a guard is a defect. | `postToolUse` hook used as a guard | 🔴 |
| 15 | `sessionStart` hook MUST be used only for context injection, not side effects. | `sessionStart` causes file writes or mutations | 🔴 |
| 16 | MCP config MUST only be added when all three conditions are met: (1) external API not reachable via Bash, (2) API requires auth/session, (3) consumer is a Domain Expert Agent. | MCP on Workflow Agent, or unnecessary MCP | 🔴 |
| 17 | `copilot` is the canonical home for any skill, agent, reference, or script that is generic and reused by 2+ plugins. | Generic utility buried in domain plugin | 🟡 |
| 18 | Domain plugin MUST NOT contain generic utility logic used by 2+ plugins. | Cross-plugin utility in domain plugin | 🟡 |
| 19 | `arch-docs` plugin MUST NOT have `user-invocable: false` skills duplicating Knowledge Skills in `copilot`. | Duplicate knowledge skill | 🟡 |
| 20 | When SKILL.md body > 300 lines, measure token cost (lines × 12). If > 4,000 tokens, MUST split. | Skill 300–500 lines, cost > 4,000 tokens | 🔴 |
| 21 | Description fields in SKILL.md frontmatter MUST be ≤ 60 words. | Description > 60 words | 🔴 |
| 22 | Every plugin MUST have a non-empty `hooks.json`. If no hooks, must be `{"version": 1, "hooks": {}}`. | `hooks.json` absent | 🔴 |

---

## The 13 Anti-patterns

| # | Name | Signal | Severity |
|---|---|---|---|
| AP1 | Orphaned hook scripts | Scripts in `hooks/` not wired in `hooks.json` | 🔴 (Rule 13) |
| AP2 | Domain logic in command files | Command file with inline workflow steps or > 66 lines | 🔴 (Rule 2) |
| AP3 | Knowledge skills misclassified as procedural | `user-invocable: true` on a skill with no numbered steps, no user interaction | 🟡 (Rule 5/6) |
| AP4 | Inline large reference tables in SKILL.md | Table or catalogue > 20 lines inline in skill body | 🟡 (Rule 11) |
| AP5 | Workflow Agents without `## Inputs` | Workflow Agent missing `## Inputs` section | 🔴 (Rule 7) |
| AP6 | Generic utility agents buried in domain plugins | Reusable agent not in `copilot/agents/` | 🟡 (Rule 18) |
| AP7 | Forcing independent entry points into Pattern A | Single router for commands with different args, different agents, no shared sub-procedures | 🟡 (Rule 1) |
| AP8 | Knowledge Skill descriptions too broad | Description matches too many sessions passively (e.g., "any git operation") | 🟡 (Rule 21) |
| AP9 | MCP config on a Workflow Agent | `mcp.json` entry consumed by a fixed-contract Workflow Agent | 🔴 (Rule 16) |
| AP10 | Absent hooks.json | Plugin directory has no `hooks.json` at all | 🔴 (Rule 22) |
| AP11 | Duplicating content across instructions files and Knowledge Skills | Same best-practice rules in both `*.instructions.md` and a Knowledge Skill | 🟡 (Rule 21) |
| AP12 | Coding standards in `copilot-instructions.md` | `copilot-instructions.md` > 150 lines; contains file-type rules that belong in `*.instructions.md` | 🔴 |
| AP13 | TODO files written to repository root | Command writes `.copilot-todo.md` or similar to repo root instead of `.todos/<plugin>/` | 🔴 |

---

## Size Limits Quick Reference

| Resource | Hard limit | Warning zone |
|---|---|---|
| `copilot-instructions.md` | ≤ 150 lines | > 100 lines |
| Command file (any pattern) | ≤ 66 lines | > 50 lines |
| Procedural Skill SKILL.md | ≤ 200 lines (≤ 500 absolute max) | > 150 lines |
| Knowledge Skill SKILL.md | ≤ 174 lines | > 135 lines |
| Skill description (words) | ≤ 60 words | > 45 words |
| Workflow Agent | 52–100 lines | > 100 lines |
| Domain Expert Agent | ≤ 280 lines | > 200 lines |
| Reference | ≤ 430 lines | — |

---

## Pattern A vs Pattern B Decision

**Use Pattern A (single router + skills)** when:
- Actions share a common command prefix (`/plugin action`)
- 2+ actions share common sub-procedures
- Unified UX is valuable for discoverability

**Use Pattern B (focused independent commands)** when:
- Entry points have different argument signatures
- Entry points delegate to different primary agents
- No shared sub-procedures between actions

**Never:** Inline all action workflows in one command file (AP2).
