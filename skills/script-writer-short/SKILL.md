---
name: script-writer-short
description: Use when a Markdown article, brief, or topic note needs to become a short oral video script, talking-head script, reels script, 视频号口播, or 60-180 second social video version.
---

# Script Writer Short

Convert an article or topic note into a short oral script. This skill is for video reuse, not long-form article writing.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill script-writer-short --input content-production/drafts/<slug>-article.md
```

## Output

```text
content-production/drafts/<slug>-script.md
content-production/drafts/<slug>-script.json
```

## Structure

- Hook: 20-30 Chinese characters, first 3 seconds.
- Introduction: set up why the viewer should care.
- Body: 2-3 points, each with conclusion + example/benefit.
- Summary: one memorable line plus comment/follow prompt.
- 拍摄提示: pacing, shot style, caption hint.

## Guardrails

- Keep it oral and compact.
- Preserve the article's core claim.
- Prefer one concrete story or scenario over abstract explanation.
- Do not add unverifiable facts.
