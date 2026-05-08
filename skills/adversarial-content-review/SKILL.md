---
name: adversarial-content-review
description: Use when a finished Markdown article needs independent review, publish readiness judgment, quality scoring, or concrete revision advice before formatting or publishing.
---

# Adversarial Content Review

Review a finished article without rewriting it. This skill outputs a structured report and a machine-readable sidecar for workflow gates.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill adversarial-content-review --input content-production/drafts/<slug>-article.md
```

## Scope

- Do review finished Markdown drafts.
- Do produce role-based critique, five-dimension scoring, verdict, and specific revision advice.
- Do block downstream work when the article needs revision or rewrite.
- Do not rewrite the article.
- Do not generate images, formatting, or publishing artifacts.

## Review Passes

1. 笔杆子审：检查观点、结构、证据和章节推进。
2. 参谋审：站在目标读者视角，判断哪里看不懂、哪里想跳过、哪里有共鸣。
3. 裁判裁定：按五维度给分并输出结论。

## Verdict Rules

- `通过`：总分 >= 8
- `需修改`：总分 5-7.9
- `需重写`：总分 < 5

## Outputs

```text
content-production/reviews/<slug>-review-report.md
content-production/reviews/<slug>-review-report.json
```
