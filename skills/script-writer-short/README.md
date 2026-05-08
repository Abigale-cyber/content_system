# script-writer-short

`script-writer-short` 是短视频口播脚本 skill。它把公众号长文、brief 或选题稿压缩成适合 60-180 秒短视频的口播脚本。

## 这个 skill 能做什么

- 把文章判断压缩成短视频表达
- 输出 Hook / Introduction / Body / Summary / 拍摄提示
- 默认生成 90 秒口播稿
- 生成 Markdown 脚本和 JSON sidecar，便于后续 TTS 或视频制作

## 输入和输出

**输入**

- `content-production/drafts/<slug>-article.md`
- 或 brief / 选题 Markdown

**输出**

- `content-production/drafts/<slug>-script.md`
- `content-production/drafts/<slug>-script.json`

## 使用方法

### 单独运行

```bash
.venv/bin/python -m skill_runtime.cli run-skill script-writer-short \
  --input content-production/drafts/ai-content-system-article.md
```

### 常见下游衔接

- 下游可接 TTS、视频制作或人工拍摄
- 常用 workflow：`article-to-short-script-pipeline`

## 什么时候用

- 主稿已经稳定，想顺手复用成视频号 / 短视频口播稿
- 你需要一个适合读出来的视频脚本，而不是继续写长文
- 你想先验证一篇文章能不能转成更口语、更短的视频版本

## 注意事项

- 它不是长文写稿器
- 建议在主稿和审稿稳定之后再用
- 它会尽量保留主观点，但不会替你补事实或查资料

## 相关文件

- [SKILL.md](./SKILL.md)
- [runtime.py](./runtime.py)
- [skill-workflow-guide.md](../../docs/skill-workflow-guide.md)
