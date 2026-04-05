# 内容流水线：中间产物与命名约定

本文档与 [content-skills-implementation-plan.md](./content-skills-implementation-plan.md) 阶段 0 配套。请按你的实际目录修改路径，**全库只保留一处「当前真相」**（避免 `draft-v3-final-真的最终.md` 满天飞）。

**Skill 之间传什么信号**（路径 / frontmatter / 飞书 record_id、典型链路表）：见 [skill-catalog.md#skill-handoff-signals](./skill-catalog.md#skill-handoff-signals)。

**路径约定**：下表中所有路径省略公共前缀 `content-production/`。例如 `inbox/*` 实际指 `content-production/inbox/*`。其余文档（`skill-catalog.md`、`content-skills-implementation-plan.md`）遵循相同约定。

## 1. 建议目录（可按需调整）

| 路径 | 用途 |
|------|------|
| `inbox/` | 采集原文、链接列表、原始导出、视频拆解报告 |
| `drafts/` | 创作中稿件（Markdown）、翻译稿 |
| `ready/` | 已定稿、已排版、封面图、待发布 |
| `published/` | 已对外发布归档 |
| `storyboards/` | 视频脚本、分镜列表 |
| `video-assets/` | 分镜图、TTS 音频、合成成片 |
| `knowledge/glossary.md` | 翻译术语表（供 `tiered-translate` 引用） |
| `knowledge/style/` | 写作风格规则、人改稿提炼的修改规律 |
| `knowledge/checklists/` | 图文发布前检查、视频脚本检查等质检清单 |
| `knowledge/methodology/` | 方法论文件（按主题分，不按来源分） |

## 2. 层间 handoff 命名示例

| 阶段 | 产物名（示例） | 说明 |
|------|----------------|------|
| 采集 | `inbox/YYYYMMDD-{slug}.md` | 含原始链接、摘录 |
| 转写 | `inbox/{slug}-transcript.md` | 音视频转写 |
| 翻译 | `drafts/{slug}-zh.md` | 外文译稿 |
| 创作 | `drafts/{slug}-article.md` | Markdown 正文 |
| 排版 | `ready/{slug}-wechat.html` | 可粘贴微信后台 |
| 文章配图 | `ready/{slug}-img-*.png` | `generate-image` 输出 |
| 封面 | `ready/{slug}-cover-*.png` | 各封面 Skill 输出 |
| 飞书行 | 表字段见 `docs/feishu-schema.md`（**待建**，阶段 3 新增） | 与 `source_url` 去重 |
| 视频脚本 | `storyboards/{slug}-script.md` | `viral-video-script` 输出 |
| 分镜图 | `video-assets/{slug}-frames/*.png` | `generate-image` 分镜输出 |
| TTS 音频 | `video-assets/{slug}-voice.wav` | `minimax-tts` 输出 |
| 成片 | `video-assets/{slug}-final.mp4` | `video-from-storyboard` 合成结果 |

## 3. 版本与覆盖规则

- 同一 slug **升级版本**用 `{slug}-article-v2.md` 或 Git，避免同目录多份「最终」。
- 若某创作 Skill **已直接输出 HTML**，在 `CLAUDE.md` 写明是否仍走 `wechat-formatter`，避免二次嵌套。

---

*首次填写后，把实际路径同步到 `CLAUDE.md` 的项目索引。*
