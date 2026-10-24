#!/usr/bin/env python3
"""AI 前沿追踪归档工具。用法见 README.md。"""
import argparse, datetime, pathlib, re, sys, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = {
    "eval": "AI 能力评测",
    "knowledge-base": "知识库 / RAG",
    "memory": "AI 记忆",
    "code-review": "AI Code Review",
    "mcp-skills": "MCP 与 Skills",
}

def add(a):
    if a.topic not in TOPICS:
        sys.exit(f"topic 必须是 {list(TOPICS)}")
    date = a.date or datetime.date.today().isoformat()
    f = ROOT / "topics" / a.topic / f"{date}.md"
    if f.exists() and a.url in f.read_text():
        print("已存在，跳过:", a.url); return
    # 全局按 URL 去重
    for p in (ROOT / "topics").rglob("*.md"):
        if a.url in p.read_text():
            print("已在", p.relative_to(ROOT), "出现过，跳过"); return
    if not f.exists():
        f.write_text(f"# {TOPICS[a.topic]} · {date}\n\n")
    src = "据 X 上的报道" if a.source == "x" else "网页/文档"
    with f.open("a") as fh:
        fh.write(f"## {a.title}\n- 来源：{src}　记录者：{a.agent}\n- 链接：{a.url}\n- 要点：{a.summary}\n")
        if a.tags: fh.write(f"- 标签：{a.tags}\n")
        fh.write("\n")
    print("已写入", f.relative_to(ROOT))
    index()

def index(_=None):
    lines = ["# 索引（自动生成，勿手改）\n"]
    for t, name in TOPICS.items():
        lines.append(f"## {name}\n")
        for p in sorted((ROOT / "topics" / t).glob("*.md"), reverse=True):
            n = len(re.findall(r"^## ", p.read_text(), re.M))
            lines.append(f"- [{p.stem}](topics/{t}/{p.name})（{n} 条）")
        lines.append("")
    (ROOT / "INDEX.md").write_text("\n".join(lines))

def commit(_=None):
    subprocess.run(["git", "add", "-A"], cwd=ROOT)
    subprocess.run(["git", "-c", "user.name=ai-radar", "-c", "user.email=ai-radar@local",
                    "commit", "-qm", f"radar {datetime.datetime.now():%F %T}"], cwd=ROOT)

p = argparse.ArgumentParser()
s = p.add_subparsers(required=True)
x = s.add_parser("add"); x.set_defaults(fn=add)
x.add_argument("--topic", required=True); x.add_argument("--title", required=True)
x.add_argument("--url", required=True); x.add_argument("--summary", required=True)
x.add_argument("--source", choices=["x", "web"], default="web")
x.add_argument("--agent", default="unknown"); x.add_argument("--date"); x.add_argument("--tags", default="")
s.add_parser("index").set_defaults(fn=index)
s.add_parser("commit").set_defaults(fn=commit)
a = p.parse_args(); a.fn(a)
