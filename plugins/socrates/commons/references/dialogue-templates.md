# Dialogue Templates

Question templates for Phase 2 of the Socrates workflow. Use the matching template
for each ambiguous finding. Adapt the placeholders; keep the framing intact.

---

**Pattern A vs B choice**
> "Your plugin has [N] commands. Do the actions share common sub-procedures, or are they
> fully independent with different argument signatures and separate primary agents?
> (Shared sub-procedures → Pattern A is appropriate. Fully independent → Pattern B.)"

---

**Agent type (Workflow vs Domain Expert)**
> "`agents/<name>.md` has no `## Inputs` section. Is this agent designed to receive a
> fixed parameter contract from a calling skill (Workflow Agent), or does it need direct
> tool access — Bash, file reads, MCP — without a fixed contract (Domain Expert Agent)?
> The distinction matters: Workflow Agents must declare `## Inputs`; Domain Expert Agents
> must not have one."

---

**Resource placement**
> "`scripts/<name>` looks like a generic utility. Is it used exclusively by this plugin,
> or do other plugins also call it? Generic utilities used by 2+ plugins belong in
> `copilot/scripts/`."

---

**Knowledge Skill user-invocable flag**
> "`skills/<name>/SKILL.md` is marked `user-invocable: true` but has no numbered steps
> or interactive prompts. Should users invoke this skill explicitly, or should it activate
> passively when the description matches the user's intent? (If passive → `user-invocable: false`.)"

---

**Orphaned hook scripts**
> "`hooks/<script>` exists but is not wired in `hooks.json`. Is this intentional —
> meaning you invoke it manually — or is the wiring missing by oversight?"
