---
name: probe
description: >
  Validates a plugin against marketplace-patterns rules using Socratic dialogue.
  Spawns a scanner, asks targeted questions only where design intent is ambiguous,
  then writes a structured TODO file and inline summary. Use when auditing any
  marketplace plugin for rule compliance, structural issues, or anti-patterns.
  Trigger on: /probe, "validate this plugin", "audit plugin", "check plugin rules".
argument-hint: <path/to/plugin>
---

# /probe

Route to the Socrates workflow.

## Arguments

Plugin path: `$ARGUMENTS`

## Instructions

Read `skills/socrates/workflow.md` and follow the workflow it describes.

Pass as context:
- **Plugin path:** `$ARGUMENTS` (if empty, the skill will ask for one)
