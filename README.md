# AI 前沿追踪 · 持久归档

位置：`/workspace/ai-radar`（共享电脑上，所有 Agent 都能写）。

## 目录
- `INDEX.md`：总索引，按领域列出每天一份文件和条数（自动生成）
- `topics/<领域>/YYYY-MM-DD.md`：每个领域每天一份，每条一个二级标题
- 领域：`eval` 能力评测 / `knowledge-base` 知识库 / `memory` 记忆 / `code-review` 代码审查 / `mcp` MCP / `skills` Skills
- `mcp-skills` 已拆分，不能再写入。协议、网关、认证用 `mcp`；SKILL.md、技能评测与安全用 `skills`

## 写入规则（每个 Agent 汇报前先写入）
```
python3 /workspace/ai-radar/scripts/radar.py add \
  --topic mcp --title "一句话标题" --url "原文链接" \
  --summary "两三句要点" --source x|web --agent 你的名字 \
  --tags "a,b" \
  --link github=https://github.com/org/repo \
  --link paper=https://arxiv.org/abs/xxxx.xxxxx
python3 /workspace/ai-radar/scripts/radar.py publish
```
- 链接全局去重，已记录过的不会重复写入
- X 内容用 `--source x`（显示为「据 X 上的报道」），其他用 `--source web`（显示为「网页/文档」）
- 没有链接的不写，不编造
- `--link` 可重复，每个值是 `类型=URL`。请尽量带上能确定的原始资源：官方 GitHub、Hugging Face、论文、X 帖、官方文档、博客、演示、视频、数据包等。不确定的 URL 不要编
- 类型使用英文小写字母、数字和短横线，可以自由扩展，不限于内置名字。页面会给这些类型画专属图标：`github`、`hf`、`paper`、`arxiv`（与 paper 同一图标）、`x`、`docs`、`blog`、`demo`、`youtube`、`reddit`、`hn`、`pypi`、`npm`、`dataset`、`leaderboard`、`discord`、`spec`。其他类型使用通用链接图标，悬停显示类型名
- 主链接仍用 `--url`。与主链接相同的地址不必再写进 `--link`，页面上同一 URL 只显示一个图标
- 有额外资源时，条目里写成一行：`- 资源：github=https://github.com/org/repo；paper=https://arxiv.org/abs/xxxx.xxxxx`（类型之间用中文分号 `；`）。没有资源就不要写这一行

## 页面
`python3 scripts/build_site.py` 只用标准库，生成 `docs/index.html`、`docs/data.json` 和 `docs/.nojekyll`。顶部是一排专题 Tab（另有「全部」，并显示条数），选中项记在 URL hash（如 `#mcp`、`#skills`），刷新或分享链接后仍停在该 Tab。搜索框只搜索当前 Tab。

## 发布
`radar.py publish` 会重建静态页（`docs/`）、更新索引、提交并推送到 GitHub，GitHub Pages 自动刷新。
网页：https://scoheart.github.io/ai-radar/
