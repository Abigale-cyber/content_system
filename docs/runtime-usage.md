# Skill Runtime 使用说明

当前项目已提供一个本地 Python 版 skill runtime，用于把阶段 1 的三个核心技能变成可调用程序。

同时，项目还保留了一个可选工作台：

- **`wechat-studio`**
- 中文名称：**微信包装工作台**
- 当前实现目录：`skills/wechat-studio/`

这个工作台负责公众号包装预览、封面/正文配图管理与后续草稿推送能力。
它位于执行器之上：调用 `generate-image` / `wechat-formatter`，保存视觉状态，并承接人工确认。

## 当前可调用的 Skills

- `case-writer-hybrid`
- `generate-image`
- `wechat-formatter`

> 当前 runtime 中真正参与主链路的是 `generate-image` / `wechat-formatter` 两个原子 skill；`wechat-studio` 是位于它们之上的人工操作台，而不是主链路节点。

关系可以理解成：

- `generate-image`：负责真正产出图片文件
- `wechat-formatter`：负责真正产出微信 HTML
- `wechat-studio`：调用这两个执行器，保存视觉状态，并在你需要人工预览、调色、调版式、挑图或推草稿时介入

## 当前可调用的 Workflow

- `stage1-pipeline`

## 1. 安装依赖

在项目根目录执行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. 查看可用 Skills

```bash
.venv/bin/python -m skill_runtime.cli list-skills
```

## 3. 查看可用 Workflows

```bash
.venv/bin/python -m skill_runtime.cli list-workflows
```

## 4. 单独运行某个 Skill

### 生成 Markdown 主稿

```bash
.venv/bin/python -m skill_runtime.cli run-skill case-writer-hybrid \
  --input content-production/inbox/20260403-ai-content-system-brief.md
```

### 生成 PNG 配图

```bash
.venv/bin/python -m skill_runtime.cli run-skill generate-image \
  --input content-production/drafts/ai-content-system-article.md
```

### 生成微信 HTML

```bash
.venv/bin/python -m skill_runtime.cli run-skill wechat-formatter \
  --input content-production/drafts/ai-content-system-article.md
```

> 以上两个执行器默认直接产出文件，不会自动写回 `wechat-studio`。如需人工包装、风格调节和草稿推送，再进入 `wechat-studio` 工作台。

## 5. 一次运行完整工作流

```bash
.venv/bin/python -m skill_runtime.cli run-workflow stage1-pipeline \
  --input content-production/inbox/20260403-ai-content-system-brief.md
```

## 6. 输出位置

运行完整 workflow 后，默认会生成：

- `content-production/drafts/ai-content-system-article.md`
- `content-production/ready/ai-content-system-img-1.png`
- `content-production/ready/ai-content-system-wechat.html`
- `content-production/published/stage1-pipeline-last-run.json`

## 7. 当前版本能力边界

这是第一版本地 runtime，目标是先把 skill 变成可调用节点，而不是一开始就接全量模型与平台 API。

当前实现方式：

- `case-writer-hybrid`：基于 brief 生成结构化 Markdown 主稿
- `generate-image`：作为独立执行器，基于文章生成一张信息图风格 PNG
- `wechat-formatter`：作为独立执行器，把 Markdown 转为简单、可读的微信 HTML
- `wechat-studio`：作为上层工作台，调用上述执行器并保存包装状态

后续可继续扩展：

- 接入真实 LLM API 替换主稿生成逻辑
- 接入真实文生图模型替换 PNG 渲染逻辑
- 让 `wechat-studio` 在不侵入主链路的前提下，进一步复用和编排 `generate-image` / `wechat-formatter`
- 接入阶段 2 的 `wechat-collect`
- 接入阶段 3 的飞书和小红书链路
