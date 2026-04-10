# Doc Review Findings

> **Reviewer:** Doc-review agent (claude-sonnet-4-6)
> **Date:** 2026-04-10
> **Scope:** 9 documentation files reviewed against the atlas + apollo architecture

---

## A. Stale trio references

### docs/PLUGIN-LIFECYCLE.md

- **Line 3**: Opening paragraph calls this "the shared specification for the Daedalus → Socrates → Aristotle plugin management cycle." Entire framing must become the Apollo management cycle.
- **Lines 12–16**: Lifecycle diagram shows `/forge create`, `/forge update`, `/forge remediate` — old subcommand names. New names: `forge`, `edit`, `assemble`, `fix`.
- **Lines 20–25**: "The three philosophers" table lists `daedalus`, `socrates`, `aristotle` with old verbs. Must be replaced with Apollo skill table (forge/edit/assemble/fix, probe, classify/increment/survey/catalog/grade).
- **Lines 28–38**: Handoff protocol callout table still references `/forge build`, `/forge remediate`, `/steward triage`, `/steward audit`, `/steward bump` using old names. Update to: `/forge assemble` → `/probe`, `/forge fix` → `/probe`, `/steward classify`, `/steward survey`, `/steward increment`.
- **Lines 255–261**: `fix-type` value table says "Routed to: **Daedalus** auto-fix" — should be "Apollo auto-fix" throughout (6 occurrences).
- **Lines 265–288**: "Aristotle Triage Protocol" section heading and content. Rename to "Apollo Classify Protocol". References to `Aristotle` (3 mentions), `/forge remediate` (2 mentions), and triage concept throughout.
- **Lines 341–350**: "Philosopher Command Verbs" table lists `daedalus`, `socrates`, `aristotle` with old mappings. Should show `apollo` → `/forge` + `/probe` + `/steward`, or be replaced with the new vocabulary table.

### docs/arch-veiled-market.md

- **Line 74**: Directory tree entry `docs/PLUGIN-LIFECYCLE.md` is annotated as "Authoritative spec: Daedalus→Socrates→Aristotle cycle" — update annotation.
- **Lines 377–383**: "Commons-Built Plugins" plugin status table lists `daedalus` (create, update, build, remediate), `socrates` (probe), `aristotle` (triage, bump, audit, inventory, review) all with ✅ Built. Should show `atlas` + `apollo` instead.
- **Lines 385–408**: "The Plugin Lifecycle Cycle" section and handoff chain table reference `/forge create`, `/forge update`, `/forge build`, `/forge remediate`, `/steward triage`, `/steward audit`, `/steward bump` — all old names.
- **Line 440**: "Planned Work" section says "Next Commons-Built Plugin: `zeno`". Once atlas + apollo are added, this is no longer the next priority; at minimum add atlas and apollo to the status table before zeno.

### docs/plugin-dev-comparison.md

- **Throughout**: Section headings, tables, and body text consistently refer to "Daedalus / Socrates / Aristotle" (35+ occurrences). The entire document is framed as a comparison against the trio. Specific high-impact locations:
  - Lines 45–60: "Daedalus / Socrates / Aristotle (veiled-market)" contestant table with old skill names (create, update, build, remediate, triage, bump, audit, inventory, review).
  - Lines 127–133: Head-to-head architecture table — trio column labels.
  - Lines 146–167: Functional depth table — "Daedalus create", "Daedalus update", "Daedalus build", "Socrates scanner", "Aristotle bump", "Aristotle audit", "Aristotle inventory", "Aristotle triage".
  - Lines 213–214: "keep the trio" recommendation. The verdict §6 explicitly recommends **not** merging — this section directly contradicts implementation-plan.md which documents the merge decision as already made.
  - Lines 284–295: Final summary table and recommendation paragraph ("keep the trio").
  - Lines 369–411: Second comparison section (§3) with same old trio references.
  - Lines 430–458: "Items to Borrow from plugin-dev" refers to adding skills to Daedalus (§5.4, §5.5).
  - **Note:** This document captures the pre-merge analysis. After Phase 5 completes, it should either be archived or updated with a header noting it reflects pre-Apollo architecture.

### docs/plugin-lifecycle-blueprint.md

- This entire document is stale. It is the "trio synthesis" blueprint that predates the Apollo merge decision. It retains the trio architecture throughout:
  - Line 1: Title "Trio Synthesis"
  - Lines 12–28: Decision summary describes keeping the trio as three separate plugins
  - Lines 34–59: Architecture diagram shows DAEDALUS, SOCRATES, ARISTOTLE as separate boxes
  - Lines 22–24: References `render_template.py` as already present in `veiled-market/scripts/` (see Section D below)
  - implementation-plan.md Phase 6 already flags this as stale and in need of update

### veiled-market/CLAUDE.md (Plugin Roadmap table)

- **Lines 13–18** (Plugin Roadmap table): Lists `daedalus` (create, update, build, remediate), `socrates` (probe), `aristotle` (triage, bump, audit, inventory, review) all as ✅ Built. Zeno is listed as the only planned plugin.
  - Must be updated to show: `atlas` (scaffold, init, sync, validate) + `apollo` (forge, edit, assemble, fix, probe, classify, increment, survey, catalog, grade, author, integrate, configure)
  - The trio entries should be removed or marked as deprecated

- **Lines 27–34** (Plugin Lifecycle cycle diagram): Shows `/forge create|update → /forge build → /probe → /steward triage → /forge remediate → /forge build → /probe → /steward bump`. All old subcommand names.

- **Key files table** (near bottom): `docs/PLUGIN-LIFECYCLE.md` is described as "Authoritative spec for the Daedalus → Socrates → Aristotle management cycle" — update description.

### ../CLAUDE.md (workspace root)

- No plugin roadmap table present. The workspace-root CLAUDE.md only describes the directory ownership/platform table and cross-project conventions — no veiled-market plugin listings. **No stale trio references found here.**

---

## B. implementation-plan.md vs plugin-inventory.md gaps

### Files in plugin-inventory.md not in implementation-plan.md

No significant gaps found — both documents cover the same set of files. plugin-inventory.md is the detailed file-by-file expansion of the structure described in implementation-plan.md.

### Line count discrepancies (>20 lines)

The following planned line counts differ between the two documents:

| File | implementation-plan.md | plugin-inventory.md | Delta | Flag |
|------|------------------------|---------------------|-------|------|
| `atlas/commons/references/stubs/` | Not enumerated individually | 26 stubs listed (not 32 as stated in totals) | Table lists 26 rows but totals say 32 | ⚠️ Inconsistency within plugin-inventory.md itself: the stubs table has 26 entries but §1.2 says "32 stubs" and §7 grand totals uses 32. |
| `apollo/skills/probe/SKILL.md` | Not given explicit target | 168 lines | — | OK (within budget) |
| `apollo/references/shared-steps.md` | Not given explicit size | ~120 lines (merged) | — | OK |
| `atlas/templates/templates.json` | "extend with scaffold scope entries" (no size) | ~870 lines | — | Note: 870 lines is a large registry file; no hard limit on templates but worth flagging for awareness |

### Structural gap: `atlas-scaffold` skill name inconsistency

- **implementation-plan.md** uses skill name `atlas-scaffold` (line 259, vocabulary table).
- **plugin-inventory.md §1.3** also uses `atlas-scaffold` ✅
- No discrepancy.

### Stubs count inconsistency (within plugin-inventory.md)

- **§1.5 heading**: "References (3 + 32 stubs)"
- **§1.5 stubs table**: Lists only **26 files** (rows in the table)
- **§1.10 Atlas Totals**: "References: 3 + 32 stubs"
- **§7 Grand Totals**: References for Atlas = 35 (3+32)
- The table is missing 6 stub entries. This is an internal inconsistency in plugin-inventory.md.

---

## C. Rule 21 violations (skill descriptions >60 words)

Rule 21 requires: description ≤ 60 words (Level-1 tax on every session).

All 14 proposed skill descriptions were checked. **Zero violations found.**

| Skill | Word count | Status |
|-------|-----------|--------|
| atlas-scaffold | 30 | ✅ |
| apollo-forge | 30 | ✅ |
| apollo-edit | 23 | ✅ |
| apollo-assemble | 19 | ✅ |
| apollo-fix | 21 | ✅ |
| apollo-probe | 30 | ✅ |
| apollo-classify | 23 | ✅ |
| apollo-increment | 22 | ✅ |
| apollo-survey | 21 | ✅ |
| apollo-catalog | 22 | ✅ |
| apollo-grade | 25 | ✅ |
| apollo-author | 27 | ✅ |
| apollo-integrate | 28 | ✅ |
| apollo-configure | 24 | ✅ |

---

## D. render_template.py status

**Verdict: No doc incorrectly claims the file already exists in `veiled-market/scripts/`.**

Findings per document:

- **plugin-inventory.md §3.1** (line 351): Lists `scripts/render_template.py` with annotation `(to port from copilot monolith)` — **correctly marked as pending** ✅
- **plugin-inventory.md §4.1** (line 392): Porting table correctly maps `copilot/scripts/render_template.py` → `veiled-market/scripts/render_template.py (Tier 1)` — **correctly shows destination, not source** ✅
- **arch-veiled-market.md §Known Constraints #9** (line 430): Explicitly states "no `render_template.py` script" exists for the current build — **correct** ✅
- **arch-veiled-market.md scripts table** (lines 326–334): Does NOT list `render_template.py` among existing scripts — **correct** ✅
- **veiled-market/CLAUDE.md scripts table**: Does NOT list `render_template.py` — **correct** ✅
- **plugin-lifecycle-blueprint.md** (line 57): Shows `render_template.py` in an architecture diagram of `veiled-market/scripts/` — **this is a stale blueprint document** that predates the current architecture. The diagram shows it as a planned/desired state, not as confirmed-existing. However, a reader unfamiliar with the document's stale status could mistake the diagram for current truth. Flag for cleanup when plugin-lifecycle-blueprint.md is updated in Phase 6.
- **implementation-plan.md Phase 3** (line 199): "Port `render_template.py` to `veiled-market/scripts/` (Tier 1)" — **correctly framed as future work** ✅

**On-disk check**: `veiled-market/scripts/render_template.py` does not exist. Confirmed.

---

## E. Recommended edits for Task 30 (docs update)

### docs/PLUGIN-LIFECYCLE.md — HIGH PRIORITY

- Replace "Daedalus → Socrates → Aristotle" framing throughout with "Apollo lifecycle management"
- Update lifecycle diagram to show `/forge assemble` (not `/forge build`) and `/forge fix` (not `/forge remediate`), remove `/forge create`/`/forge update`
- Replace "three philosophers" table with Apollo command/skill table
- Update handoff protocol callouts to use new subcommand names
- Replace all "Daedalus auto-fix" references (6×) with "Apollo auto-fix"
- Rename "Aristotle Triage Protocol" → "Apollo Classify Protocol"; update body
- Replace "Philosopher Command Verbs" table with new vocabulary table (atlas/apollo only; remove zeno if not yet scoped)

### veiled-market/CLAUDE.md — HIGH PRIORITY

- Replace Plugin Roadmap table: remove daedalus/socrates/aristotle rows, add atlas + apollo rows with new skill names and ✅/🔲 status
- Update Plugin Lifecycle cycle diagram to use new subcommand names
- Update "Key files" table entry for `docs/PLUGIN-LIFECYCLE.md`
- Update any references to the three-philosopher cycle in prose

### docs/arch-veiled-market.md — MEDIUM PRIORITY

- Update line 74 annotation for `PLUGIN-LIFECYCLE.md`
- Replace "Commons-Built Plugins" status table (lines 377–383): remove trio, add atlas + apollo
- Update "The Plugin Lifecycle Cycle" section (lines 385–408) to use new subcommand names and Apollo framing
- Add atlas and apollo to the status table before zeno in "Planned Work"

### docs/plugin-lifecycle-blueprint.md — MEDIUM PRIORITY (Phase 6)

- Either: add a deprecation/superseded header pointing to implementation-plan.md + plugin-inventory.md as the authoritative source
- Or: rewrite to reflect the Apollo architecture
- At minimum: add a banner note: "⚠️ This document reflects the pre-merge trio architecture. See implementation-plan.md for the current Apollo design."

### docs/plugin-dev-comparison.md — LOW PRIORITY (post-Phase 5)

- Add a header note indicating this comparison was written against the trio (pre-Apollo) architecture
- Update "Verdict" sections that recommend keeping the trio to acknowledge the merge has been decided
- Update all "Daedalus/Socrates/Aristotle" column references to "Apollo" in tables
- Update "items to borrow" sections that reference adding skills "to Daedalus" → "to Apollo"
- Consider archiving as `docs/archive/plugin-dev-comparison-trio.md` once Apollo is live

### docs/plugin-inventory.md — LOW PRIORITY (Phase 6)

- Fix internal stubs inconsistency: the stubs table lists 26 files but §1.5 heading, §1.10, and §7 all say 32. Either add the 6 missing stub entries or correct the counts.

### README.md — LOW PRIORITY

- README.md only lists discovery-pipeline plugins (terraformer, easy-*). The atlas/apollo commons-built plugins are not listed. Consider adding an "Infrastructure plugins" section once they are live.
- No stale trio references found in README.md (trio is not mentioned).
