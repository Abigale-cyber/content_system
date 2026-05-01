---
name: ai-dalaba
description: Unified AI digest skill for AI大喇叭. Fetches builders signals plus the latest AI news in one run, deduplicates overlaps with builders first, and outputs a single Chinese digest-ready JSON context. Use this for daily digest, AI快讯, builders + latest news, morning briefing, and scheduled AI大喇叭 pushes.
---

# AI大喇叭

`ai-dalaba` is the single digest skill for AI大喇叭. It replaces the old split workflow and always uses one direct script entrypoint.

## When To Use

Use this skill whenever the user wants:

- 今日 AI 日报
- builders 动向 + 最新资讯的融合快讯
- AI 大喇叭定时推送
- AI 快讯 / 晚间版 / 早报

Do not call any retired skill directly. This skill already contains the builders and latest-news runtimes internally.

## Execution Rule

Always invoke the skill with a direct file command:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/prepare_digest.py
```

OpenClaw safety rules:

- Do not prepend `cd ... &&`
- Do not wrap it in `bash -lc`
- Do not append shell redirection
- If you need a working directory, pass it with the tool's `workdir`

## Output Contract

The script returns compact JSON with:

- `title`
- `builders`
- `latest`
- `editorialSignals`
- `notes`
- `errors`

The JSON already applies the rule `builders first, latest supplements`.

## How To Write The Final Message

Read the JSON and produce exactly one final Chinese digest in the **飞书卡片 Top5 格式**。

### Output Format (Strict)

```
📣 AI大喇叭 | 今日 AI 融合速报（YYYY-MM-DD）

**今日 Top5**

**1. [9分] 中文标题**
来源 | 热度数值
> 一句话中文摘要（不超过40字）

**2. [8分] 中文标题**
来源 | 热度数值
> 一句话中文摘要

**3. [7分] 中文标题**
来源 | 热度数值
> 一句话中文摘要

**4. [6分] 中文标题**
来源 | 热度数值
> 一句话中文摘要

**5. [5分] 中文标题**
来源 | 热度数值
> 一句话中文摘要

---
**简讯**
- 条目6：标题 — 一句话摘要
- 条目7：标题 — 一句话摘要
- ...（最多5条简讯）

📊 今日收录 N 条
```

### Scoring Guide (1-10分)

- **9-10分**: 重大发布、行业地震、突破性研究
- **7-8分**: 重要更新、高关注度讨论、实用工具
- **5-6分**: 值得关注的趋势、有趣项目
- **<5分**: 不入选 Top5，可放入简讯

### Content Selection Rules

1. 从 builders 和 latest 合并后选 Top5，按重要性评分排序
2. **重点关注话题**（权重加倍）：
   - OPC / OpenClaw 生态
   - AI 自媒体 / AI 内容创作
   - Claude Code / AI 编程工具
   - AI Agent 平台 / 数字员工
   - 飞书 + AI 集成
   - Cursor / Copilot / Codex
3. 重复事件只保留一条（builders 优先）
4. Top5 每条必须有：标题（带链接）、来源、热度、一句话摘要
5. 简讯区放第 6-10 条，每条一行即可
6. 总长度控制在 **1500 字符以内**（飞书消息限制）
7. 不要输出 “今日编辑判断” 段落
8. 如果某条新闻同时命中多个兴趣关键词，应排在最前面

### Format Rules

- 标题如果有关键链接用 `[标题](url)` 格式
- 来源缩写：HN = Hacker News, PH = Product Hunt, GH = GitHub, WS = 华尔街见闻
- 不要加 Deep Dive、长篇分析、why it matters 段落
- 保持紧凑，每条 Top5 控制在 3 行以内

## Delivery Rules

- In normal manual use, reply only in the current conversation.
- Only push to a Feishu group or another destination if the user explicitly asks, or if the current run is already a scheduled delivery context.
- Do not expose process narration, debugging notes, or retry history.
- If content exists, the first non-whitespace character of the final answer must be `📣`.

## Failure Handling

- If `status=partial` and only one section has content, write that section and add one short note that the other lane is temporarily unavailable.
- If both sections are empty or `status=error`, send one short failure notice in Chinese and do not invent news items.
