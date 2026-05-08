# adversarial-content-review

`adversarial-content-review` 是独立审稿 skill。它不负责写稿，只负责判断一篇 Markdown 主稿能不能继续进入发布包装。

## 这个 skill 能做什么

- 读取一篇已完成的 Markdown 主稿
- 分三轮审稿：笔杆子审、参谋审、裁判裁定
- 输出五维度评分
- 给出 `通过 / 需修改 / 需重写` 结论
- 生成 Markdown 审稿报告和 JSON sidecar
- 如果结论不过线，可以作为 workflow 的阻塞门控

## 输入和输出

**输入**

- `content-production/drafts/<slug>-article.md`

**输出**

- `content-production/reviews/<slug>-review-report.md`
- `content-production/reviews/<slug>-review-report.json`

## 使用方法

### 单独运行

```bash
.venv/bin/python -m skill_runtime.cli run-skill adversarial-content-review \
  --input content-production/drafts/ai-content-system-article.md
```

## 什么时候用

- 主稿已经写完，想判断能不能继续配图和排版
- 你想把“修改意见”结构化记录下来
- 你想在发布前增加一道独立质量门控

## 注意事项

- 它不直接改文章
- 如果结论是 `需修改` 或 `需重写`，应先回到主稿修改
- 它适合放在 `case-writer-hybrid` 后、`generate-image` / `wechat-formatter` 前

## 相关文件

- [SKILL.md](./SKILL.md)
- [runtime.py](./runtime.py)
- [skill-workflow-guide.md](../../docs/skill-workflow-guide.md)
