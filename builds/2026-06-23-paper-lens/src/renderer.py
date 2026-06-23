"""HTML viewer generator for Paper Lens."""
import html as html_lib
import json
from datetime import datetime, timezone


def _safe_json(data) -> str:
    """JSON-encode data with angle brackets unicode-escaped to prevent XSS via script injection."""
    return (
        json.dumps(data)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def render_html(papers: list) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = len(papers)
    unread = sum(1 for p in papers if not p.get("is_read"))
    today_count = sum(1 for p in papers if str(p.get("fetched_date", ""))[:10] == today)
    high_count = sum(1 for p in papers if (p.get("relevance_score") or 0) >= 7)

    papers_json = _safe_json(papers)

    css = _build_css()
    js = _build_js(papers_json, today)
    body_html = _build_body(total, unread, today_count, high_count, papers)

    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Paper Lens — Research Paper Inbox</title>",
        css,
        "</head>",
        body_html,
        js,
        "</html>",
    ])


def _build_css() -> str:
    return """<style>
:root{--bg:#0f1117;--surface:#1a1d2e;--surface2:#242740;--border:#2d3158;
  --text:#e2e8f0;--dim:#94a3b8;--green:#4ade80;--amber:#fbbf24;--blue:#60a5fa;
  --purple:#a78bfa;--accent:#818cf8;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:1rem 1.5rem;}
.hrow{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem;}
h1{font-size:1.25rem;font-weight:700;color:var(--accent);}
.stats{display:flex;gap:1rem;font-size:.8rem;color:var(--dim);}
.stats span{color:var(--text);font-weight:600;}
.controls{padding:.75rem 1.5rem;display:flex;gap:.6rem;flex-wrap:wrap;align-items:center;
  background:var(--surface);border-bottom:1px solid var(--border);}
#search{flex:1;min-width:180px;background:var(--surface2);border:1px solid var(--border);
  border-radius:6px;padding:.45rem .75rem;color:var(--text);font-size:.9rem;outline:none;}
#search:focus{border-color:var(--accent);}
.fb{padding:.35rem .7rem;border-radius:20px;border:1px solid var(--border);background:transparent;
  color:var(--dim);font-size:.8rem;cursor:pointer;transition:all .15s;}
.fb:hover{border-color:var(--accent);color:var(--accent);}
.fb.active{background:var(--accent);border-color:var(--accent);color:#fff;}
.cnt{background:var(--surface2);border-radius:10px;padding:.1rem .4rem;font-size:.7rem;margin-left:.2rem;}
main{padding:1.5rem;max-width:960px;margin:0 auto;}
#rc{font-size:.8rem;color:var(--dim);margin-bottom:1rem;}
.papers{display:flex;flex-direction:column;gap:.7rem;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:1rem 1.25rem;transition:border-color .15s;}
.card:hover{border-color:var(--accent);}
.card.read{opacity:.6;}
.ctop{display:flex;align-items:flex-start;justify-content:space-between;gap:.75rem;margin-bottom:.4rem;}
.ptitle{font-size:.95rem;font-weight:600;flex:1;}
.ptitle a{color:var(--text);text-decoration:none;}
.ptitle a:hover{color:var(--accent);}
.rb{flex-shrink:0;font-size:.8rem;font-weight:700;padding:.2rem .5rem;border-radius:12px;}
.rh{background:#14532d;color:var(--green);}
.rm{background:#451a03;color:var(--amber);}
.rl{background:#1c1c1c;color:var(--dim);}
.pmeta{font-size:.75rem;color:var(--dim);margin-bottom:.4rem;}
.tags{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.45rem;}
.tag{font-size:.7rem;padding:.12rem .45rem;border-radius:10px;background:var(--surface2);
  color:var(--dim);border:1px solid var(--border);}
.tm{border-color:#4338ca;color:var(--purple);background:#1e1b4b;}
.psumm{font-size:.85rem;color:var(--dim);line-height:1.55;}
.cfoot{display:flex;align-items:center;justify-content:space-between;margin-top:.7rem;}
.rbtn{font-size:.75rem;padding:.22rem .55rem;border-radius:12px;border:1px solid var(--border);
  background:transparent;color:var(--dim);cursor:pointer;}
.rbtn:hover{border-color:var(--green);color:var(--green);}
.rbtn.ir{border-color:var(--green);color:var(--green);}
.empty{text-align:center;padding:3rem;color:var(--dim);}
.empty h2{font-size:1rem;margin-bottom:.4rem;}
@media(max-width:600px){.hrow{flex-direction:column;align-items:flex-start;}.stats{flex-wrap:wrap;}}
</style>"""


def _build_body(total: int, unread: int, today_count: int, high_count: int, papers: list) -> str:
    esc = html_lib.escape
    return "\n".join([
        "<body>",
        "<header>",
        '  <div class="hrow">',
        "    <h1>Paper Lens</h1>",
        '    <div class="stats">',
        f"      <div>Total <span>{esc(str(total))}</span></div>",
        f"      <div>Unread <span>{esc(str(unread))}</span></div>",
        f"      <div>Today <span>{esc(str(today_count))}</span></div>",
        f"      <div>High Relevance <span>{esc(str(high_count))}</span></div>",
        "    </div>",
        "  </div>",
        "</header>",
        '<div class="controls">',
        '  <input type="text" id="search" placeholder="Search papers..." oninput="af()">',
        f'  <button class="fb active" data-f="all" onclick="sf(this)">All <span class="cnt" id="ca">{esc(str(total))}</span></button>',
        f'  <button class="fb" data-f="unread" onclick="sf(this)">Unread <span class="cnt" id="cu">{esc(str(unread))}</span></button>',
        f'  <button class="fb" data-f="today" onclick="sf(this)">Today <span class="cnt" id="ct">{esc(str(today_count))}</span></button>',
        f'  <button class="fb" data-f="high" onclick="sf(this)">High Relevance <span class="cnt" id="ch">{esc(str(high_count))}</span></button>',
        "</div>",
        "<main>",
        '  <div id="rc"></div>',
        '  <div class="papers" id="pc"></div>',
        '  <div id="es" class="empty" style="display:none"><h2>No papers match</h2><p>Try a different search or filter.</p></div>',
        "  <noscript>",
        "    <ul>",
        *[
            f'      <li><a href="https://arxiv.org/abs/{html_lib.escape(p.get("arxiv_id",""))}">{html_lib.escape(p.get("title",""))}</a></li>'
            for p in papers
        ],
        "    </ul>",
        "  </noscript>",
        "</main>",
        "</body>",
    ])


def _build_js(papers_json: str, today: str) -> str:
    return (
        "<script>\n"
        f"const P={papers_json};\n"
        f'const TD="{today}";\n'
        "let cf='all';\n"
        "function ri(){try{return new Set(JSON.parse(localStorage.getItem('pl-read')||'[]'));}catch{return new Set();}}\n"
        "function si(id){const s=ri();s.add(id);localStorage.setItem('pl-read',JSON.stringify([...s]));}\n"
        "function ir(p){return p.is_read===1||ri().has(p.arxiv_id);}\n"
        "function rc(s){return s>=7?'rb rh':s>=4?'rb rm':'rb rl';}\n"
        "function esc(s){const d=document.createElement('div');d.textContent=String(s??'');return d.innerHTML;}\n"
        "function mk(p){\n"
        "  const rd=ir(p),sc=p.relevance_score??5;\n"
        "  const tgs=[];\n"
        "  if(p.methodology&&p.methodology!=='other')tgs.push('<span class=\"tag tm\">'+esc(p.methodology)+'</span>');\n"
        "  if(p.topic_label)tgs.push('<span class=\"tag\">'+esc(p.topic_label)+'</span>');\n"
        "  const ta=tgs.length?'<div class=\"tags\">'+tgs.join('')+'</div>':'';\n"
        "  const au=p.authors.split(', ').slice(0,3).join(', ')+(p.authors.split(', ').length>3?' et al.':'');\n"
        "  return `<div class=\"card${rd?' read':''}\" data-id=\"${esc(p.arxiv_id)}\" data-s=\"${sc}\" data-d=\"${esc(p.fetched_date)}\" data-r=\"${rd?'1':'0'}\">`\n"
        "    +'<div class=\"ctop\"><div class=\"ptitle\"><a href=\"https://arxiv.org/abs/'+esc(p.arxiv_id)+'\" target=\"_blank\" rel=\"noopener\">'+esc(p.title)+'</a></div>'\n"
        "    +'<span class=\"'+rc(sc)+'\">'+sc+'/10</span></div>'\n"
        "    +'<div class=\"pmeta\">'+esc(au)+' · '+esc(p.published_date)+' · '+esc(p.arxiv_id)+'</div>'\n"
        "    +ta+'<div class=\"psumm\">'+esc(p.summary||'')+'</div>'\n"
        "    +'<div class=\"cfoot\"><button class=\"rbtn'+(rd?' ir':'')+\"\\\" onclick=\\\"mr('\"+(p.arxiv_id).replace(/'/g,\"\\\\'\")+\"',this)\\\">\"+(rd?'✓ Read':'Mark as read')+'</button></div>'\n"
        "    +'</div>';\n"
        "}\n"
        "function mr(id,btn){si(id);const c=btn.closest('.card');c.dataset.r='1';c.classList.add('read');btn.textContent='✓ Read';btn.classList.add('ir');af();}\n"
        "function sf(btn){document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));btn.classList.add('active');cf=btn.dataset.f;af();}\n"
        "function af(){\n"
        "  const q=document.getElementById('search').value.toLowerCase();\n"
        "  const rids=ri();\n"
        "  const vis=P.filter(p=>{\n"
        "    const rd=p.is_read===1||rids.has(p.arxiv_id);\n"
        "    if(cf==='unread'&&rd)return false;\n"
        "    if(cf==='today'&&p.fetched_date.slice(0,10)!==TD)return false;\n"
        "    if(cf==='high'&&(p.relevance_score??0)<7)return false;\n"
        "    if(q){const h=(p.title+' '+(p.summary||'')+' '+(p.topic_label||'')+' '+p.authors).toLowerCase();if(!h.includes(q))return false;}\n"
        "    return true;\n"
        "  });\n"
        "  document.getElementById('pc').innerHTML=vis.map(mk).join('');\n"
        "  document.getElementById('rc').textContent=vis.length+' of '+P.length+' papers';\n"
        "  document.getElementById('es').style.display=vis.length===0?'block':'none';\n"
        "}\n"
        "af();\n"
        "</script>"
    )
