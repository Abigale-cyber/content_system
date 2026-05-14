---
name: alex-account-positioning
description: Use when Alex needs to define or refine a creator account's target audience, value promise, content pillars, differentiation, and conversion path before benchmark analysis, topic selection, or brief writing.
---

# Alex Account Positioning

This skill is the strategy layer before `alex-benchmark-research`, `topic-radar`, and `content-brief-builder`.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill alex-account-positioning --input notes/<account>-positioning.md
```

## Output

```text
content-production/positioning/<slug>-positioning-report.md
content-production/positioning/<slug>-positioning-pack.json
```

## Scope

- Do define target audience, value promise, content pillars, differentiation, and conversion path
- Do help narrow broad "I want to do AI self-media" ambitions into one coherent account direction
- Do produce a reusable positioning artifact for downstream skills
- Do not discover hot topics
- Do not write full briefs
- Do not write articles

## Inputs

Preferred inputs:

- Markdown request with frontmatter
- founder or creator notes
- benchmark conclusions from `alex-benchmark-research`
- manually written audience, background, and monetization constraints

Read [references/schema.md](references/schema.md) before preparing a new request.

## What To Decide

Read [references/positioning-rubric.md](references/positioning-rubric.md). The core questions are:

1. Who exactly is this account for?
2. What recurring pain or ambition does it serve?
3. What one-line promise should the audience remember?
4. What 3-5 content pillars make the account coherent?
5. What makes this account different from generic AI content?
6. What should the likely conversion path be?

## Guardrails

- Avoid "everyone is the audience"
- Avoid encyclopedia-style positioning
- Avoid promising value with no operational proof
- Prefer one sharp direction over several diluted ones

## Handoff

Use the positioning output:

- before `alex-benchmark-research` to clarify what kinds of benchmark accounts matter
- before `topic-radar` to evaluate whether a topic matches the account's pillars
- before `content-brief-builder` to keep briefs consistent with the account promise

## Timeliness Gate

Tag claims as:

- `Evergreen`
- `Verify-Now`
- `Legacy-2024`

Keep durable audience and value logic. Verify current tool stacks, platform tactics, and trend-driven positioning language.
