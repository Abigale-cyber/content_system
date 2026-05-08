---
name: case-writer-hybrid
description: Expand a structured brief in `content-production/inbox/` into a reusable long-form markdown article draft, then run a local writer / critic / judge quality loop with a constrained humanization pass. Use when Codex needs a stage-1 article draft plus reusable writing sidecars for downstream `generate-image` and `wechat-formatter`.
---

# Case Writer Hybrid

Turn the structured brief into a stage-1 article draft, a writing pack sidecar, and a review trace that can flow into image generation and WeChat formatting.

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

Optional but recommended extra sections:

- `SCQA 结构`
- `风险提醒`
- `素材来源可信度`

## Follow Drafting Workflow

### 自动模式

默认 CLI 命令继续走自动模式：

1. Read the brief and preserve explicit user-supplied claims, framing, and evidence.
2. Use `论证方向` as the backbone for the major argument sections.
3. Pull material from `可用案例 / 素材` into the matching sections instead of inventing new examples first.
4. If present, use `SCQA 结构` to sharpen the problem statement and core answer.
5. If present, carry `风险提醒` and `素材来源可信度` into the writing pack; low-confidence materials must be treated as leads to verify, not finished facts.
6. Build a stable first draft structure: title, 导语, 问题提出, 核心判断, 论证段, 结论, 可传播总结.
7. Run up to 3 local rounds of `writer -> critic -> humanizer-zh -> judge`.
8. In the judge loop, pay special attention to `story_resonance`: if the draft is too abstract, the next round should add a short story slice with人物、冲突、转折 and a reader-facing resonance anchor such as“你有没有这种感觉”or“说白了”.
9. If the score still fails after 3 rounds, stop and emit a quality-gate notice instead of continuing downstream.

### 交互模式

当用户说“先看大纲”“先确认标题”“交互式写”时，不调用 `runtime.py`，而是按下面的步骤走：

0. 写前门控：读取 `references/pre-write-checks.md`
   - 核心判断够硬吗？
   - 读者够具体吗？
   - 素材充足吗（至少 3 条）？
   - 任一不通过就停下来，先改 brief
1. 读取 brief，提取 `topic`、`target_reader`、`publish_goal`、`论证方向`、`SCQA`
2. 阶段一，先出标题和大纲
   - 读取 `references/title-and-packaging.md`
   - 生成 3 个标题候选
   - 读取 `references/framework-selection.md`
   - 从五大框架和六种结构模板里选最合适的一种
   - 基于 SCQA 产出章节大纲
   - 停下来等用户确认标题和大纲
3. 阶段二，按确认后的大纲写全文
   - 开头读取 `references/hook-and-ending.md`
   - 正文读取 `references/framework-selection.md`
   - 如果需要增强故事感，读取 `references/story-injection.md`
   - 保持每段不超过 5 行，每句尽量不超过 25 字，先说观点再说理由
4. 写后自检：再次读取 `references/pre-write-checks.md`
5. 去 AI 痕迹和回改
   - 先读取 `references/revision-loop.md`
   - 按“结构 → 语言 → 共鸣锚点”跑三轮回改
   - 再按 `references/framework-selection.md` 的去 AI 痕迹表做一轮精修
   - 需要更强去 AI 痕迹时，再串联 `humanizer-zh`
6. 输出到 `content-production/drafts/<slug>-article.md`

## Write Output

Write the markdown draft to:

```text
content-production/drafts/<slug>-article.md
```

Also write:

```text
content-production/drafts/<slug>-writing-pack.md
content-production/drafts/<slug>-writing-pack.json
content-production/drafts/<slug>-review-trace.json
```

If the draft fails the quality gate after 3 rounds, also write:

```text
content-production/published/YYYYMMDD-<slug>-quality-gate.md
```

## Respect Constraints

- Treat the result as a controlled local draft loop, not a free-form creative writer
- If the brief is sparse, preserve structure and fill gaps conservatively
- Prefer explicit user-supplied arguments over invented framing
- Do not continue to image generation or formatting if the quality gate fails

## Read Related Files

- Runtime entry: `skill_runtime/engine.py`
- Usage guide: `docs/case-writer-hybrid-execution-spec.md`
- Downstream skills: `generate-image`, `wechat-formatter`
- Interactive references:
  - `references/framework-selection.md`
  - `references/hook-and-ending.md`
  - `references/pre-write-checks.md`
  - `references/revision-loop.md`
  - `references/story-injection.md`
