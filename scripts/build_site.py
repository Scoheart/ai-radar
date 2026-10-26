#!/usr/bin/env python3
"""把 topics/*/*.md 解析成 docs/data.json，并生成静态页 docs/index.html。

只用 Python 标准库。
"""
import json, pathlib, re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = {
    "eval": "能力评测",
    "knowledge-base": "知识库",
    "memory": "记忆",
    "code-review": "代码审查",
    "mcp": "MCP",
    "skills": "Skills",
    "bugfix": "修 Bug",
}

def parse_links(raw):
    """解析「github=URL；hf=URL」。没有资源时返回空字典。"""
    links = {}
    for part in re.split(r"[；;]", raw or ""):
        part = part.strip().strip("。")
        if "=" not in part:
            continue
        typ, url = part.split("=", 1)
        typ, url = typ.strip(), url.strip()
        if typ and url:
            links[typ] = url
    return links

# 缩进的「- 」或「* 」。允许普通空格、制表符和全角空格。
NESTED_BULLET = re.compile(r"^[ \t\u3000]+[-*]\s+(.*)$")

def collect_items(lines, start, inline):
    """收集一个缩进列表。

    冒号同一行上的文字算一条；后面缩进的列表各算一条。
    空行不结束列表，只要后面还有缩进条目。下一条顶格内容则停。
    更深的缩进行并进上一条，避免一句被折行拆开。
    返回 (条目列表, 下一条待处理行的下标)。
    """
    items = []
    inline = (inline or "").strip()
    if inline:
        items.append(inline)
    i = start
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and NESTED_BULLET.match(lines[j]):
                i = j
                continue
            break
        m = NESTED_BULLET.match(ln)
        if m:
            text = m.group(1).strip()
            if text:
                items.append(text)
            i += 1
            continue
        if items and re.match(r"^[ \t\u3000]{2,}\S", ln):
            items[-1] = (items[-1] + " " + ln.strip()).strip()
            i += 1
            continue
        break
    return items, i

# 旧稿称呼仍认：关键结论、内容精炼总结并进摘要；对团队的启发和学习并进启示。
LIST_FIELDS = {
    "摘要": "highlights",
    "内容精炼总结": "highlights",
    "关键结论": "highlights",
    "启示": "lessons",
    "对团队的启发和学习": "lessons",
}
LIST_HEAD = re.compile(
    r"^- (内容精炼总结|对团队的启发和学习|关键结论|摘要|启示)\s*[:：]\s*(.*)$"
)

def parse():
    items = []
    for topic in TOPICS:
        folder = ROOT / "topics" / topic
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.md")):
            date = f.stem
            for block in re.split(r"^## ", f.read_text(), flags=re.M)[1:]:
                lines = block.strip().splitlines()
                it = {
                    "topic": topic,
                    "date": date,
                    "title": lines[0].strip(),
                    "url": "",
                    "summary": "",
                    "source": "",
                    "agent": "",
                    "tags": [],
                    "links": {},
                    "highlights": [],
                    "lessons": [],
                }
                i = 1
                while i < len(lines):
                    ln = lines[i]
                    m = LIST_HEAD.match(ln)
                    if m:
                        extra, i = collect_items(lines, i + 1, m.group(2))
                        it[LIST_FIELDS[m.group(1)]].extend(extra)
                        continue
                    if ln.startswith("- 来源："):
                        m = re.match(r"- 来源：(.*?)　记录者：(.*)", ln)
                        if m:
                            it["source"], it["agent"] = m.group(1).strip(), m.group(2).strip()
                    elif ln.startswith("- 链接："):
                        it["url"] = ln.removeprefix("- 链接：").strip()
                    elif ln.startswith("- 要点："):
                        it["summary"] = ln.removeprefix("- 要点：").strip()
                    elif ln.startswith("- 标签："):
                        it["tags"] = [x.strip() for x in re.split(r"[,，]", ln.removeprefix("- 标签：")) if x.strip()]
                    elif ln.startswith("- 资源：") or ln.startswith("- 资源:"):
                        it["links"] = parse_links(re.sub(r"^- 资源[:：]", "", ln).strip())
                    i += 1
                items.append(it)
    return items

def embed(obj):
    # 避免条目正文里的 `<` 提前结束 script。
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )

HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>AI 雷达 - 社区</title>
<style>
:root {
  --bg: #f3f2ef;
  --side: #e7e5e0;
  --fg: #1c1b19;
  --muted: #5f5a53;
  --card: #fffcf9;
  --line: #e3dfd6;
  --chip: #eeece6;
  --accent: #1f4e79;
  --lesson: #2f6b4a;
  --nav-on: #1f4e79;
  --nav-on-fg: #f7f5f1;
  --nav-hover: rgba(28, 27, 25, .055);
  --shadow: 0 1px 0 rgba(28, 27, 25, .04);
  --side-w: 248px;
  --bar-h: 0px;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #141311;
    --side: #1c1b18;
    --fg: #f3f0ea;
    --muted: #b7b0a4;
    --card: #1e1d1a;
    --line: #34322c;
    --chip: #2a2824;
    --accent: #9ec4e6;
    --lesson: #9dccb0;
    --nav-on: #9ec4e6;
    --nav-on-fg: #142028;
    --nav-hover: rgba(243, 240, 234, .06);
    --shadow: none;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
html { scroll-padding-top: calc(var(--bar-h, 0px) + 12px); }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei", "WenQuanYi Micro Hei", "Droid Sans Fallback", sans-serif;
}
.app {
  display: flex;
  align-items: flex-start;
  min-height: 100vh;
}
.side {
  position: sticky;
  top: 0;
  align-self: flex-start;
  flex: 0 0 var(--side-w);
  width: var(--side-w);
  height: 100vh;
  height: 100dvh;
  overflow-y: auto;
  padding: 22px 12px 28px;
  background: var(--side);
  border-right: 1px solid var(--line);
  z-index: 5;
}
.mast { margin: 0 4px 14px; padding: 0 8px; }
h1 { font-size: 20px; line-height: 1.25; font-weight: 600; letter-spacing: -0.02em; margin: 0; }
.sub { margin: 4px 0 0; color: var(--muted); font-size: 12px; line-height: 1.4; }
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 4px 12px;
  padding: 0 10px;
  height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--card);
}
.search svg, .picker > svg { width: 16px; height: 16px; flex: none; stroke: var(--muted); fill: none; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }
.search input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--fg);
  font: inherit;
  font-size: 14px;
}
.search input::placeholder { color: var(--muted); }
.search:focus-within, .picker select:focus-visible, .iconbtn:focus-visible, .summary a:focus-visible, .block a:focus-visible, h3 a:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.nav { display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 34px;
  padding: 6px 10px;
  border-radius: 8px;
  color: var(--fg);
  text-decoration: none;
  font-size: 14px;
  line-height: 1.35;
}
.nav-item .name { display: flex; align-items: center; gap: 8px; min-width: 0; }
.nav-item .label { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mark {
  width: 16px;
  height: 16px;
  flex: none;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
  color: var(--mark, var(--muted));
}
.nav-item[aria-current="page"] .mark { color: currentColor; }
[data-topic="eval"] { --mark: #1f4e79; }
[data-topic="knowledge-base"] { --mark: #2f6b4a; }
[data-topic="memory"] { --mark: #5c4e86; }
[data-topic="code-review"] { --mark: #3d6278; }
[data-topic="mcp"] { --mark: #0e6b6b; }
[data-topic="skills"] { --mark: #8a5520; }
[data-topic="bugfix"] { --mark: #8d3b3b; }
@media (prefers-color-scheme: dark) {
  [data-topic="eval"] { --mark: #9ec4e6; }
  [data-topic="knowledge-base"] { --mark: #9dccb0; }
  [data-topic="memory"] { --mark: #cfc4ea; }
  [data-topic="code-review"] { --mark: #a9c7d6; }
  [data-topic="mcp"] { --mark: #8fd0d0; }
  [data-topic="skills"] { --mark: #e2b98a; }
  [data-topic="bugfix"] { --mark: #f0b4b0; }
}
.nav-item .n {
  flex: none;
  min-width: 1.6em;
  text-align: right;
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
.nav-item:hover { background: var(--nav-hover); }
.nav-item[aria-current="page"] {
  background: var(--nav-on);
  color: var(--nav-on-fg);
  font-weight: 600;
}
.nav-item[aria-current="page"]:hover { background: var(--nav-on); }
.nav-item[aria-current="page"] .n { color: var(--nav-on-fg); font-weight: 500; }
.nav-item:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.nav-item[aria-current="page"]:focus-visible { outline-color: var(--nav-on-fg); }
.picker { display: none; position: relative; margin: 0 4px; }
.picker select {
  width: 100%;
  height: 42px;
  padding: 0 36px 0 36px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--card);
  color: var(--fg);
  font: inherit;
  font-size: 16px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
}
.picker > svg {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.picker-mark {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  pointer-events: none;
  z-index: 1;
}
.main { flex: 1 1 auto; min-width: 0; padding: 14px 32px 88px; }
.stream { max-width: 720px; min-width: 0; }
.hint { margin: 8px 0 0; color: var(--muted); font-size: 12px; }
.hint:empty { display: none; }
.day {
  position: sticky;
  top: var(--bar-h, 0px);
  z-index: 4;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin: 0;
  padding: 12px 0 8px;
  background: var(--bg);
  border-bottom: 1px solid var(--line);
  font-size: 13px;
  font-weight: 600;
}
.day .c { color: var(--muted); font-weight: 500; font-variant-numeric: tabular-nums; }
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px 12px;
  margin: 10px 0 0;
  box-shadow: var(--shadow);
}
.card:hover { position: relative; z-index: 3; }
.kicker { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding: 0 8px 0 6px;
  border-radius: 999px;
  background: var(--chip);
  color: var(--muted);
  font-size: 12px;
}
.chip .mark { width: 14px; height: 14px; }
.card h3 { font-size: 16px; line-height: 1.45; font-weight: 600; letter-spacing: -0.011em; margin: 0 0 6px; }
.card h3 a { color: inherit; text-decoration: none; }
.card h3 a:hover { color: var(--accent); }
.summary { margin: 0; font-size: 14.5px; line-height: 1.65; }
.summary a, .block a { color: var(--accent); text-underline-offset: 2px; overflow-wrap: anywhere; }
.block {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
}
.block h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 4px;
  color: var(--fg);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
}
.block h4::before {
  content: "";
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 2px;
  background: var(--accent);
}
.lessons h4::before { background: var(--lesson); }
.block ul { margin: 0; padding: 0 0 0 1.15em; }
.block li {
  margin: 0;
  padding: 1px 0;
  font-size: 14px;
  line-height: 1.55;
  overflow-wrap: break-word;
}
.highlights li::marker { color: var(--accent); }
.lessons li::marker { color: var(--lesson); }
.block-first { margin-top: 8px; padding-top: 0; border-top: 0; }
.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 12.5px;
}
.meta time { font-variant-numeric: tabular-nums; }
.tag {
  display: inline-block;
  padding: 0 6px;
  border-radius: 4px;
  background: var(--chip);
  color: var(--fg);
  font-size: 12px;
}
.actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 12px; }
.icons { display: flex; flex-wrap: wrap; gap: 6px; }
.iconbtn {
  position: relative;
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
  border-radius: 9px;
  background: var(--bg);
  color: var(--fg);
  text-decoration: none;
}
.iconbtn:hover { border-color: var(--fg); color: var(--accent); }
.iconbtn svg { width: 16px; height: 16px; display: block; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }
.iconbtn:hover::after, .iconbtn:focus-visible::after {
  content: attr(data-label);
  position: absolute;
  left: 50%;
  bottom: calc(100% + 6px);
  transform: translateX(-50%);
  padding: 4px 7px;
  border-radius: 6px;
  background: var(--fg);
  color: var(--bg);
  font-size: 12px;
  line-height: 1.3;
  white-space: nowrap;
  pointer-events: none;
  z-index: 6;
}
.empty { color: var(--muted); text-align: center; padding: 48px 8px; }
@media (max-width: 899px) {
  :root { --bar-h: 148px; }
  .app { display: block; min-height: 0; }
  .side {
    position: sticky;
    top: 0;
    width: auto;
    height: auto;
    flex: none;
    overflow: visible;
    z-index: 8;
    padding: 14px 14px 12px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .mast { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 2px 12px; margin: 0 0 10px; padding: 0 2px; }
  h1 { font-size: 18px; }
  .sub { margin: 0; }
  .search { height: 42px; margin: 0 0 8px; border-radius: 10px; padding: 0 12px; }
  .search input { font-size: 16px; }
  .nav { display: none; }
  .picker { display: block; }
  .main { padding: 4px 14px 72px; }
}
@media (max-width: 640px) {
  .card { padding: 13px 13px 12px; }
  .block { margin-top: 8px; padding-top: 7px; }
  .block-first { margin-top: 8px; padding-top: 0; border-top: 0; }
  .iconbtn { width: 44px; height: 44px; }
}
@media (forced-colors: active) {
  .nav-item[aria-current="page"] { background: Highlight; color: HighlightText; outline: 2px solid CanvasText; }
  .nav-item[aria-current="page"] .n { color: HighlightText; }
  .block { border-top-color: CanvasText; }
  .block h4, .block li::marker { color: CanvasText; }
  .block h4::before { background: CanvasText; }
  .mark { color: CanvasText; }
  .nav-item[aria-current="page"] .mark { color: HighlightText; }
}
@media (prefers-reduced-motion: reduce) {
  * { scroll-behavior: auto !important; }
}
</style>
</head>
<body>
<div class="app">
<aside class="side">
  <header class="mast">
    <h1>AI 雷达 - 社区</h1>
    <p class="sub" id="sub"></p>
  </header>
  <label class="search">
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
    <input id="q" type="search" placeholder="搜索当前专题" aria-label="搜索当前专题的标题、要点、摘要、启示、标签" autocomplete="off">
  </label>
  <nav class="nav" id="nav" aria-label="专题"></nav>
  <label class="picker">
    <span id="topic-mark" class="picker-mark" aria-hidden="true"></span>
    <select id="topic" aria-label="专题"></select>
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
  </label>
</aside>
<main class="main">
  <div class="stream">
    <p class="hint" id="hint" aria-live="polite"></p>
    <div id="list"></div>
    <noscript><p class="empty">需要启用 JavaScript 才能浏览这份归档。</p></noscript>
  </div>
</main>
</div>
<script>
const T = __TOPICS__;
const D = __DATA__;
const ORDER = ["all", ...Object.keys(T)];
const TOPIC_ICON = {
  all: '<path d="M9 7h11M9 12h11M9 17h11"/><path d="M4.5 7h.01M4.5 12h.01M4.5 17h.01"/>',
  eval: '<rect x="6" y="4" width="12" height="16" rx="2"/><path d="M9 4.5h6M9 12.5l2 2 4-4"/>',
  "knowledge-base": '<path d="M5 5.2A2.2 2.2 0 0 1 7.2 3H19v16H7.2A2.2 2.2 0 0 0 5 21.2z"/><path d="M5 5.2A2.2 2.2 0 0 1 7.2 7.4H19"/>',
  memory: '<path d="M12 4 3.5 8.5 12 13l8.5-4.5L12 4z"/><path d="M3.5 12 12 16.5 20.5 12M3.5 15.5 12 20l8.5-4.5"/>',
  "code-review": '<path d="M8 8 4 12l4 4M16 8l4 4-4 4"/>',
  mcp: '<circle cx="6" cy="12" r="2.2"/><circle cx="17" cy="7" r="2.2"/><circle cx="17" cy="17" r="2.2"/><path d="M8.1 12H12l2.6-3.6M12 12l2.6 3.6"/>',
  skills: '<path d="M4 9h16v10H4z"/><path d="M9 9V7.2A3 3 0 0 1 15 7.2V9M4 13h16"/>',
  bugfix: '<path d="M9 10.2a3 3 0 0 1 6 0V14a3 3 0 0 1-6 0z"/><path d="M12 10.2V14M9 12H5.5M15 12h3.5"/><path d="M9.2 14.6 6.8 17M14.8 14.6l2.4 2.4M9.2 10.2 7 7.2M14.8 10.2 17 7.2"/>'
};
function topicIcon(k) {
  const body = TOPIC_ICON[k];
  if (!body) return "";
  return `<svg class="mark" viewBox="0 0 24 24" aria-hidden="true">${body}</svg>`;
}

const LABEL = {
  github: "GitHub", hf: "Hugging Face", paper: "论文", arxiv: "arXiv", x: "X",
  docs: "文档", blog: "博客", demo: "演示", youtube: "YouTube", reddit: "Reddit",
  hn: "Hacker News", pypi: "PyPI", npm: "npm", dataset: "数据集",
  leaderboard: "排行榜", discord: "Discord", spec: "规范", link: "链接"
};
const ICONS = {
  github: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
  hf: '<circle cx="12" cy="12.2" r="7.2"/><path d="M8.4 13.6c.8 1.35 2 2 3.6 2s2.8-.65 3.6-2"/><circle cx="9.2" cy="10.6" r=".7" style="fill:currentColor;stroke:none"/><circle cx="14.8" cy="10.6" r=".7" style="fill:currentColor;stroke:none"/><path d="M7.2 8.4 5.6 6.2M16.8 8.4l1.6-2.2"/>',
  paper: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M8 13h8M8 17h5"/>',
  x: '<path d="M5 5l14 14M19 5 5 19"/>',
  docs: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  blog: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  demo: '<circle cx="12" cy="12" r="9"/><path d="M10 8.8v6.4l5.6-3.2z"/>',
  youtube: '<rect x="2.5" y="6" width="19" height="12" rx="3"/><path d="M10.5 9.4v5.2l5-2.6z"/>',
  reddit: '<circle cx="12" cy="13" r="7"/><circle cx="9" cy="12.6" r=".7" style="fill:currentColor;stroke:none"/><circle cx="15" cy="12.6" r=".7" style="fill:currentColor;stroke:none"/><path d="M9.2 15.4c.8.8 1.8 1.2 2.8 1.2s2-.4 2.8-1.2"/><path d="M15.6 8.2 13.8 6.6"/><circle cx="17.2" cy="7.4" r="1.5"/>',
  hn: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 7.5 12 13l4-5.5M12 13v4.5"/>',
  pypi: '<path d="M12 3 20 7.5v9L12 21 4 16.5v-9z"/><path d="M12 12 20 7.5M12 12v9M12 12 4 7.5"/>',
  npm: '<path d="M4 8h16v8H4z"/><path d="M8 16V10h2.2v4h1.6V10H14v6"/>',
  dataset: '<ellipse cx="12" cy="6" rx="7.5" ry="3"/><path d="M4.5 6v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"/><path d="M4.5 12v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6"/>',
  leaderboard: '<path d="M8 21h8M12 17v4"/><path d="M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4.5A2.5 2.5 0 0 0 7 10.5M17 6h2.5A2.5 2.5 0 0 1 17 10.5"/>',
  discord: '<path d="M8 8.6c1.6-.9 3.1-1.3 4-1.3s2.4.4 4 1.3"/><path d="M6.6 10.2C5 11.5 4.4 13.4 4.4 15.4c1.5 1.1 3 1.6 4.5 1.6l.8-1.6h4.6l.8 1.6c1.5 0 3-.5 4.5-1.6 0-2-0.6-3.9-2.2-5.2"/><circle cx="9.4" cy="13.8" r=".7" style="fill:currentColor;stroke:none"/><circle cx="14.6" cy="13.8" r=".7" style="fill:currentColor;stroke:none"/>',
  spec: '<path d="M9 6h12M9 12h12M9 18h12"/><path d="M3.5 6.2 5 7.6 7.2 4.8M3.5 12.2 5 13.6 7.2 10.8M3.5 18.2 5 19.6 7.2 16.8"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.07 0l1.77-1.77a5 5 0 0 0-7.07-7.07L10.5 5.4"/><path d="M14 11a5 5 0 0 0-7.07 0L5.16 12.77a5 5 0 0 0 7.07 7.07l1.23-1.23"/>'
};

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const linkify = s => esc(s).replace(/(https?:\/\/[^\s，。）)]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
const labelOf = type => LABEL[type] || type;
const iconOf = type => ICONS[type === "arxiv" ? "paper" : type] || ICONS.link;

function hostOf(u) { return u.hostname.toLowerCase().replace(/^www\./, ""); }
function under(h, domain) { return h === domain || h.endsWith("." + domain); }
function detect(url) {
  let u;
  try { u = new URL(url); } catch { return "link"; }
  if (u.protocol !== "http:" && u.protocol !== "https:") return "link";
  const h = hostOf(u);
  const seg = u.pathname.split("/").filter(Boolean).map(s => s.toLowerCase());
  if (under(h, "github.com")) return "github";
  if (under(h, "arxiv.org")) return "arxiv";
  if (["openreview.net", "aclanthology.org", "aclweb.org", "biorxiv.org", "medrxiv.org", "semanticscholar.org", "doi.org", "ssrn.com", "paperswithcode.com"].some(d => under(h, d))) return "paper";
  if (under(h, "x.com") || under(h, "twitter.com")) return "x";
  if (under(h, "youtube.com") || h === "youtu.be") return "youtube";
  if (under(h, "reddit.com")) return "reddit";
  if (h === "news.ycombinator.com") return "hn";
  if (under(h, "pypi.org") || h === "pypi.python.org") return "pypi";
  if (under(h, "npmjs.com") || under(h, "npmjs.org")) return "npm";
  if (under(h, "discord.com") || h === "discord.gg" || under(h, "discordapp.com")) return "discord";
  if (under(h, "huggingface.co") || h === "hf.co") return seg[0] === "datasets" ? "dataset" : "hf";
  if (["medium.com", "substack.com", "dev.to", "bearblog.dev", "hashnode.dev", "wordpress.com"].some(d => under(h, d))) return "blog";
  if (under(h, "readthedocs.io") || under(h, "gitbook.io")) return "docs";
  if (h.startsWith("blog.")) return "blog";
  if (h.startsWith("docs.")) return "docs";
  if (h.startsWith("spec.")) return "spec";
  if (h.startsWith("demo.")) return "demo";
  const table = [
    ["blog", ["blog", "news", "posts", "post", "articles", "article", "research", "research-notes"]],
    ["docs", ["docs", "doc", "documentation", "guide", "guides", "reference"]],
    ["spec", ["seps", "sep", "spec", "specs", "specification", "rfc"]],
    ["leaderboard", ["leaderboard", "leaderboards", "benchmarks"]],
    ["dataset", ["datasets", "dataset"]],
    ["demo", ["demo", "playground"]]
  ];
  for (const s of seg) {
    for (const [type, names] of table) if (names.includes(s)) return type;
  }
  if (h.startsWith("developers.") || h.startsWith("developer.")) return "docs";
  if (h.endsWith(".github.io")) return "docs";
  return "link";
}
function norm(url) {
  try {
    const u = new URL(url);
    const h = hostOf(u);
    return u.protocol + "//" + h + u.pathname.replace(/\/+$/, "") + u.search;
  } catch { return String(url || "").trim(); }
}
function safeHttp(url) { return /^https?:\/\//i.test(url || ""); }
function resources(item) {
  const explicit = [];
  const seen = new Set();
  for (const [type, url] of Object.entries(item.links || {})) {
    if (!safeHttp(url)) continue;
    const n = norm(url);
    if (seen.has(n)) continue;
    seen.add(n);
    explicit.push({ type, url, n });
  }
  const out = [];
  const shown = new Set();
  if (safeHttp(item.url)) {
    const n = norm(item.url);
    out.push({ type: detect(item.url), url: item.url });
    shown.add(n);
  }
  for (const e of explicit) {
    if (shown.has(e.n)) continue;
    shown.add(e.n);
    out.push({ type: e.type, url: e.url });
  }
  return out;
}
function iconLink(type, url) {
  const name = labelOf(type);
  return `<a class="iconbtn" data-type="${esc(type)}" data-label="${esc(name)}" href="${esc(url)}" target="_blank" rel="noopener" aria-label="${esc(name)}"><svg viewBox="0 0 24 24" aria-hidden="true">${iconOf(type)}</svg></a>`;
}

let cur = "all";
const latest = D.map(x => x.date).sort().at(-1) || "—";
document.getElementById("sub").textContent = `共 ${D.length} 条 · 更新至 ${latest}`;

function fromHash() {
  const h = decodeURIComponent(location.hash.replace(/^#/, ""));
  if (!h || h === "all") return "all";
  return Object.prototype.hasOwnProperty.call(T, h) ? h : "all";
}
const narrow = () => window.matchMedia("(max-width: 899px)").matches;
function syncBar() {
  const side = document.querySelector(".side");
  const h = narrow() ? side.offsetHeight : 0;
  document.documentElement.style.setProperty("--bar-h", h + "px");
}
function topicName(k) { return k === "all" ? "全部" : (T[k] || k); }
function countOf(k) { return k === "all" ? D.length : D.filter(x => x.topic === k).length; }
function rawHash() { return decodeURIComponent(location.hash.replace(/^#/, "")); }
function readHash() {
  const next = fromHash();
  if (rawHash() !== next) history.replaceState(null, "", "#" + next);
  return next;
}
function paintNav() {
  const nav = document.getElementById("nav");
  const sel = document.getElementById("topic");
  if (!nav.childElementCount) {
    for (const k of ORDER) {
      const name = topicName(k);
      const n = countOf(k);
      const a = document.createElement("a");
      a.className = "nav-item";
      a.href = "#" + k;
      a.dataset.key = k;
      if (k !== "all") a.dataset.topic = k;
      a.innerHTML = `<span class="name">${topicIcon(k)}<span class="label">${esc(name)}</span></span><span class="n">${n}</span>`;
      nav.appendChild(a);
      const opt = document.createElement("option");
      opt.value = k;
      opt.textContent = name + " · " + n;
      sel.appendChild(opt);
    }
  }
  for (const a of nav.querySelectorAll(".nav-item")) {
    if (a.dataset.key === cur) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
  if (sel.value !== cur) sel.value = cur;
  const mark = document.getElementById("topic-mark");
  if (cur === "all") mark.removeAttribute("data-topic");
  else mark.dataset.topic = cur;
  mark.innerHTML = topicIcon(cur);
  document.title = topicName(cur) + " · AI 雷达 - 社区";
}
function render() {
  const q = document.getElementById("q").value.trim().toLowerCase();
  const name = cur === "all" ? "全部" : T[cur];
  const hay = x => [x.title, x.summary, ...(x.highlights || []), ...(x.lessons || []), ...(x.tags || [])].join("\n").toLowerCase();
  const xs = D.filter(x => (cur === "all" || x.topic === cur) && (!q || hay(x).includes(q)));
  xs.sort((a, b) => a.date === b.date ? 0 : (a.date < b.date ? 1 : -1));
  const hint = document.getElementById("hint");
  hint.textContent = q ? `在「${name}」中 ${xs.length} 条匹配` : "";
  const list = document.getElementById("list");
  if (!xs.length) {
    const msg = q || cur === "all" ? "没有匹配的内容" : "这个专题还没有条目";
    list.innerHTML = `<p class="empty">${msg}</p>`;
    return;
  }
  const groups = [];
  for (const x of xs) {
    if (!groups.length || groups[groups.length - 1].date !== x.date) groups.push({ date: x.date, items: [x] });
    else groups[groups.length - 1].items.push(x);
  }
  list.innerHTML = groups.map(g => {
    const cards = g.items.map(card).join("");
    return `<section><h2 class="day"><span>${esc(g.date)}</span><span class="c">${g.items.length} 条</span></h2>${cards}</section>`;
  }).join("");
}
function bulletBlock(items, title, kind, divided) {
  const xs = (Array.isArray(items) ? items : []).map(s => String(s).trim()).filter(Boolean);
  if (!xs.length) return "";
  const cls = divided ? `block ${kind}` : `block ${kind} block-first`;
  return `<section class="${cls}"><h4>${title}</h4><ul>${xs.map(t => `<li>${linkify(t)}</li>`).join("")}</ul></section>`;
}
function card(x) {
  const icons = resources(x).map(r => iconLink(r.type, r.url)).join("");
  const title = safeHttp(x.url) ? `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title)}</a>` : esc(x.title);
  const chips = [];
  if (cur === "all") chips.push(`<span class="chip">${topicIcon(x.topic)}${esc(T[x.topic] || x.topic)}</span>`);
  const kicker = chips.length ? `<div class="kicker">${chips.join("")}</div>` : "";
  const tags = (x.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
  const prose = String(x.summary || "").trim();
  const highlightItems = Array.isArray(x.highlights) ? x.highlights : [];
  const hasHighlights = highlightItems.some(s => String(s).trim());
  const summary = prose && !hasHighlights ? `<p class="summary">${linkify(prose)}</p>` : "";
  const highlights = bulletBlock(x.highlights, "摘要", "highlights", !!summary);
  const lessons = bulletBlock(x.lessons, "启示", "lessons", !!(summary || highlights));
  const actions = icons ? `<div class="actions"><div class="icons">${icons}</div></div>` : "";
  return `<article class="card" data-topic="${esc(x.topic)}">
    ${kicker}
    <h3>${title}</h3>
    ${summary}
    ${highlights}
    ${lessons}
    <div class="meta"><time datetime="${esc(x.date)}">${esc(x.date)}</time>${tags}</div>
    ${actions}
  </article>`;
}
function paint() { paintNav(); render(); syncBar(); }
document.getElementById("q").addEventListener("input", () => { render(); syncBar(); });
document.getElementById("topic").addEventListener("change", () => {
  const k = document.getElementById("topic").value;
  if (rawHash() !== k) location.hash = k;
});
window.addEventListener("hashchange", () => {
  const next = readHash();
  const changed = next !== cur;
  cur = next;
  paint();
  if (changed) window.scrollTo(0, 0);
});
window.addEventListener("resize", syncBar);
if (window.ResizeObserver) new ResizeObserver(syncBar).observe(document.querySelector(".side"));
cur = readHash();
paint();
</script>
</body>
</html>
"""

def main():
    items = parse()
    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    (out / "data.json").write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    html = HTML.replace("__TOPICS__", embed(TOPICS)).replace("__DATA__", embed(items))
    (out / "index.html").write_text(html)
    (out / ".nojekyll").write_text("")
    counts = Counter(i["topic"] for i in items)
    linked = sum(1 for i in items if i["links"])
    highlighted = sum(1 for i in items if i["highlights"])
    taught = sum(1 for i in items if i["lessons"])
    print(f"站点已生成：{len(items)} 条，其中 {linked} 条带资源行，{highlighted} 条带摘要，{taught} 条带启示")
    for key, name in TOPICS.items():
        print(f"  {key} {name}: {counts[key]}")

if __name__ == "__main__":
    main()
