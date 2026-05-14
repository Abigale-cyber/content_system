# 阶段 1 执行手册

适用目标：稳定跑通当前唯一主链路

`观点 brief` -> `case-writer-hybrid` -> `generate-image` -> `wechat-formatter`

当前有两个常用入口：

1. 你已经有结构化 brief：
   直接跑 `stage1-pipeline`
2. 你只有题目草稿或选题说明：
   直接跑 `topic-to-wechat-pipeline`

## 1. 本阶段要完成什么

阶段 1 不是追求一次写出完美文章，而是先验证这条链路可以重复跑通，并且每次都能留下标准产物。

本阶段最低交付：

1. 一份结构化输入 brief
2. 一份 Markdown 成稿
3. 至少一张配图或信息图
4. 一份微信公众号 HTML
5. 一份发布前检查记录

## 2. 执行顺序

### 步骤 1：准备输入 brief

使用 `docs/stage1-sample-brief-ai-content-system.md` 或 `docs/stage1-brief-template.md`。

要求：

- 观点必须明确
- 目标读者必须明确
- 至少给出 3 条论证方向
- 最好提供 2 到 3 个案例线索

如果还没有结构化 brief，可以先运行：

```bash
.venv/bin/python -m skill_runtime.cli run-skill content-brief-builder \
  --input notes/my-topic.md
```

如果你想从题目草稿一口气跑到微信 HTML，可以直接运行：

```bash
.venv/bin/python -m skill_runtime.cli run-workflow topic-to-wechat-pipeline \
  --input notes/my-topic.md
```

## 步骤 2：执行 `case-writer-hybrid`

输入：

- 一份观点 brief

目标输出：

- `content-production/drafts/{slug}-article.md`

要求：

- 输出必须是 Markdown，不直接产出 HTML
- 文章结构至少包含：问题、观点、案例、结论
- 若有三路径竞写或评分对比，可保留到附录或备注中，但最终要落一份主稿

对应说明：

- `docs/case-writer-hybrid-execution-spec.md`

## 步骤 3：执行 `generate-image`

输入：

- 文章主标题
- 文章核心观点
- 文章中的 1 到 3 个关键论点

目标输出：

- `content-production/ready/{slug}-img-1.png`
- 可选更多：`content-production/ready/{slug}-img-2.png`

要求：

- 优先生成信息图或公众号插图
- 视觉必须服务正文，不做无关装饰图

对应说明：

- `docs/generate-image-execution-spec.md`

## 步骤 4：执行 `wechat-formatter`

输入：

- `content-production/drafts/{slug}-article.md`

目标输出：

- `content-production/ready/{slug}-wechat.html`

要求：

- 只对 Markdown 做一次排版
- 若上游已经输出 HTML，需要先确认是否跳过本步

对应说明：

- `docs/wechat-formatter-execution-spec.md`

## 步骤 5：执行发布前检查

使用：

- `docs/article-prepublish-checklist.md`

要求：

- 至少检查正文、配图、排版、风险、落盘 5 个维度
- 把本次运行中暴露出来的问题写回 `docs/CLAUDE.md` 或检查清单

## 3. 一次完整运行后的文件形态

至少应能看到：

- 输入 brief：建议保存在 `content-production/inbox/`
- Markdown 成稿：`content-production/drafts/{slug}-article.md`
- 配图：`content-production/ready/{slug}-img-*.png`
- 微信 HTML：`content-production/ready/{slug}-wechat.html`

## 4. 本阶段最常见错误

| 错误 | 典型表现 | 处理方式 |
|------|----------|----------|
| brief 太空 | 只有标题，没有观点 | 先补观点、读者、目标再执行 |
| 成稿不是 Markdown | 直接生成 HTML | 固定要求主稿只输出 Markdown |
| 配图和正文脱节 | 图片好看但不服务正文 | 让图片围绕论点或结构生成 |
| 排版重复 | HTML 再进 formatter | 明确只对 Markdown 排版一次 |
| 没有复盘记录 | 下次还会重复踩坑 | 用检查清单记录问题并回写规则 |

## 5. 本阶段完成标准

满足以下 3 条，即认为阶段 1 初步可执行：

- 同一条链路至少跑通 1 次
- 产物都按约定路径落盘
- 新开一个会话，仅看 `docs/` 也知道该怎么继续跑

## 6. 推荐命令

只有题目草稿时：

```bash
.venv/bin/python -m skill_runtime.cli run-workflow topic-to-wechat-pipeline \
  --input notes/my-topic.md
```

已有结构化 brief 时：

```bash
.venv/bin/python -m skill_runtime.cli run-workflow stage1-pipeline \
  --input content-production/inbox/YYYYMMDD-<slug>-gzh-brief.md
```
