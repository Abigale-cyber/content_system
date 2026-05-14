---
name: alex-ai-self-media-coach
description: Use when Alex needs to decide which skill or workflow should handle a self-media task such as account positioning, benchmark analysis, title work, topic selection, brief building, drafting, review, repurposing, or publishing.
---

# Alex AI Self-Media Coach

This is the top-level Alex routing skill. It does not replace the specialist skills. It decides which one should act next.

## Default Command

```bash
.venv/bin/python -m skill_runtime.cli run-skill alex-ai-self-media-coach --input notes/<request>.md
```

## Output

```text
content-production/routes/<slug>-route-report.md
content-production/routes/<slug>-route-pack.json
```

## Scope

- Do interpret what stage of the content workflow the user is in
- Do recommend the next primary skill and optional downstream chain
- Do preserve Alex's voice and strategic logic
- Do not replace the underlying specialist skill execution
- Do not write the final article, title pack, or benchmark report itself unless explicitly routed downstream

## Routing Philosophy

Alex should prefer the narrowest skill that solves the current blocker.

Examples:

- "I don't know what kind of account to build" -> `alex-account-positioning`
- "拆一下这个博主/账号" -> `alex-benchmark-research`
- "这些标题为什么能火" -> `alex-title-lab`
- "这个热点到底值不值得写" -> `topic-radar`
- "先别写，先帮我整理 brief" -> `content-brief-builder`
- "直接写成文章" -> `case-writer-hybrid`
- "帮我审一遍再发" -> `adversarial-content-review`
- "改成短视频口播" -> `script-writer-short`
- "排版/发到公众号" -> `wechat-formatter` / `wechat-draft-publisher`

## Decision Order

1. Determine whether the user lacks strategy, benchmark context, packaging, topic judgment, structure, draft, review, or publishing support.
2. Route to the earliest missing step in the chain.
3. Prefer upstream correction over downstream patching.

That means:

- if positioning is unclear, do not jump to article writing
- if benchmark clarity is missing, do not jump to title polishing
- if topic clarity is missing, do not jump to brief writing

## Chain

The default Alex chain is:

`alex-account-positioning -> alex-benchmark-research -> alex-title-lab -> topic-radar -> content-brief-builder -> case-writer-hybrid -> adversarial-content-review -> script-writer-short / wechat-formatter / wechat-draft-publisher`

Not every request needs the whole chain. Route only to the next useful step.

## Timeliness Gate

As the router, Alex should mark:

- `Evergreen`
- `Verify-Now`
- `Legacy-2024`

Use [references/legacy-2024-notes.md](references/legacy-2024-notes.md) when a request depends on old course materials, platform mechanisms, or outdated tool stacks.

## Read Before Routing

- [references/routing-matrix.md](references/routing-matrix.md)
- [references/request-signals.md](references/request-signals.md)
