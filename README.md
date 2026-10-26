# AI 前沿追踪 · 持久归档

位置：`/workspace/ai-radar`（共享电脑上，所有 Agent 都能写）。

## 目录
- `INDEX.md`：总索引，按领域列出每天一份文件和条数（自动生成）
- `topics/<领域>/YYYY-MM-DD.md`：每个领域每天一份，每条一个二级标题
- 领域：`eval` 能力评测 / `knowledge-base` 知识库 / `memory` 记忆 / `code-review` 代码审查 / `mcp` MCP / `skills` Skills / `bugfix` 修 Bug
- `mcp-skills` 已拆分，不能再写入。协议、网关、认证用 `mcp`；SKILL.md、技能评测与安全用 `skills`

## 写入规则（每个 Agent 汇报前先写入）
```
python3 /workspace/ai-radar/scripts/radar.py add \
  --topic mcp --title "一句话标题" --url "原文链接" \
  --summary "两三句要点，保留背景和限定条件。卡片上若写了摘要，这段不再重复展示" \
  --highlight "这条内容本身的一句判断" \
  --highlight "另一条判断" \
  --lesson "团队可以怎么改流程或补能力" \
  --lesson "另一条可实践的启发" \
  --source x|web --agent 你的名字 \
  --tags "a,b" \
  --link github=https://github.com/org/repo \
  --link paper=https://arxiv.org/abs/xxxx.xxxxx
python3 /workspace/ai-radar/scripts/radar.py publish
```
- 链接全局去重，已记录过的不会重复写入
- X 内容用 `--source x`（显示为「据 X 上的报道」），其他用 `--source web`（显示为「网页/文档」）
- 没有链接的不写，不编造
- `--highlight` 可重复，每条是卡片上的「摘要」：这条文章或项目本身的判断，不要写成给团队的建议
- `--lesson` 可重复，每条是卡片上的「启示」：可实践的改法、流程或能力缺口，不要把要点再讲一遍
- 两块都可以不写。没写的那一块不会出现在卡片上
- 修 Bug 用 `--topic bugfix`。侧边栏和筛选显示「修 Bug」，地址 hash 是 `#bugfix`
- `--link` 可重复，每个值是 `类型=URL`。请尽量带上能确定的原始资源：官方 GitHub、Hugging Face、论文、X 帖、官方文档、博客、演示、视频、数据包等。不确定的 URL 不要编
- 类型使用英文小写字母、数字和短横线，可以自由扩展，不限于内置名字。页面会给这些类型画专属图标：`github`、`hf`、`paper`、`arxiv`（与 paper 同一图标）、`x`、`docs`、`blog`、`demo`、`youtube`、`reddit`、`hn`、`pypi`、`npm`、`dataset`、`leaderboard`、`discord`、`spec`。其他类型使用通用链接图标，悬停显示类型名
- 主链接仍用 `--url`。与主链接相同的地址不必再写进 `--link`，页面上同一 URL 只显示一个图标
- 有额外资源时，条目里写成一行：`- 资源：github=https://github.com/org/repo；paper=https://arxiv.org/abs/xxxx.xxxxx`（类型之间用中文分号 `；`）。没有资源就不要写这一行

## 卡片上的两块列表

卡片的主信息是两块 bullet list，小标题分别是「摘要」和「启示」。缺哪一块，页面就隐藏哪一块，不留空标题。

`docs/data.json` 里对应两个字符串数组：

- `highlights`：摘要。只提炼这条内容本身的重点
- `lessons`：启示。写团队可以怎么建设能力，例如可执行的改法、流程调整、能力缺口

「要点」仍然要写，给搜索和没有摘要的旧卡片用。一旦写了摘要，卡片就不再展示整段要点，避免和第一块重复。只有启示、没有摘要时，要点段落仍留在标题下面。两块都没有时，卡片保持原来的要点段落。

手写时放在「要点」之后、「标签」和「资源」之前：

```markdown
## 一句话标题
- 来源：网页/文档　记录者：你的名字
- 链接：https://example.com/article
- 要点：两三句说明这是什么、依据是什么。
- 摘要：
  - 这条内容本身的判断，一句说完
  - 另一条判断
- 启示：
  - 团队可以改的一个做法
  - 需要补上的一种能力或流程
- 标签：a,b
- 资源：github=https://github.com/org/repo
```

- 列表项必须缩进：两个英文空格，再写 `- `。顶格的 `- 标签：`、`- 资源：` 不会被收进列表
- 只有一条时可以写在同一行：`- 摘要：这一句`
- 同一条如果要换行，下一行继续缩进，不要再加 `- `
- 每块通常 2–4 条。摘要只写原文里核对得到的判断；启示写团队接下来能做的事，不编造原文没有的数字
- 没有把握的那一块整段省掉，不要写空的标题行
- 旧稿里的「关键结论」「内容精炼总结」会并进摘要，「对团队的启发和学习」会并进启示
- 搜索会匹配要点、两块列表和标签

两块都写全的例子：`topics/eval/2026-10-26.md`。知识库、记忆、代码审查、MCP、Skills 最近的文件里，有的两块都有，有的只有摘要，打开即可照抄。

## 修 Bug

`--topic bugfix` 写入 `topics/bugfix/`。页面上的名字是「修 Bug」，hash 是 `#bugfix`。

侧边栏每个专题都有一个 16px 线框图标，并且只给图标上色，好和旁边的专题区分。修 Bug 用虫子图标，颜色是砖红（`#8d3b3b`，深色模式 `#f0b4b0`）。选中之后整行仍是统一的高亮，图标改成行内文字的颜色。窄屏的专题下拉左边也会显示同一个图标。

这个专题可以先没有条目。打开 `#bugfix` 时会看到「这个专题还没有条目」，不会留一张空卡片。

## 本地预览

在仓库根目录执行 `python3 scripts/build_site.py`，然后用浏览器打开 `docs/index.html`。默认是「全部」，最新日期在最上面。有两块列表的卡片直接显示「摘要」和「启示」；缺的那一块不出现。还没写这两块的卡片仍显示整段要点。

## 页面
`python3 scripts/build_site.py` 只用标准库，生成 `docs/index.html`、`docs/data.json` 和 `docs/.nojekyll`。桌面端（≥900px）是左侧专题栏：站点标题、搜索框、专题列表（另有「全部」，每项显示条数）；右侧是当前专题按日期分组的条目。窄屏改为顶部的标题、搜索和专题下拉。选中项记在 URL hash（如 `#mcp`、`#skills`、`#bugfix`），刷新或分享链接后仍停在该专题。搜索框只搜索当前专题的标题、要点、摘要、启示和标签。卡片顺序是标题、摘要、启示，然后是日期、标签和资源图标。没有摘要时，标题下仍是整段要点。

## 发布
`radar.py publish` 会重建静态页（`docs/`）、更新索引、提交并推送到 GitHub，GitHub Pages 自动刷新。
网页：https://scoheart.github.io/ai-radar/
