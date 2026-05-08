---
name: topic-radar
description: Use when a topic, hotspot, rough note, news scan, or trend needs to be turned into scored article angles before building a content brief.
---

# Topic Radar

Convert a raw topic or hotspot note into candidate writing angles. This skill is an upstream decision layer before `content-brief-builder`.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill topic-radar --input notes/<topic>.md
```

## Output

```text
content-production/topics/<slug>-topic-radar.md
content-production/topics/<slug>-topic-radar.json
```

## What To Check

- 四维打分：热爱程度、专业能力、市场需求、资源积累
- 三类选题公式：痛点+工具+具体结果、误解+反转+证明、低效动作+AI替代+效果对比
- 推荐结构：观点类、热点类、教学类、对比式、故事类
- 素材缺口：提醒哪里还缺案例、数据或来源

## Handoff

Pick the recommended angle, then feed the report or selected angle into `content-brief-builder`.
