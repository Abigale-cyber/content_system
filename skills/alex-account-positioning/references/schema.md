# Alex Account Positioning Schema

Use a Markdown request with YAML-style frontmatter.

## Minimal Request

```markdown
---
account_name: Alex AI Self-Media
topic_domain: AI content workflows
target_audience: AI content creators
---

## Creator Background
- I understand AI tools and content production.

## Audience Pains
- They know AI matters but cannot turn it into stable content output.

## Audience Goals
- They want repeatable content systems, not just isolated prompts.
```

## Supported Frontmatter Fields

| Field | Notes |
| --- | --- |
| `account_name` | working account name |
| `topic_domain` | domain focus |
| `target_audience` | optional explicit audience |
| `notes` | optional context |

## Recommended Sections

- `## Creator Background`
- `## Audience Pains`
- `## Audience Goals`
- `## Proof Assets`
- `## Business Goal`
- `## Constraints`
- `## Benchmark Notes`

## Output Contract

The skill writes:

- `content-production/positioning/<slug>-positioning-report.md`
- `content-production/positioning/<slug>-positioning-pack.json`
