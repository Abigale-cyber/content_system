# Feishu Top 5 Briefing Instructions

> INPUT: JSON from `daily_briefing.py --profile general` (sections: `global_scan`, `hn_ai`, `github_trending`)
> OUTPUT: A compact Markdown string formatted for Feishu post message

## Task

From all input data, select the **top 5 most impactful** items. Rank by a combination of: heat/score, AI relevance, and potential impact on Chinese developers. Score each item 1-10.

## Output Format

Produce **exactly** this Markdown structure:

```
**每日热点 Top5 | YYYY-MM-DD**

**1. [N分] 中文标题**
来源 | 热度数值
> 一句话中文摘要（不超过40字）

**2. [N分] 中文标题**
来源 | 热度数值
> 一句话中文摘要

...（共5条）

📊 今日收录 N 条
```

## Scoring Guide

- 9-10: 重大发布、行业地震、突破性研究
- 7-8: 重要更新、高关注度讨论、实用工具
- 5-6: 值得关注的趋势、有趣的项目
- <5: 不入选 Top5

## Rules

1. **总长度控制在 800-1500 字符**（飞书消息限制）
2. **不要** Deep Dive 分析，每条只有一句话摘要
3. 保留知名英文专有名词（ChatGPT、Claude、GitHub 等）
4. 来源用中文（Hacker News → HN，微博热搜 → 微博）
5. 不要输出任何 JSON，只输出纯 Markdown 文本
6. 如果某条有重要链接，附在来源行：`来源 | 热度 | [讨论](url)`
