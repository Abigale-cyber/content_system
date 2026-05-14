# Routing Matrix

## Upstream First

Always route to the earliest missing step.

| User need | Primary skill | Typical downstream |
| --- | --- | --- |
| unclear account direction | `alex-account-positioning` | `alex-benchmark-research` -> `alex-title-lab` |
| wants benchmark teardown | `alex-benchmark-research` | `alex-title-lab` -> `topic-radar` |
| wants title help | `alex-title-lab` | `topic-radar` -> `content-brief-builder` |
| wants topic judgment | `topic-radar` | `content-brief-builder` |
| wants structured brief | `content-brief-builder` | `case-writer-hybrid` |
| wants article draft | `case-writer-hybrid` | `adversarial-content-review` |
| wants review | `adversarial-content-review` | `script-writer-short` / `wechat-formatter` |
| wants short video script | `script-writer-short` | optional formatting/publishing |
| wants WeChat formatting | `wechat-formatter` | `wechat-draft-publisher` |
| wants publish | `wechat-draft-publisher` | end of chain |
