---
name: alex-benchmark-research
description: Use when one or more creator accounts, columns, titles, article samples, or post samples need to be decomposed into account positioning, recurring columns, narrative patterns, and topic density before topic selection or brief building.
---

# Alex Benchmark Research

This skill is an analysis layer for Alex. It sits upstream of `topic-radar` and `content-brief-builder`.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill alex-benchmark-research --input notes/<account>-benchmark.md
```

## Output

```text
content-production/benchmarks/<slug>-benchmark-report.md
content-production/benchmarks/<slug>-benchmark-pack.json
```

## Scope

- Do analyze creator accounts, article sets, post sets, and benchmark samples
- Do infer account positioning, content pillars, recurring columns, narrative patterns, and topic density
- Do output reusable findings for Alex
- Do not depend on one specific crawler
- Do not treat 2024 platform/tool tactics as default current truth
- Do not replace `topic-radar`, `content-brief-builder`, or `case-writer-hybrid`

## Inputs

Preferred inputs:

- a Markdown request with frontmatter
- a CSV sample file
- a Markdown table of benchmark samples
- prior outputs from `wechat-report` or similar collection skills

Read [references/schema.md](references/schema.md) before normalizing unusual inputs.

## What To Analyze

Read [references/analysis-rubric.md](references/analysis-rubric.md). The core passes are:

1. Account structure
2. Recurring columns
3. Narrative patterns
4. Topic density
5. Timeliness risk

## Timeliness Gate

Always classify meaningful findings into:

- `Evergreen`
- `Verify-Now`
- `Legacy-2024`

Default rules:

- prefer the last 90 days
- down-rank content older than 180 days unless the user explicitly requests historical analysis
- never carry forward old model names, pricing, plugin paths, deployment instructions, or platform rule claims without verification

Read [references/legacy-2024-notes.md](references/legacy-2024-notes.md) when the source material comes from Alex's 2024 course stack.

## Handoff

Use the benchmark output in one of three ways:

- feed strategic patterns into `topic-radar`
- feed a chosen angle plus benchmark findings into `content-brief-builder`
- reuse narrative or column findings for future `alex-title-lab`

## Report Standard

The report must answer:

- what this account really promises the audience
- what its 3-5 main content pillars are
- which recurring columns create publishing habit
- what hook, structure, proof, and CTA patterns repeat
- which topics are dense, rising, stable, or fading
- what Alex should borrow, adapt, or avoid

Use [references/report-template.md](references/report-template.md) as the output shape.
