# AI 前沿追踪 · 持久归档

位置：`/workspace/ai-radar`（共享电脑上，所有 Agent 都能写）。

## 目录
- `INDEX.md`：总索引，按领域列出每天一份文件和条数（自动生成）
- `topics/<领域>/YYYY-MM-DD.md`：每个领域每天一份，每条一个二级标题
- 领域：`eval` 能力评测 / `knowledge-base` 知识库 / `memory` 记忆 / `code-review` 代码审查 / `mcp-skills` MCP 与 Skills

## 写入规则（每个 Agent 汇报前先写入）
```
python3 /workspace/ai-radar/scripts/radar.py add \
  --topic eval --title "一句话标题" --url "原文链接" \
  --summary "两三句要点" --source x|web --agent 你的名字 [--tags "a,b"]
python3 /workspace/ai-radar/scripts/radar.py publish
```
- 链接全局去重，已记录过的不会重复写入
- X 内容用 `--source x`（显示为「据 X 上的报道」）
- 没有链接的不写，不编造

## 发布
`radar.py publish` 会重建静态页（`docs/`）、更新索引、提交并推送到 GitHub，GitHub Pages 自动刷新。
网页：https://scoheart.github.io/ai-radar/
