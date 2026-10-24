#!/usr/bin/env python3
"""把 topics/*/*.md 解析成 docs/data.json，并生成静态页 docs/index.html。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = {"eval": "能力评测", "knowledge-base": "知识库", "memory": "记忆",
          "code-review": "代码审查", "mcp-skills": "MCP 与 Skills"}

def parse():
    items = []
    for t in TOPICS:
        for f in sorted((ROOT / "topics" / t).glob("*.md")):
            date = f.stem
            for block in re.split(r"^## ", f.read_text(), flags=re.M)[1:]:
                lines = block.strip().splitlines()
                it = {"topic": t, "date": date, "title": lines[0].strip(),
                      "url": "", "summary": "", "source": "", "agent": "", "tags": []}
                for ln in lines[1:]:
                    if ln.startswith("- 来源："):
                        m = re.match(r"- 来源：(.*?)　记录者：(.*)", ln)
                        if m: it["source"], it["agent"] = m.group(1), m.group(2)
                    elif ln.startswith("- 链接："): it["url"] = ln[5:].strip()
                    elif ln.startswith("- 要点："): it["summary"] = ln[5:].strip()
                    elif ln.startswith("- 标签："): it["tags"] = [x for x in re.split(r"[,，]", ln[5:]) if x.strip()]
                items.append(it)
    return items

HTML = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 前沿追踪</title>
<style>
:root{--bg:#fafaf9;--fg:#1c1917;--mut:#78716c;--card:#fff;--line:#e7e5e4;--acc:#2563eb}
@media(prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#e7e5e4;--mut:#a8a29e;--card:#1c1917;--line:#292524;--acc:#60a5fa}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Segoe UI",sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:28px 16px 80px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);font-size:13px;margin-bottom:18px}
.bar{position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:5;border-bottom:1px solid var(--line)}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.tab{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:3px 12px;font-size:13px;cursor:pointer}
.tab.on{background:var(--acc);border-color:var(--acc);color:#fff}
input{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font-size:14px}
h2.d{font-size:14px;color:var(--mut);margin:26px 0 8px;font-weight:600}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:10px}
.card h3{font-size:15px;margin:0 0 4px}.card h3 a{color:var(--fg);text-decoration:none}.card h3 a:hover{color:var(--acc)}
.card p{margin:4px 0 6px}.meta{font-size:12px;color:var(--mut)}
.tag{display:inline-block;background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:0 6px;margin-right:4px;font-size:11px}
.empty{color:var(--mut);text-align:center;padding:40px 0}
</style></head><body><div class="wrap">
<h1>AI 前沿追踪</h1><div class="sub" id="sub"></div>
<div class="bar"><div class="tabs" id="tabs"></div><input id="q" placeholder="搜索标题、要点、标签…"></div>
<div id="list"></div></div>
<script>
const T=__TOPICS__, D=__DATA__;let cur="all";
const esc=s=>s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const linkify=s=>esc(s).replace(/(https?:\/\/[^\s，。）)]+)/g,'<a href="$1" target="_blank" rel="noopener">$1</a>');
document.getElementById("sub").textContent=`共 ${D.length} 条 · 最近更新 ${D.map(x=>x.date).sort().pop()||"-"}`;
function tabs(){const el=document.getElementById("tabs");el.innerHTML="";
 [["all","全部"],...Object.entries(T)].forEach(([k,n])=>{const c=k==="all"?D.length:D.filter(x=>x.topic===k).length;
  const b=document.createElement("button");b.className="tab"+(cur===k?" on":"");b.textContent=`${n} ${c}`;b.onclick=()=>{cur=k;tabs();render()};el.appendChild(b)})}
function render(){const q=document.getElementById("q").value.trim().toLowerCase();
 const xs=D.filter(x=>(cur==="all"||x.topic===cur)&&(!q||(x.title+x.summary+x.tags.join(" ")).toLowerCase().includes(q)));
 xs.sort((a,b)=>b.date.localeCompare(a.date));const g={};xs.forEach(x=>(g[x.date]=g[x.date]||[]).push(x));
 const el=document.getElementById("list");
 if(!xs.length){el.innerHTML='<div class="empty">没有匹配的内容</div>';return}
 el.innerHTML=Object.entries(g).map(([d,a])=>`<h2 class="d">${d} · ${a.length} 条</h2>`+a.map(x=>`<div class="card">
  <h3>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title)}</a>`:esc(x.title)}</h3>
  <p>${linkify(x.summary)}</p><div class="meta">${T[x.topic]} · ${esc(x.source)} · ${esc(x.agent)} ${x.tags.map(t=>`<span class="tag">${esc(t.trim())}</span>`).join("")}</div></div>`).join("")).join("")}
document.getElementById("q").oninput=render;tabs();render();
</script></body></html>"""

def main():
    items = parse()
    out = ROOT / "docs"; out.mkdir(exist_ok=True)
    (out / "data.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    html = HTML.replace("__TOPICS__", json.dumps(TOPICS, ensure_ascii=False)).replace(
        "__DATA__", json.dumps(items, ensure_ascii=False).replace("</", "<\\/"))
    (out / "index.html").write_text(html)
    (out / ".nojekyll").write_text("")
    print(f"站点已生成：{len(items)} 条")

if __name__ == "__main__":
    main()
