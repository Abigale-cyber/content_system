# Alex Benchmark Research Schema

Use a Markdown request with YAML-style frontmatter.

## Minimal Request

```markdown
---
platform: xiaohongshu
account_name: Example Creator
analysis_window_days: 90
sample_size: 12
focus:
  - account structure
  - recurring columns
  - narrative patterns
  - topic density
sample_file: references/example-samples.csv
---

Please analyze this account and tell Alex what to borrow, adapt, and avoid.
```

## Supported Frontmatter Fields

| Field | Notes |
| --- | --- |
| `platform` | `xiaohongshu`, `wechat`, `douyin`, `video-account`, `mixed` |
| `account_name` | human-readable benchmark label |
| `analysis_window_days` | default `90` |
| `sample_size` | optional expected sample count |
| `focus` | list of priorities |
| `sample_file` | relative CSV or Markdown file |
| `seed_urls` | optional URL list for manual follow-up |
| `notes` | optional extra context |

## Preferred Sample Fields

| Field | Meaning |
| --- | --- |
| `title` | title |
| `publish_date` | publish date |
| `url` | source URL |
| `platform` | source platform |
| `content_summary` | summary |
| `topic_cluster` | normalized topic cluster |
| `hook_type` | opening hook |
| `narrative_pattern` | structure pattern |
| `format_type` | tutorial, commentary, case study, listicle, etc. |
| `audience` | who it is for |
| `pain_point` | what problem it targets |
| `proof_type` | proof style |
| `cta_type` | CTA pattern |
| `engagement_signal` | likes/comments/saves/views or normalized score |

## Output Contract

The skill writes:

- `content-production/benchmarks/<slug>-benchmark-report.md`
- `content-production/benchmarks/<slug>-benchmark-pack.json`
