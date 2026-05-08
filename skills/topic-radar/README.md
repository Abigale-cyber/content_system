# topic-radar

`topic-radar` 是选题拆解 skill。它把热点、粗笔记或趋势说明转成多个可写切口，帮助你在正式写稿前先判断“这个题到底怎么写”。

## 这个 skill 能做什么

- 从一个热点或粗想法里拆出 3 个候选切口
- 输出四维打分：热爱程度、专业能力、市场需求、资源积累
- 给出推荐结构、标题方向和素材缺口
- 选出一个推荐角度，作为后续 `content-brief-builder` 的上游输入

## 输入和输出

**输入**

- `notes/*.md`
- 或任意包含热点、想法、素材说明的 Markdown

**输出**

- `content-production/topics/<slug>-topic-radar.md`
- `content-production/topics/<slug>-topic-radar.json`

## 使用方法

### 单独运行

```bash
.venv/bin/python -m skill_runtime.cli run-skill topic-radar \
  --input notes/my-hot-topic.md
```

### 常见下游衔接

- 下游 brief：`content-brief-builder`
- 常用 workflow：`topic-radar-to-brief-pipeline`

## 什么时候用

- 你知道最近有个热点，但还不知道具体该写哪个角度
- 你有粗笔记或素材清单，想先做选题判断
- 你想在写稿前先看清“值不值得写”

## 注意事项

- 它不直接写文章
- 它适合放在最前面，用来决定后面的 brief 和研究方向
- 如果素材缺口明显，建议先补资料再进入正式写稿

## 相关文件

- [SKILL.md](./SKILL.md)
- [runtime.py](./runtime.py)
- [skill-workflow-guide.md](../../docs/skill-workflow-guide.md)
