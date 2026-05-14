# 养虾转养马第一步：把 Hermes Agent 装起来

有句话我最近越听越想笑：

“OpenClaw 是养虾，Hermes Agent 是养马。”

这个梗很有传播感，也确实好玩。但问题是，很多人现在连马厩门都没打开，就已经开始讨论马术比赛了。

有人问：Hermes 能不能接微信？能不能定时写公众号？能不能像 Claude Code 一样改代码？能不能帮我做自动化工作流？能不能把 OpenClaw 替掉？

这些问题当然都能聊，但我想先泼一盆冷水：**如果你还没有亲手把 Hermes 在自己的电脑上跑起来，那这些问题基本都属于“云养马”。**

看别人截图很爽，看测评文章也很爽，但 Agent 这东西和普通 App 不一样。它不是你注册个账号、打开网页，就算开始用了。Hermes 真正的价值，是它能接进你的电脑环境，能读文件、跑命令、调用工具、保存技能，最后变成一个真的能帮你干活的本地 Agent。

所以这篇文章不做宏大叙事，不争 OpenClaw 和 Hermes 谁更强，也不讲一堆你第一天根本用不上的高级功能。

今天只解决一件事：

> **把 Hermes Agent 装起来，并且确认它真的跑通。**

只要这一步完成，后面你再研究微信接入、Skills、自定义人格、定时任务、自动写文章，都会顺很多。反过来，如果第一步没跑通，后面所有折腾都会变成玄学排错。

---

## 先记住一句话：第一天只跑通最小闭环

很多人第一次装 Agent，最容易犯的错误就是贪心。

刚看到 Hermes 支持 Gateway、Skills、Cron、浏览器、文件工具、消息平台，一激动全都想开。结果装到一半，模型报错；好不容易模型能回话，工具又不能用；工具刚开起来，微信 Gateway 又连不上。最后你根本分不清到底是哪一层坏了。

我的建议很简单：**第一天别追求全能，只跑通最小闭环。**

这个最小闭环只有 4 步：

1. 安装 Hermes；
2. 配好模型；
3. 启动 Hermes；
4. 让它读一次你当前目录，再跑一次体检。

如果这 4 步完成了，你就不是“装了一个聊天机器人”，而是真的让一个本地 Agent 活起来了。

最快命令长这样：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes model
hermes
```

如果你用的是 zsh，把第二行换成：

```bash
source ~/.zshrc
```

这几行看起来很短，但它背后完成的是一条完整链路：安装程序、刷新命令、配置模型、启动 Agent。你第一天先别管花活，就把这条链路跑通。

---

## 安装前，你真正需要准备什么？

别被“Agent 框架”“工具调用”“上下文窗口”这些词吓住。新手第一天只需要准备三样东西。

**第一，一台适合折腾命令行的电脑。**

macOS 和 Linux 会比较顺。如果你是 Windows 用户，我建议优先用 WSL2，也就是 Windows 里的 Linux 环境。不是说 PowerShell 不能装，而是对小白来说，第一天没必要把时间花在 Windows 原生环境的奇怪小坑上。

**第二，一个终端。**

macOS 打开“终端”或者 iTerm；Linux / WSL2 打开系统终端；Windows 如果走 WSL2，就打开 Ubuntu 终端。你不需要一开始就懂所有命令，只要能复制、粘贴、执行就够了。

**第三，一个能用的大模型 API Key。**

这一点很多人会搞错：Hermes 不是自带大模型的 App。你可以把它理解成“会干活的身体”，但它需要接一个大模型当大脑。

后面运行 `hermes model` 的时候，你会选择模型服务商，比如 OpenRouter、Anthropic、OpenAI、Gemini、DeepSeek、Kimi、Qwen、MiniMax，或者你自己的 OpenAI-compatible 接口。

这里不用第一天就追求最强模型。我的建议是：**先选一个你能稳定调用的模型。**

Agent 很吃上下文，因为它要看历史对话、工具返回、文件内容和任务步骤。Hermes 官方建议模型上下文至少 64K tokens。你现在不需要理解 tokens 的所有细节，只要知道一件事：上下文太短，Agent 很容易干着干着就忘了前面发生什么。

如果你的电脑没有 Git，可以先检查一下：

```bash
git --version
```

能看到版本号就行。如果提示找不到 git，macOS 可以运行：

```bash
xcode-select --install
```

Ubuntu / WSL2 可以运行：

```bash
sudo apt update
sudo apt install git -y
```

---

## 第一步：安装 Hermes，别被英文输出吓退

macOS / Linux / WSL2 用户，直接复制这一行：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

然后等它跑完。

这个过程会刷出不少英文输出。新手看到这里很容易紧张，感觉是不是哪里报错了。其实大多数时候，只要终端没有明确停下来提示失败，就让它继续跑。

这条安装命令会帮你准备运行 Hermes 需要的东西，比如 Python、Node.js、uv、ripgrep、ffmpeg，也会下载 Hermes Agent 代码，创建运行环境，并把 `hermes` 命令放到系统路径里。

你不需要第一天理解每个依赖是干什么的。先跑起来，后面再慢慢拆。

安装完成后，重新加载终端配置：

```bash
source ~/.bashrc
```

如果你用 zsh，就运行：

```bash
source ~/.zshrc
```

然后检查命令是否生效：

```bash
hermes --version
```

如果能看到版本号，说明 Hermes 已经被你的系统认识了。

如果出现 `command not found: hermes`，先别急着重装。这个问题很常见，通常不是安装失败，而是终端还没刷新环境变量。最简单的办法是：关掉当前终端，重新开一个，再运行一次：

```bash
hermes --version
```

很多时候，就这么简单。

---

## Windows 用户：第一天别硬刚 PowerShell

如果你是 Windows 用户，我建议你把这句话记下来：

> **能用 WSL2，就先用 WSL2。**

WSL2 可以理解成 Windows 里的 Linux 环境。很多 AI 开发工具在 Linux 下更稳定，教程也更多。你后面要装依赖、跑命令、排查问题，WSL2 通常会少很多没必要的折磨。

在 WSL2 的 Ubuntu 终端里，仍然是同一条命令：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

如果你坚持 Windows 原生安装，也可以在 PowerShell 里运行：

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

但我真心不建议纯小白第一天就从 PowerShell 开始。你今天的目标不是证明 Windows 原生环境能不能搞定，而是先让 Hermes 跑起来。

**效率比姿势重要。**

---

## 第二步：配置模型，这一步是在给 Hermes 装“大脑”

安装好以后，运行：

```bash
hermes model
```

它会进入一个交互式选择流程。你按照提示选择模型服务商，填入 API Key，再选择具体模型。

这里最容易翻车的地方有两个。

第一个，是把 Hermes 当成自带模型的软件。不是。Hermes 是 Agent 框架，它需要接入模型服务。没有模型，它就没有“大脑”。

第二个，是 API Key、Base URL、Model Name 随便填。尤其是自定义接口，Base URL 多一个斜杠、模型名拼错、Key 少复制一位，都可能导致后面一直报错。

如果你配置完以后 Hermes 报错，不要慌，也不要马上去配置文件里乱改。先重新跑一遍：

```bash
hermes model
```

重新选择服务商，重新填 Key，重新选模型。这比你凭记忆手动改配置稳得多。

如果你用的是 OpenAI-compatible 自定义接口，重点检查四件事：

- Base URL 是否正确；
- API Key 是否完整；
- Model Name 是否和服务商后台一致；
- 这个接口是否真的兼容 OpenAI 格式。

第一天别搞太复杂的模型路由、多 Key 轮换、多供应商切换。那些以后再玩。

先用一个稳定模型把主流程跑通。

---

## 第三步：启动 Hermes，但别只测“你好”

模型配置好以后，直接运行：

```bash
hermes
```

进入 Hermes 后，你当然可以先问一句：

```text
你好，简单介绍一下你能帮我做什么。
```

如果它能正常回复，说明模型调用基本没问题。

但注意，这还不算真正跑通。

因为“能聊天”只能证明模型能回话，不能证明 Hermes 已经具备本地 Agent 的能力。真正要测的是：它能不能调用工具，能不能理解你当前电脑环境。

所以你再发一句：

```text
请检查我当前目录下有哪些文件，并告诉我这个目录大概是做什么的。
```

如果 Hermes 能列出文件，并根据文件结构判断这是一个什么项目，那感觉就完全不一样了。

这时候你会第一次意识到：它不是一个隔着网页的聊天机器人，而是真的坐进了你的工作环境里。它能看上下文，能调用工具，能基于你的文件做判断。

这一步，才是 Hermes 和普通聊天框拉开差距的地方。

---

## 第四步：跑一次体检，别靠感觉排错

安装完成后，我建议你立刻跑一次：

```bash
hermes doctor
```

你可以把它理解成 Hermes 的体检报告。它会帮你检查依赖、配置、模型、工具等状态。

小白排查问题时最容易靠猜。模型报错了，猜是 Key 问题；工具不能用，猜是权限问题；命令找不到，猜是安装失败。猜来猜去，半天过去了，问题还在原地。

`hermes doctor` 的价值，就是把问题尽量摊开给你看。

以后只要你感觉 Hermes “怪怪的”，第一反应都应该是：

```bash
hermes doctor
```

不是立刻重装，也不是立刻改配置。

先体检。

---

## 你只需要先记住这 7 个命令

刚开始不用记太多。下面这 7 个命令，已经够你用一阵子了。

| 命令 | 用来干什么 |
|---|---|
| `hermes` | 启动 Hermes，进入聊天 |
| `hermes model` | 选择或切换模型 |
| `hermes doctor` | 检查环境和配置 |
| `hermes setup` | 运行完整配置向导 |
| `hermes tools` | 开关工具能力 |
| `hermes --continue` | 继续上一次会话 |
| `hermes update` | 更新 Hermes |

如果你只愿意记三个，那就记这三个：

```bash
hermes
hermes model
hermes doctor
```

一个启动，一个配模型，一个查问题。

足够你完成第一天的入门。

---

## 最容易翻车的 5 个坑

**第一个坑：`hermes: command not found`。**

这通常不是安装失败，而是终端路径没刷新。先运行 `source ~/.bashrc`，如果你用 zsh，就运行 `source ~/.zshrc`。还不行，就关掉终端重新打开。

**第二个坑：模型配置完还是报错。**

优先怀疑 API Key、模型名、服务商配置。不要凭感觉乱改，直接重新运行 `hermes model`，重新走一遍配置流程。

**第三个坑：能聊天，但不能读文件、不能执行任务。**

这时要检查工具有没有启用：

```bash
hermes tools
```

Hermes 的强项是工具调用。如果工具没开，它就会退化成一个比较普通的聊天助手。

**第四个坑：第一天就急着接微信。**

接微信、Telegram、Discord、Slack 这类消息平台，本质上是在已经能工作的 Hermes 外面，再套一层 Gateway。如果 CLI 还没跑通，你直接折腾 Gateway，出问题时根本分不清是模型、工具、终端还是消息平台坏了。

所以顺序一定是：**先 CLI，后 Gateway。**

**第五个坑：装完以后不知道问什么。**

不要只问“你好”。你可以直接这样测：

```text
请检查当前目录，告诉我这里是什么项目。
```

```text
请帮我总结这个文件夹的主要结构。
```

```text
请帮我把今天的工作计划整理成 markdown 文件。
```

```text
请联网搜索 Hermes Agent 的官方文档，总结它最适合哪些使用场景。
```

这些问题比“你好”更能测出 Agent 的真实能力。

---

## 跑通以后，再玩这些高级功能

当你已经能正常运行 `hermes`，并且确认它能读文件、能调用工具后，就可以开始玩更有意思的东西了。

第一，可以打开更多工具：

```bash
hermes tools
```

小白一开始不要全开。建议先从 terminal、file、web、browser 这些基础能力开始。够用了，再逐步加 vision、image_gen、cronjob 等能力。

第二，可以定制它的人格。

Hermes 支持用 `SOUL.md` 定义默认身份和说话风格。默认位置是：

```text
~/.hermes/SOUL.md
```

比如你希望它每次都以“Angela，一个耐心、清醒、有人味的协作助手”的身份出现，就可以把这种设定写进去。这样它以后启动时，就不会每次都像一个陌生机器人。

第三，可以开始用 Skills。

Skills 可以理解成 Hermes 的经验包。你经常写公众号文章，就可以有公众号写作流程；你经常排查代码问题，就可以有调试流程；你经常做研究，就可以有资料搜集和整理流程。

你可以先看看有哪些技能：

```bash
hermes skills list
```

或者搜索某类技能：

```bash
hermes skills search 关键词
```

第四，再考虑接入消息平台：

```bash
hermes gateway setup
```

但我还是那句话：**先 CLI 跑通，再接 Gateway。**

不要一上来就把所有功能堆在一起。功能越多，出问题时越难判断是哪一层出了问题。

---

## 最短复制版

如果你只想复制命令，看这里。

### macOS / Linux / WSL2

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes model
hermes
```

如果你用 zsh：

```bash
source ~/.zshrc
```

### Windows PowerShell 原生安装

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

然后重新打开 PowerShell，再运行：

```powershell
hermes model
hermes
```

### 出问题先体检

```bash
hermes doctor
```

---

## 最后说句实话

Agent 这个东西，最容易让人产生幻觉。

看别人截图，感觉自己已经懂了；看几篇测评，感觉自己已经会选型了；听别人说“养虾”“养马”，感觉自己已经入圈了。

但真正的分水岭很朴素：

> **你有没有亲手把它跑起来。**

只要 Hermes 在你的电脑上真正跑通一次，你对 Agent 的理解就会立刻变得具体。你会知道模型为什么重要，工具为什么重要，配置为什么重要，Skills 为什么不是花活，Gateway 为什么应该放到后面。

所以别再云养马了。

今天先做一件事：打开终端，把第一条命令跑起来。

等它真的回复你、真的能看文件、真的能帮你处理任务时，你再回头看那些争论，会发现很多问题根本不用吵。

因为 Agent 时代，真正拉开差距的不是谁会说概念，而是谁先让自己的 Agent 开始干活。