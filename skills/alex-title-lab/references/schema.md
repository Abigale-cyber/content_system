# Alex Title Lab Schema

Use a Markdown request with YAML-style frontmatter.

## Minimal Request

```markdown
---
topic: AI workflow writing
reader_profile: AI content creators
pain_point: the content is useful but the title still feels flat
core_view: Most people do not need more prompts. They need reusable task templates.
sample_file: example-titles.csv
---

Analyze these sample titles and generate Alex-ready variants.
```

## Supported Frontmatter Fields

| Field | Notes |
| --- | --- |
| `topic` | the main topic or packaging direction |
| `reader_profile` | who the title is for |
| `pain_point` | what the reader struggles with |
| `core_view` | the core argument behind the title |
| `sample_file` | relative CSV or Markdown table |
| `account_name` | optional benchmark label |
| `notes` | optional extra context |

## Preferred Sample Fields

| Field | Meaning |
| --- | --- |
| `title` | sample headline |
| `summary` | optional content summary |
| `topic_cluster` | optional cluster |
| `platform` | optional source platform |
| `engagement_signal` | optional likes/comments/saves/views or normalized score |

## Output Contract

The skill writes:

- `content-production/titles/<slug>-title-report.md`
- `content-production/titles/<slug>-title-pack.json`
