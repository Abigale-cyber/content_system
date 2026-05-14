---
name: alex-title-lab
description: Use when title samples, benchmark headlines, topic notes, or a chosen angle need to be analyzed into title patterns and then expanded into Alex-ready headline variants before brief writing or publishing.
---

# Alex Title Lab

This skill is Alex's dedicated headline analysis and experimentation layer.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill alex-title-lab --input notes/<topic>-titles.md
```

## Output

```text
content-production/titles/<slug>-title-report.md
content-production/titles/<slug>-title-pack.json
```

## Scope

- Do analyze headline samples into repeatable patterns
- Do classify title drivers, patterns, and click triggers
- Do generate candidate title variants for Alex
- Do not replace `topic-radar` or `content-brief-builder`
- Do not judge platform rules, pricing, or model names without current verification

## Inputs

Preferred inputs:

- Markdown request with frontmatter
- CSV title sample list
- Markdown table of title samples
- benchmark outputs or manually assembled title lists

Read [references/schema.md](references/schema.md) before preparing new inputs.

## What To Analyze

Read [references/title-rubric.md](references/title-rubric.md). Focus on:

1. title patterns
2. title drivers
3. hook styles
4. reader value signals
5. Alex adaptation opportunities

## Handoff

Use this skill:

- after `alex-benchmark-research` when benchmark accounts reveal strong title families
- before `content-brief-builder` when Alex needs a sharper packaging direction
- before publishing when one topic needs several title experiments

## Timeliness Gate

Always separate:

- `Evergreen` title psychology
- `Verify-Now` trend pegs, current platform language, and temporary buzzwords
- `Legacy-2024` patterns tied to obsolete tools or ecosystem states

Use [references/legacy-2024-notes.md](references/legacy-2024-notes.md) when Alex source material comes from 2024 course assets.
