---
name: case-writer-hybrid
description: Expand a structured brief in `content-production/inbox/` into a reusable long-form markdown article draft with argument sections and supporting cases. Use when Codex needs to turn a stage-1 brief into `article_markdown` for the content factory pipeline or for downstream `generate-image` and `wechat-formatter` steps.
---

# Case Writer Hybrid

Turn the structured brief into a stage-1 article draft that can flow into image generation and WeChat formatting.

## Quick Start

Run the default command:

```bash
.venv/bin/python -m skill_runtime.cli run-skill case-writer-hybrid --input content-production/inbox/20260403-ai-content-system-brief.md
```

## Prepare Input

Expect a markdown file with these sections:

- `基础信息`
- `核心观点`
- `背景与语境`
- `论证方向`
- `可用案例 / 素材`

Important fields inside `基础信息`:

- `date`
- `slug`
- `topic`
- `target_reader`
- `publish_goal`

## Follow Drafting Workflow

1. Read the brief and preserve explicit user-supplied claims, framing, and evidence.
2. Use `论证方向` as the backbone for the major argument sections.
3. Pull material from `可用案例 / 素材` into the matching sections instead of inventing new examples first.
4. Build a stable first draft structure: title, 导语, 问题提出, 核心判断, 论证段, 结论, 可传播总结.
5. Fill gaps conservatively when the brief is sparse and keep uncertainty implicit rather than overstating claims.

## Write Output

Write the markdown draft to:

```text
content-production/drafts/<slug>-article.md
```

Optimize for stable first-draft generation rather than high-creativity final copy.

## Respect Constraints

- Treat the result as a draft, not a final polished article
- If the brief is sparse, preserve structure and fill gaps conservatively
- Prefer explicit user-supplied arguments over invented framing

## Read Related Files

- Runtime entry: `skill_runtime/engine.py`
- Usage guide: `docs/case-writer-hybrid-execution-spec.md`
- Downstream skills: `generate-image`, `wechat-formatter`
