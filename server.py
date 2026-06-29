# -*- coding: utf-8 -*-
"""
みんレポ 差枚ランキングビューア (ローカルアプリ)

min-repo.com からホール名で検索し、その店の「全台 差枚ランキング」を
台番号付きで最新10日分まとめて表示するローカルWebアプリ。

使い方:
    python server.py
ブラウザが自動で開きます (http://127.0.0.1:8765)。

追加ライブラリ不要 (Python標準ライブラリのみ)。
"""

import os
import re
import gzip
import json
import time
import html as ihtml
import threading
import webbrowser
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8765
BASE = "https://min-repo.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
# クエリ付きページの取得に必要なアンチスクレイプ用Cookie (ベースページのJSが設定する値)
FALLBACK_D2 = "vl+ql6ffB9gLcUM60IiB2g=="
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
REQUEST_DELAY = 0.25       # 連続リクエスト間の待機(サーバ負荷配慮)
CACHE_TTL = 60 * 60 * 6    # レポートキャッシュ有効期間(秒)

_d2_cache = {"value": None}
_last_fetch = [0.0]
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# 取得まわり
# ---------------------------------------------------------------------------
def http_get(url, use_cookie=False):
    with _lock:
        wait = REQUEST_DELAY - (time.time() - _last_fetch[0])
        if wait > 0:
            time.sleep(wait)
        _last_fetch[0] = time.time()
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ja,en;q=0.8",
        "Accept-Encoding": "gzip",
    }
    if use_cookie:
        headers["Cookie"] = "_d2=%s" % get_d2()
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    return data.decode("utf-8", "replace")


def get_d2():
    """ベースレポートページのインラインJSから _d2 トークンを抽出(キャッシュ)。"""
    if _d2_cache["value"]:
        return _d2_cache["value"]
    try:
        # 適当な既知レポートからトークンを採取
        html = http_get(BASE + "/1740665/")
        m = re.search(r"\$\.cookie\(\s*['\"]_d2['\"]\s*,\s*['\"]([^'\"]+)['\"]", html)
        if m:
            _d2_cache["value"] = m.group(1)
    except Exception:
        pass
    if not _d2_cache["value"]:
        _d2_cache["value"] = FALLBACK_D2
    return _d2_cache["value"]


def _strip(x):
    return ihtml.unescape(re.sub(r"<[^>]+>", "", x)).strip()


# ---------------------------------------------------------------------------
# パース
# ---------------------------------------------------------------------------
def search_halls(query):
    """ホール名で検索 → [{name, slug}] を返す。"""
    url = BASE + "/?" + urllib.parse.urlencode({"s": query})
    html = http_get(url, use_cookie=True)
    seen, out = set(), []
    for m in re.finditer(r'href="https://min-repo\.com/tag/([^"/]+)/"', html):
        slug = m.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        name = urllib.parse.unquote(slug)
        out.append({"name": name, "slug": slug})
    return out


def hall_days(slug):
    """ホールの日別一覧(新しい順) → [{id, date, total, avg, avgg, summary}]。"""
    url = "%s/tag/%s/" % (BASE, slug)
    html = http_get(url, use_cookie=True)
    days = []
    for tr in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        m = re.search(r'href="https://min-repo\.com/(\d+)/"[^>]*>([^<]+)</a>', tr)
        if not m:
            continue
        tds = [_strip(t) for t in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(tds) < 4:
            continue
        days.append({
            "id": m.group(1),
            "date": m.group(2).strip(),
            "total": tds[1] if len(tds) > 1 else "",
            "avg": tds[2] if len(tds) > 2 else "",
            "avgg": tds[3] if len(tds) > 3 else "",
            "summary": tds[4] if len(tds) > 4 else "",
        })
    return days


def report_ranking(post_id):
    """1日分の全台差枚ランキング(差枚順) → [{dai, kishu, samai, game, deri}]。"""
    cache = os.path.join(CACHE_DIR, "rep_%s.json" % post_id)
    if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < CACHE_TTL:
        try:
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    url = "%s/%s/?kishu=all" % (BASE, post_id)
    html = http_get(url, use_cookie=True)
    i = html.find("全台")
    seg = html[i:] if i >= 0 else html
    j = seg.find("<table>")
    k = seg.find("</table>", j)
    table = seg[j:k] if j >= 0 else ""
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", table, re.S):
        if "<th" in tr:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 5:
            continue
        rows.append({
            "kishu": _strip(tds[0]),
            "dai": _strip(tds[1]),
            "samai": _strip(tds[2]),
            "game": _strip(tds[3]),
            "deri": _strip(tds[4]),
        })
    try:
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)
    except Exception:
        pass
    return rows


# ---------------------------------------------------------------------------
# HTTP ハンドラ
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        try:
            if path == "/" or path == "/index.html":
                self._send(200, INDEX_HTML, "text/html; charset=utf-8")
            elif path == "/api/search":
                q = (qs.get("q") or [""])[0].strip()
                if not q:
                    self._send(200, {"halls": []})
                else:
                    self._send(200, {"halls": search_halls(q)})
            elif path == "/api/hall":
                slug = (qs.get("slug") or [""])[0]
                days = int((qs.get("days") or ["10"])[0])
                d = hall_days(slug)
                name = urllib.parse.unquote(slug)
                self._send(200, {"hall": name, "days": d[:days]})
            elif path == "/api/report":
                pid = (qs.get("id") or [""])[0]
                self._send(200, {"id": pid, "rows": report_ranking(pid)})
            else:
                self._send(404, {"error": "not found"})
        except Exception as e:
            self._send(500, {"error": str(e)})


# ---------------------------------------------------------------------------
# フロントエンド (単一HTML)
# ---------------------------------------------------------------------------
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>みんレポ 差枚ランキングビューア</title>
<style>
  :root{--bg:#0f1220;--panel:#181c2e;--line:#2a3050;--fg:#e8ecff;--mut:#8b93b8;
        --pos:#ff5d6c;--neg:#3da9fc;--accent:#ffc24b;}
  *{box-sizing:border-box;}
  body{margin:0;font-family:"Segoe UI","Hiragino Kaku Gothic ProN","Meiryo",sans-serif;
       background:var(--bg);color:var(--fg);}
  header{padding:16px 20px;border-bottom:1px solid var(--line);position:sticky;top:0;
         background:linear-gradient(180deg,#191d33,#13162640);backdrop-filter:blur(6px);z-index:5;}
  h1{font-size:18px;margin:0 0 4px;}
  .sub{color:var(--mut);font-size:12px;}
  .wrap{padding:18px 20px;max-width:1500px;margin:0 auto;}
  .searchbar{display:flex;gap:8px;margin-bottom:14px;}
  input[type=text]{flex:1;padding:11px 14px;border-radius:10px;border:1px solid var(--line);
        background:var(--panel);color:var(--fg);font-size:15px;}
  button{padding:11px 18px;border-radius:10px;border:1px solid var(--line);
        background:var(--accent);color:#1a1400;font-weight:700;cursor:pointer;font-size:14px;}
  button.ghost{background:var(--panel);color:var(--fg);font-weight:500;}
  button:hover{filter:brightness(1.08);}
  .halls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;}
  .halls button{background:var(--panel);color:var(--fg);font-weight:500;border-color:var(--line);}
  .tabs{display:flex;gap:6px;margin:14px 0;flex-wrap:wrap;}
  .tabs button{background:var(--panel);color:var(--mut);font-weight:600;}
  .tabs button.on{background:var(--accent);color:#1a1400;}
  .status{color:var(--mut);font-size:13px;margin:10px 0;}
  table{border-collapse:collapse;width:100%;font-size:13px;}
  th,td{border:1px solid var(--line);padding:5px 8px;text-align:right;white-space:nowrap;}
  th{background:#1d2238;color:var(--mut);position:sticky;top:0;}
  td.l,th.l{text-align:left;}
  th.sortable{cursor:pointer;user-select:none;}
  th.sortable:hover{color:var(--fg);}
  th.sortable.act{color:var(--accent);}
  .arw{font-size:10px;margin-left:2px;}
  td.kishu{white-space:normal;min-width:150px;max-width:240px;line-height:1.3;}
  .hint{font-size:11px;color:var(--mut);margin:2px 0 10px;}
  .pos{color:var(--pos);font-weight:700;}
  .neg{color:var(--neg);}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;
        margin-bottom:14px;}
  .daygrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(460px,1fr));gap:14px;}
  .dhead{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;}
  .dhead .d{font-weight:700;font-size:15px;}
  .dhead .t{font-size:12px;color:var(--mut);}
  .scroll{max-height:520px;overflow:auto;border-radius:8px;}
  .matrix-wrap{overflow:auto;max-height:75vh;border:1px solid var(--line);border-radius:10px;}
  .matrix td.dai{position:sticky;left:0;background:#1d2238;font-weight:700;z-index:2;}
  .matrix th.dai{position:sticky;left:0;background:#1d2238;z-index:3;}
  /* 合計列を右端に固定（横スクロールしても常に見える） */
  .matrix td.tot,.matrix th.tot{position:sticky;background:#1d2238;text-align:right;
        width:80px;min-width:80px;max-width:80px;font-variant-numeric:tabular-nums;}
  .matrix td.tot{z-index:2;}
  .matrix th.tot{z-index:4;}
  .matrix .tot10{right:0;}
  .matrix .tot7{right:80px;}
  .matrix .tot3{right:160px;border-left:2px solid var(--accent);}
  .cell{font-variant-numeric:tabular-nums;}
  .muted{color:var(--mut);}
  .legend{font-size:11px;color:var(--mut);margin:6px 0 0;}
  a{color:var(--accent);}
</style>
</head>
<body>
<header>
  <h1>🎰 みんレポ 差枚ランキングビューア</h1>
  <div class="sub">ホール名で検索 → 全台差枚ランキングを台番付きで最新10日分表示 (データ元: min-repo.com)</div>
</header>
<div class="wrap">
  <div class="searchbar">
    <input id="q" type="text" placeholder="ホール名を入力 (例: マルハン / センター)" autofocus>
    <button id="go">検索</button>
  </div>
  <div id="halls" class="halls"></div>
  <div id="status" class="status"></div>
  <div id="result"></div>
</div>

<script>
const $ = s => document.querySelector(s);
const esc = s => (s||"").replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));

function numClass(s){
  const n = parseInt((s||"").replace(/[^\-0-9]/g,""),10);
  if(isNaN(n)) return "";
  return n>0?"pos":(n<0?"neg":"muted");
}
function fmtSamai(s){
  const n = parseInt((s||"").replace(/[^\-0-9]/g,""),10);
  if(isNaN(n)) return esc(s);
  return (n>0?"+":"")+n.toLocaleString();
}

async function api(path){
  const r = await fetch(path);
  if(!r.ok) throw new Error((await r.json()).error||r.statusText);
  return r.json();
}

let DAYS=[], REPORTS={};
let dailySort={key:"samai",dir:"desc"};   // 差枚順がデフォルト
let matrixSort={key:"total",dir:"desc"};  // 10日計順がデフォルト

function parseNum(s){const n=parseInt((s||"").replace(/[^\-0-9]/g,""),10);return isNaN(n)?null:n;}
function sortRows(rows,key,dir){
  const arr=[...rows];
  arr.sort((a,b)=>{
    if(key==="kishu"){const x=a.kishu||"",y=b.kishu||"";return dir==="asc"?x.localeCompare(y,"ja"):y.localeCompare(x,"ja");}
    const x=parseNum(a[key]),y=parseNum(b[key]);
    if(x==null&&y==null)return 0; if(x==null)return 1; if(y==null)return -1;  // 空欄は末尾
    return dir==="asc"?x-y:y-x;
  });
  return arr;
}
function arw(key,sort){return sort.key===key?`<span class="arw">${sort.dir==="asc"?"▲":"▼"}</span>`:"";}

$("#go").onclick = doSearch;
$("#q").addEventListener("keydown", e=>{ if(e.key==="Enter") doSearch(); });

async function doSearch(){
  const q = $("#q").value.trim();
  if(!q) return;
  $("#halls").innerHTML=""; $("#result").innerHTML="";
  $("#status").textContent = "検索中…";
  try{
    const {halls} = await api("/api/search?q="+encodeURIComponent(q));
    $("#status").textContent = halls.length ? halls.length+" 件のホールが見つかりました。選択してください:" : "該当するホールがありません。";
    $("#halls").innerHTML = halls.map(h=>`<button data-slug="${encodeURIComponent(h.slug)}">${esc(h.name)}</button>`).join("");
    $("#halls").querySelectorAll("button").forEach(b=>{
      b.onclick = ()=> loadHall(b.dataset.slug, b.textContent);
    });
  }catch(e){ $("#status").textContent = "エラー: "+e.message; }
}

async function loadHall(slug, name){
  $("#result").innerHTML=""; REPORTS={}; DAYS=[];
  $("#status").textContent = `「${name}」の日別一覧を取得中…`;
  try{
    const {days} = await api("/api/hall?slug="+slug+"&days=10");
    DAYS = days;
    if(!days.length){ $("#status").textContent="この店のデータが見つかりませんでした。"; return; }
    $("#status").innerHTML = `<b>${esc(name)}</b> 最新 ${days.length} 日分の全台ランキングを取得中… <span id="prog"></span>`;
    renderTabs(name);
    // 各日のランキングを並行取得
    let done=0;
    await Promise.all(days.map(async d=>{
      try{ const r = await api("/api/report?id="+d.id); r.rows.forEach((x,i)=>x._rank=i+1); REPORTS[d.id]=r.rows; }
      catch(e){ REPORTS[d.id]=[]; }
      done++; const p=$("#prog"); if(p) p.textContent=`(${done}/${days.length})`;
    }));
    $("#status").innerHTML = `<b>${esc(name)}</b> 最新 ${days.length} 日分を表示中`;
    showTab(currentTab);
  }catch(e){ $("#status").textContent = "エラー: "+e.message; }
}

let currentTab = "daily";
function renderTabs(name){
  const html = `<div class="tabs">
      <button data-t="daily">📋 日別ランキング</button>
      <button data-t="matrix">📊 台番×日 差枚マトリクス</button>
    </div><div id="tabbody"></div>`;
  $("#result").innerHTML = html;
  $("#result").querySelectorAll(".tabs button").forEach(b=>{
    b.onclick=()=>{ currentTab=b.dataset.t; showTab(currentTab); };
  });
}
function showTab(t){
  $("#result").querySelectorAll(".tabs button").forEach(b=>b.classList.toggle("on",b.dataset.t===t));
  if(t==="daily") renderDaily(); else renderMatrix();
}

function dailyHeader(){
  const h=(k,label,cls)=>`<th class="sortable ${cls||''} ${dailySort.key===k?'act':''}" data-k="${k}">${label}${arw(k,dailySort)}</th>`;
  return `<tr><th>順</th>${h('dai','台番')}${h('kishu','機種','l')}${h('samai','差枚')}${h('game','G数')}${h('deri','出率')}</tr>`;
}
function renderDaily(){
  const body = $("#tabbody");
  body.innerHTML = `<div class="hint">列見出し（台番・機種・差枚 など）をクリックすると全日まとめて並び替わります。「順」は各日の差枚順位です。</div>`
    + `<div class="daygrid">` + DAYS.map(d=>{
    const rows = sortRows(REPORTS[d.id]||[], dailySort.key, dailySort.dir);
    const trs = rows.map(r=>`<tr>
        <td>${r._rank||""}</td>
        <td><b>${esc(r.dai)}</b></td>
        <td class="l kishu">${esc(r.kishu)}</td>
        <td class="${numClass(r.samai)}">${fmtSamai(r.samai)}</td>
        <td>${esc(r.game)}</td>
        <td>${esc(r.deri)}</td></tr>`).join("");
    return `<div class="card">
        <div class="dhead"><span class="d">${esc(d.date)}</span>
          <span class="t">総差枚 <b class="${numClass(d.total)}">${esc(d.total)}</b> ／ 平均 ${esc(d.avg)} ／ 平均G ${esc(d.avgg)}</span></div>
        <div class="scroll"><table>
          ${dailyHeader()}
          ${trs || '<tr><td colspan="6" class="muted">データなし</td></tr>'}
        </table></div></div>`;
  }).join("") + `</div>`;
  body.querySelectorAll("th.sortable").forEach(th=>{
    th.onclick=()=>{
      const k=th.dataset.k;
      if(dailySort.key===k) dailySort.dir = dailySort.dir==="asc"?"desc":"asc";
      else dailySort={key:k, dir:(k==="kishu"||k==="dai")?"asc":"desc"};
      renderDaily();
    };
  });
}

function renderMatrix(){
  // 台番 を行、日付を列にした差枚ピボット
  const dais = new Set();
  DAYS.forEach(d=> (REPORTS[d.id]||[]).forEach(r=> dais.add(r.dai)));
  let daiList = [...dais];
  // 台番→機種(最新日優先)、台番→日別差枚
  const lookup = {};   // dai -> {id -> samaiNum}
  const kishuOf = {};  // dai -> kishu
  DAYS.forEach(d=>{
    (REPORTS[d.id]||[]).forEach(r=>{
      lookup[r.dai] = lookup[r.dai]||{};
      lookup[r.dai][d.id] = parseInt((r.samai||"").replace(/[^\-0-9]/g,""),10);
      if(!kishuOf[r.dai]) kishuOf[r.dai]=r.kishu;
    });
  });
  // 直近N日分の合計（データのある日のみ加算。1日もなければ null）
  const sumOf=(dn,list)=>{let s=0,has=false;list.forEach(d=>{const v=lookup[dn]?.[d.id];if(v!=null&&!isNaN(v)){s+=v;has=true;}});return has?s:null;};
  const tot3={}, tot7={}, tot10={};
  daiList.forEach(dn=>{ tot3[dn]=sumOf(dn,DAYS.slice(0,3)); tot7[dn]=sumOf(dn,DAYS.slice(0,7)); tot10[dn]=sumOf(dn,DAYS); });

  const ms=matrixSort;
  const totMap={total:tot10, total7:tot7, total3:tot3};
  daiList.sort((a,b)=>{
    if(ms.key==="kishu"){const x=kishuOf[a]||"",y=kishuOf[b]||"";return ms.dir==="asc"?x.localeCompare(y,"ja"):y.localeCompare(x,"ja");}
    let x,y;
    if(ms.key==="dai"){x=parseInt(a)||0;y=parseInt(b)||0;}
    else if(totMap[ms.key]){x=totMap[ms.key][a];y=totMap[ms.key][b];}
    else if(ms.key.indexOf("day:")===0){const id=ms.key.slice(4);x=lookup[a]?.[id];y=lookup[b]?.[id];}
    if(x==null||isNaN(x)){ if(y==null||isNaN(y))return 0; return 1; }   // 空欄は末尾
    if(y==null||isNaN(y))return -1;
    return ms.dir==="asc"?x-y:y-x;
  });

  const mh=(k,label,cls)=>`<th class="sortable ${cls||''} ${ms.key===k?'act':''}" data-k="${k}">${label}${arw(k,ms)}</th>`;
  const head = `<tr>${mh('dai','台番','dai')}${mh('kishu','機種(直近)','l')}`
      + DAYS.map(d=>mh('day:'+d.id, esc(d.date))).join("")
      + mh('total3','3日計','tot tot3') + mh('total7','7日計','tot tot7') + mh('total','10日計','tot tot10')
      + `</tr>`;
  const totCell=(v,c2)=>{
    if(v==null) return `<td class="tot ${c2} muted">-</td>`;
    const c=v>0?"pos":(v<0?"neg":"muted");
    return `<td class="tot ${c2} ${c}"><b>${(v>0?"+":"")+v.toLocaleString()}</b></td>`;
  };
  const body = daiList.map(dn=>{
    const cells = DAYS.map(d=>{
      const v = lookup[dn]?.[d.id];
      if(v==null||isNaN(v)) return `<td class="muted">-</td>`;
      const cls = v>0?"pos":(v<0?"neg":"muted");
      const bg = v>0 ? `background:rgba(255,93,108,${Math.min(Math.abs(v)/4000,0.5)})`
                     : (v<0?`background:rgba(61,169,252,${Math.min(Math.abs(v)/4000,0.5)})`:"");
      return `<td class="cell ${cls}" style="${bg}">${(v>0?"+":"")+v.toLocaleString()}</td>`;
    }).join("");
    return `<tr><td class="dai">${esc(dn)}</td><td class="l">${esc(kishuOf[dn]||"")}</td>${cells}`
      + totCell(tot3[dn],'tot3') + totCell(tot7[dn],'tot7') + totCell(tot10[dn],'tot10') + `</tr>`;
  }).join("");
  $("#tabbody").innerHTML = `<div class="hint">同じ台番(座席)の差枚を横断比較。右端に直近 3日計・7日計・10日計 を固定表示（横スクロールしても常時表示）。列見出し（台番・機種・各日・各合計）クリックで並び替え。色が濃いほど絶対値が大きい。</div>`
    + `<div class="matrix-wrap"><table class="matrix"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
  $("#tabbody").querySelectorAll("th.sortable").forEach(th=>{
    th.onclick=()=>{
      const k=th.dataset.k;
      if(matrixSort.key===k) matrixSort.dir = matrixSort.dir==="asc"?"desc":"asc";
      else matrixSort={key:k, dir:(k==="kishu"||k==="dai")?"asc":"desc"};
      renderMatrix();
    };
  });
}
</script>
</body>
</html>
"""


def main():
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    url = "http://%s:%d/" % (HOST, PORT)
    print("みんレポ 差枚ランキングビューアを起動しました:", url)
    print("終了するには Ctrl+C を押してください。")
    try:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました。")
        srv.shutdown()


if __name__ == "__main__":
    main()
