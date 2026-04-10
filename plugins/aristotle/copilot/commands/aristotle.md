---
name: steward
description: >
  Plugin lifecycle orchestrator. Triages Socrates findings, manages version bumps,
  audits cross-plugin health, shows inventory, and runs quality review loops.
  Trigger on: /steward, "triage findings", "bump version", "audit all plugins",
  "plugin inventory", "review plugin quality".
argument-hint: <triage|bump|audit|inventory|review> [plugin] [args]
---

# /steward

Route to the Aristotle skill for the requested action.

## Arguments

The user provided: `$ARGUMENTS`

Parse the first token as **action**.

## Routing

| Action | Skill |
|--------|-------|
| `triage` | `skills/triage/workflow.md` |
| `bump` | `skills/bump/workflow.md` |
| `audit` | `skills/audit/workflow.md` |
| `inventory` | `skills/inventory/workflow.md` |
| `review` | `skills/review/workflow.md` |

Load the skill file for the matched action and follow its workflow. Pass all remaining arguments to the loaded skill.

If the action is unrecognised or no arguments are given, show the table above as a usage guide and stop.
