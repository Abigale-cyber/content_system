# 飞书多维表字段契约（公众号对比采集）

本文档定义 `wechat-report -> 用户确认 -> feishu-bitable-sync` 这条链路写入飞书时使用的字段名、授权模式与兜底策略。当前实现按 **一篇文章一行** 同步，使用 `source_url` 去重。

## 1. 推荐连接方式

当前默认方案：

1. 先运行 `wechat-report` 生成本地结构化对比报告
2. 用户阅读后明确确认“发送到飞书”
3. 首次同步前先运行 `feishu-user-auth`
4. 再运行 `feishu-bitable-sync`

默认同步模式是 **用户授权写入**，不再默认依赖 `tenant_access_token` 的应用身份直写。

## 2. 必备环境变量

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_BITABLE_APP_TOKEN`
- `FEISHU_BITABLE_TABLE_ID`

可选：

- `FEISHU_SYNC_AUTH_MODE`
  默认 `user`；兼容保留 `tenant`
- `FEISHU_OAUTH_REDIRECT_URI`
  默认 `http://127.0.0.1:14578/callback`
- `FEISHU_USER_AUTH_CACHE_PATH`
  默认 `~/.codex/feishu-auth/content-system-sync.json`
- `FEISHU_OPEN_BASE_URL`

## 3. 授权缓存

- `feishu-user-auth` 会把 `user_access_token + refresh_token` 缓存在：
  `~/.codex/feishu-auth/content-system-sync.json`
- 缓存文件不进入仓库，权限应为仅当前用户可读写。
- `feishu-bitable-sync` 会优先读取这份缓存；若 access token 过期，会尝试自动刷新。

## 4. 建议字段

| 字段名 | 推荐类型 | 说明 |
|------|----------|------|
| `topic` | 单行文本 | 本次主题，例如 `Harness Engineering` |
| `report_slug` | 单行文本 | 本地报告 slug |
| `source_url` | 单行文本 / URL | 原文链接；去重主键 |
| `公众号` | 单行文本 | 公众号名称 |
| `作者` | 单行文本 | 文章作者 |
| `标题` | 单行文本 | 文章标题 |
| `发布时间` | 单行文本 / 日期 | 原文发布时间 |
| `是否原创` | 单行文本 / 单选 | `是` / `否` |
| `摘要` | 多行文本 | 文章摘要 |
| `阅读数` | 数字 | 若公开页或浏览器会话未暴露则留空 |
| `点赞数` | 数字 | 同上 |
| `评论数` | 数字 | 同上 |
| `打赏数` | 数字 | 同上 |
| `comment_id` | 单行文本 | 微信评论 ID，常用于后续追踪 |
| `互动采集状态` | 单行文本 / 单选 | `visible_in_public_html` / `visible_in_browser_session` / `requires_logged_in_session` / `hidden_in_public_html` / `unavailable` |
| `正文纯文本长度` | 数字 | 正文纯文本字符数 |
| `段落数` | 数字 | 正文段落数 |
| `图片数` | 数字 | 正文图片数量 |
| `外链数` | 数字 | 正文外部链接数量 |
| `公众号内链数` | 数字 | 正文内引用的公众号文章链接数量 |
| `封面图` | 单行文本 / URL | 封面图 URL |
| `采集时间` | 单行文本 / 日期时间 | 本次同步或导出时间 |
| `同步状态` | 单行文本 / 单选 | `created` / `updated` / `csv_exported` |

## 5. 同步状态值

`wechat-report` raw JSON 的 `feishu_sync.status` 当前支持：

- `awaiting_user_confirmation`
- `auth_required`
- `synced`
- `csv_exported`
- `sync_failed`

说明：

- `awaiting_user_confirmation`
  本地报告已生成，但用户还没确认要不要发飞书
- `auth_required`
  还没有本机用户授权缓存，需先运行 `feishu-user-auth`
- `synced`
  已直接写入飞书多维表
- `csv_exported`
  直接写入失败，但已导出一份可导入飞书的 CSV
- `sync_failed`
  直接写入失败，且 CSV 兜底也失败

## 6. 输出与兜底

- 成功或失败都会写同步回执：
  `content-production/published/YYYYMMDD-{slug}-feishu-sync.md`
- 当 direct sync 失败且 CSV 兜底成功时，还会额外输出：
  `content-production/published/YYYYMMDD-{slug}-feishu-import.csv`
- 首次授权会写：
  `content-production/published/YYYYMMDD-feishu-user-auth.md`

## 7. 当前范围

- 首版只覆盖 `wechat-report` 产出的公众号对比数据。
- `feishu-bitable-sync` 不会自动运行。
- 只有用户先阅读 `wechat-report` 生成的本地报告，并明确确认“发送到飞书”，才运行同步。
- 不自动创建飞书字段；请先按上表建好字段，再运行同步。
