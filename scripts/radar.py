#!/usr/bin/env python3
"""AI 前沿追踪归档工具。用法见 README.md。"""
import argparse, datetime, pathlib, re, sys, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = {
    "eval": "能力评测",
    "knowledge-base": "知识库",
    "memory": "记忆",
    "code-review": "代码审查",
    "mcp": "MCP",
    "skills": "Skills",
}
# 小写字母、数字、短横线，可以自由扩展，不限于内置图标。
LINK_TYPE = re.compile(r"^[a-z0-9-]+$")
BUILTIN_ICONS = (
    "github", "hf", "paper", "arxiv", "x", "docs", "blog", "demo",
    "youtube", "reddit", "hn", "pypi", "npm", "dataset", "leaderboard",
    "discord", "spec",
)

def parse_link(raw):
    if "=" not in raw:
        sys.exit(f"--link 需要「类型=URL」，收到：{raw}")
    typ, url = raw.split("=", 1)
    typ, url = typ.strip(), url.strip()
    if not typ or not LINK_TYPE.fullmatch(typ) or not re.search(r"[a-z0-9]", typ):
        sys.exit(
            f"资源类型「{typ}」不合法：只能使用英文小写字母、数字和短横线"
            "（例如 github、paper、my-notes）。类型可以自由扩展；"
            "页面为 "
            + "、".join(BUILTIN_ICONS)
            + " 准备了专属图标，其余类型使用通用链接图标。"
        )
    if not re.match(r"^https?://\S+$", url):
        sys.exit(f"--link 的 URL 需以 http:// 或 https:// 开头，且不能含空白：{url}")
    return typ, url

def add(a):
    if a.topic == "mcp-skills":
        sys.exit("专题 mcp-skills 已拆成 mcp 和 skills，请改用 --topic mcp 或 --topic skills")
    if a.topic not in TOPICS:
        names = "、".join(f"{k}（{v}）" for k, v in TOPICS.items())
        sys.exit(f"topic 必须是以下之一：{names}。收到：{a.topic}")
    links, seen = [], set()
    for raw in a.link or []:
        typ, url = parse_link(raw)
        if typ in seen:
            sys.exit(f"--link 类型「{typ}」重复，每种类型只写一个 URL")
        seen.add(typ)
        links.append((typ, url))
    date = a.date or datetime.date.today().isoformat()
    f = ROOT / "topics" / a.topic / f"{date}.md"
    if f.exists() and a.url in f.read_text():
        print("已存在，跳过:", a.url); return
    for p in (ROOT / "topics").rglob("*.md"):
        if a.url in p.read_text():
            print("已在", p.relative_to(ROOT), "出现过，跳过"); return
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text(f"# {TOPICS[a.topic]} · {date}\n\n")
    src = "据 X 上的报道" if a.source == "x" else "网页/文档"
    with f.open("a") as fh:
        fh.write(f"## {a.title}\n- 来源：{src}　记录者：{a.agent}\n- 链接：{a.url}\n- 要点：{a.summary}\n")
        if a.tags:
            fh.write(f"- 标签：{a.tags}\n")
        if links:
            fh.write("- 资源：" + "；".join(f"{t}={u}" for t, u in links) + "\n")
        fh.write("\n")
    print("已写入", f.relative_to(ROOT))
    index()

def index(_=None):
    lines = ["# 索引（自动生成，勿手改）\n"]
    for t, name in TOPICS.items():
        lines.append(f"## {name}\n")
        folder = ROOT / "topics" / t
        if folder.is_dir():
            for p in sorted(folder.glob("*.md"), reverse=True):
                n = len(re.findall(r"^## ", p.read_text(), re.M))
                lines.append(f"- [{p.stem}](topics/{t}/{p.name})（{n} 条）")
        lines.append("")
    (ROOT / "INDEX.md").write_text("\n".join(lines))

def commit(_=None):
    subprocess.run(["git", "add", "-A"], cwd=ROOT)
    subprocess.run(["git", "-c", "user.name=ai-radar", "-c", "user.email=ai-radar@local",
                    "commit", "-qm", f"radar {datetime.datetime.now():%F %T}"], cwd=ROOT)

def publish(_=None):
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], check=True)
    index(); commit()
    r = subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=ROOT)
    print("已推送，页面稍后刷新" if r.returncode == 0 else "推送失败，请检查 git remote / 登录状态")

def main(argv=None):
    p = argparse.ArgumentParser(description="AI 前沿追踪归档")
    s = p.add_subparsers(required=True)
    x = s.add_parser("add", help="写入一条归档")
    x.set_defaults(fn=add)
    x.add_argument("--topic", required=True, help="eval / knowledge-base / memory / code-review / mcp / skills")
    x.add_argument("--title", required=True)
    x.add_argument("--url", required=True, help="主链接")
    x.add_argument("--summary", required=True)
    x.add_argument("--source", choices=["x", "web"], default="web")
    x.add_argument("--agent", default="unknown")
    x.add_argument("--date")
    x.add_argument("--tags", default="")
    x.add_argument("--link", action="append", default=None, metavar="TYPE=URL",
                   help="可重复。资源链接，类型=URL。类型为小写字母、数字、短横线，可自由扩展")
    s.add_parser("index").set_defaults(fn=index)
    s.add_parser("commit").set_defaults(fn=commit)
    s.add_parser("publish").set_defaults(fn=publish)
    a = p.parse_args(argv)
    a.fn(a)

if __name__ == "__main__":
    main()
