# Drafts directory

This directory holds auto-generated draft plugins awaiting evaluation and promotion.

Draft inputs (GitHub Issues) are produced by the **01 · Discover** workflow, which runs a parallel matrix job per `(source, resource_type)` pair and creates one issue per discovered resource. Issues labeled `status/draft` are picked up by the next stage.

Draft plugins are created by the **02 · Compile Plugin Draft** workflow and evaluated/enriched by the **03 · Evaluate & Enrich Drafts** workflow.

Finalized plugins are promoted to `../plugins/` by the **04 · Finalize Plugin** workflow.

> **Do not manually edit files here** — they are managed by GitHub Actions workflows.
