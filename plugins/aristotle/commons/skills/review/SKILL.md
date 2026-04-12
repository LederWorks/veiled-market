---
name: aristotle-review
description: 'Run a quality eval loop on a plugin skill: generate test prompts, grade trigger accuracy, analyse description breadth, and suggest an improved description if needed.'
user-invocable: false
---

# Review Workflow

Evaluate a skill's description quality through a simulated trigger-grading loop.

## Step 1 — Parse arguments

Arguments passed: `$ARGUMENTS`

- **Plugin name** (required — first token). Error if missing.
- **Skill name** (optional — second token). If omitted, use the plugin's primary skill
  (first `user-invocable: false` skill, or whichever is listed first).

## Step 2 — Read the skill

Read `plugins/<plugin>/commons/skills/<skill>/SKILL.md`. Extract:
- `name` and `description` from frontmatter
- Word count of the description (limit: 60 words)

## Step 3 — Generate test prompts

Ask the user: "Provide 3–5 test prompts that should trigger this skill."

If the user does not respond or asks for automatic generation, derive 3–5 representative
prompts from the `description` field (cover main intent + edge cases).

## Step 4 — Grade each prompt

For each test prompt simulate: "Would an AI invoke this skill given this trigger?"

| Grade | Meaning |
|-------|---------|
| ✅ | Triggers correctly — intent matches skill scope |
| ⚠️ | Triggers but wrong scope — description too broad |
| ❌ | Misses entirely — description too narrow |

## Step 5 — Analyse description quality

Assess:
- Is the trigger intent clear and unambiguous?
- False positive risk: could unrelated prompts trigger this skill?
- False negative risk: could relevant prompts be missed?

## Step 6 — Output quality report

```
## Quality Review: <plugin>/<skill>

Description: "<current description>"
Word count: N (limit: 60)

| Prompt | Trigger? | Grade |
|--------|----------|-------|
| ...    | Yes      | ✅    |
| ...    | No       | ❌    |

**Score:** N/N correct
**Issue:** <description problem, if any>
**Suggested description:** "<improved version>"
```

## Step 7 — Apply fix (optional)

Ask: "Apply suggested description? [y/n]"

If yes:
1. Edit the `description` field in `plugins/<plugin>/commons/skills/<skill>/SKILL.md`
2. End with: "Rebuild with `/forge build <plugin>`"
