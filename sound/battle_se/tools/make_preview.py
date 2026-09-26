# -*- coding: utf-8 -*-
"""Resources/BattleSE の WAV を埋め込んだ確認用ページ（../preview.html）を作る。1ファイルで再生できる。"""
import os
import json
import base64
import wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WAV = os.path.join(HERE, "..", "Resources", "BattleSE")
meta = json.load(open(os.path.join(HERE, "se_list.json"), encoding="utf-8"))

items = []
for m in meta:
    path = os.path.join(WAV, m["name"] + ".wav")
    raw = open(path, "rb").read()
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768
    b = np.array_split(np.abs(x), 90)
    peaks = [round(float(c.max()), 3) if len(c) else 0 for c in b]
    items.append(dict(m, peaks=peaks, data=base64.b64encode(raw).decode()))

groups = []
for it in items:
    if it["group"] not in groups:
        groups.append(it["group"])

html = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>バトル攻撃SE</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#1f2328;--sub:#5d6470;--line:#e2e0da;--accent:#c2410c;--wave:#94a3b8;--wave-on:#c2410c;--chip:#f1efe9}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171b;--card:#1e2126;--ink:#e8e6e1;--sub:#9aa3ad;--line:#2e3239;--accent:#fb923c;--wave:#4b5563;--wave-on:#fb923c;--chip:#262a30}}
:root[data-theme=dark]{--bg:#15171b;--card:#1e2126;--ink:#e8e6e1;--sub:#9aa3ad;--line:#2e3239;--accent:#fb923c;--wave:#4b5563;--wave-on:#fb923c;--chip:#262a30}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 system-ui,-apple-system,"Hiragino Sans","Yu Gothic UI",sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px}
.wrap{max-width:1100px;margin:0 auto}
h1{font-size:18px;margin:0 0 8px}
.bar{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;color:var(--sub);font-size:13px}
.bar input[type=search]{flex:1 1 200px;min-width:0;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);font:inherit}
.bar label{display:flex;gap:6px;align-items:center;white-space:nowrap}
nav{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
nav a{font-size:12px;padding:3px 9px;border-radius:999px;background:var(--chip);color:var(--ink);text-decoration:none}
main{padding:8px 16px 40px}
h2{font-size:15px;margin:22px 0 8px;display:flex;align-items:center;gap:10px}
h2 button{font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:8px}
.se{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 10px;display:grid;grid-template-columns:40px 1fr;gap:4px 10px;align-items:start}
.se.playing{border-color:var(--accent)}
.play{grid-row:span 3;width:40px;height:40px;border-radius:50%;border:none;background:var(--accent);color:#fff;font-size:15px;cursor:pointer}
.name{font:600 13px ui-monospace,SFMono-Regular,Consolas,monospace;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;word-break:break-all}
.name small{font:12px system-ui;color:var(--sub)}
.loop{font:11px system-ui;color:var(--accent);border:1px solid var(--accent);border-radius:4px;padding:0 4px}
.desc{font-size:13px}
.use{font-size:12px;color:var(--sub)}
canvas{grid-column:1/-1;width:100%;height:28px;display:block}
button.small{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:3px 9px;cursor:pointer;font:inherit}
.hidden{display:none}
@media (max-width:600px){header{position:static}}
</style></head><body>
<header><div class="wrap">
<h1>バトル攻撃SE（__COUNT__ 音）</h1>
<div class="bar">
<input type="search" id="q" placeholder="名前・説明・使う所で絞り込み（例：命中、魔法、ループ）">
<label>音量 <input type="range" id="vol" min="0" max="1" step="0.01" value="0.8"></label>
<label><input type="checkbox" id="jit"> 鳴らすたびに少し揺らす（Unity の BattleSE と同じ）</label>
<button class="small" id="stop">すべて止める（Esc）</button>
</div>
<nav id="nav"></nav>
</div></header>
<main class="wrap" id="main"></main>
<script>
const SE = __DATA__;
const GROUPS = __GROUPS__;
let ctx, master; const buffers = {}; const playing = new Map();
function audio(){ if(!ctx){ ctx = new (window.AudioContext||window.webkitAudioContext)(); master = ctx.createGain(); master.connect(ctx.destination); setVol(); } return ctx; }
function setVol(){ if(master) master.gain.value = +document.getElementById('vol').value; }
async function buf(s){ if(!buffers[s.name]){ const b = Uint8Array.from(atob(s.data), c=>c.charCodeAt(0)).buffer; buffers[s.name] = await audio().decodeAudioData(b); } return buffers[s.name]; }
function stop(name){ const p = playing.get(name); if(p){ try{p.src.stop();}catch(e){} playing.delete(name); p.el.classList.remove('playing'); p.btn.textContent='▶'; } }
function stopAll(){ [...playing.keys()].forEach(stop); }
async function play(s, el, btn){
  audio(); if(ctx.state==='suspended') await ctx.resume();
  if(s.loop && playing.has(s.name)){ stop(s.name); return; }
  const src = ctx.createBufferSource(); src.buffer = await buf(s);
  const g = ctx.createGain(); src.connect(g); g.connect(master);
  if(document.getElementById('jit').checked){ src.playbackRate.value = 1 + (Math.random()*2-1)*0.04; g.gain.value = 1 - Math.random()*0.1; }
  src.loop = !!s.loop;
  if(!s.loop) stop(s.name);
  src.start(); el.classList.add('playing'); btn.textContent = s.loop ? '■' : '▶';
  playing.set(s.name, {src, el, btn});
  src.onended = ()=>{ if(playing.get(s.name)?.src===src){ playing.delete(s.name); el.classList.remove('playing'); btn.textContent='▶'; } };
  animate(s, el, src);
}
function drawWave(c, s, pos){
  const r = c.getBoundingClientRect(), d = devicePixelRatio||1; c.width = r.width*d; c.height = r.height*d;
  const g = c.getContext('2d'), cs = getComputedStyle(document.documentElement), n = s.peaks.length, w = c.width/n;
  for(let i=0;i<n;i++){ const h = Math.max(1, s.peaks[i]*c.height); g.fillStyle = (pos!=null && i/n<=pos) ? cs.getPropertyValue('--wave-on') : cs.getPropertyValue('--wave'); g.fillRect(i*w+0.5, (c.height-h)/2, Math.max(1,w-1), h); }
}
function animate(s, el, src){
  const c = el.querySelector('canvas'), t0 = ctx.currentTime, rate = src.playbackRate.value;
  const tick = ()=>{ if(playing.get(s.name)?.src!==src){ drawWave(c, s); return; } const p = ((ctx.currentTime-t0)*rate/s.sec); drawWave(c, s, s.loop ? p%1 : p); requestAnimationFrame(tick); };
  tick();
}
const main = document.getElementById('main'), nav = document.getElementById('nav'); const cards = [];
GROUPS.forEach((gname, gi)=>{
  const list = SE.filter(s=>s.group===gname);
  const h = document.createElement('h2'); h.id = 'g'+gi; h.innerHTML = `${gname} <small style="color:var(--sub);font-weight:400">${list.length} 音</small>`;
  const all = document.createElement('button'); all.className='small'; all.textContent='順に鳴らす';
  all.onclick = async ()=>{ for(const s of list.filter(s=>!s.loop)){ const card = cards.find(c=>c.s===s); if(card.el.classList.contains('hidden')) continue; card.el.scrollIntoView({block:'nearest'}); await play(s, card.el, card.btn); await new Promise(r=>setTimeout(r, Math.min(s.sec,1.6)*1000+250)); } };
  h.appendChild(all); main.appendChild(h);
  const a = document.createElement('a'); a.href='#g'+gi; a.textContent = gname; nav.appendChild(a);
  const grid = document.createElement('div'); grid.className='grid'; main.appendChild(grid);
  list.forEach(s=>{
    const el = document.createElement('div'); el.className='se';
    el.innerHTML = `<button class="play" aria-label="${s.name} を再生">▶</button><div class="name">${s.name}<small>${s.sec.toFixed(2)}秒</small>${s.loop?'<span class="loop">ループ</span>':''}</div><div class="desc">${s.desc}</div><div class="use">使う所：${s.use}</div><canvas></canvas>`;
    const btn = el.querySelector('.play'); btn.onclick = ()=>play(s, el, btn);
    el.querySelector('canvas').onclick = ()=>play(s, el, btn);
    grid.appendChild(el); cards.push({s, el, btn});
  });
});
function redraw(){ cards.forEach(c=>drawWave(c.el.querySelector('canvas'), c.s)); }
requestAnimationFrame(redraw); addEventListener('resize', redraw);
document.getElementById('vol').oninput = setVol;
document.getElementById('stop').onclick = stopAll;
addEventListener('keydown', e=>{ if(e.key==='Escape') stopAll(); });
document.getElementById('q').oninput = e=>{
  const q = e.target.value.trim().toLowerCase();
  cards.forEach(c=>{ const t = (c.s.name+c.s.desc+c.s.use+c.s.group+(c.s.loop?'ループ loop':'')).toLowerCase(); c.el.classList.toggle('hidden', !!q && !q.split(/\\s+/).every(w=>t.includes(w))); });
  document.querySelectorAll('.grid').forEach(g=>{ const h = g.previousElementSibling; const any = [...g.children].some(x=>!x.classList.contains('hidden')); g.classList.toggle('hidden',!any); h.classList.toggle('hidden',!any); });
};
</script></body></html>
"""
html = html.replace("__DATA__", json.dumps(items, ensure_ascii=False)).replace("__GROUPS__", json.dumps(groups, ensure_ascii=False)).replace("__COUNT__", str(len(items)))
out = os.path.join(HERE, "..", "preview.html")
open(out, "w", encoding="utf-8").write(html)
print(f"{os.path.normpath(out)}（{os.path.getsize(out) // 1024} KB）")

# ---------------- README ----------------
rows = {}
for m in meta:
    rows.setdefault(m["group"], []).append(f"| `{m['name']}` | {m['sec']:.2f}秒{'（ループ）' if m['loop'] else ''} | {m['desc']} | {m['use']} |")
lists = "\n\n".join(f"### {g}（{len(r)} 音）\n\n| 名前 | 長さ | 音 | 使う所 |\n|---|---|---|---|\n" + "\n".join(r) for g, r in rows.items())
readme = f"""# バトルの攻撃 SE（{len(meta)} 音）

`preview.html` をブラウザで開くと、全部の音を聞き比べられます（音は html の中に入っているので、このファイルだけで再生できます）。
このファイルは `tools/make_preview.py` が自動生成します。

## 形式

- WAV（44.1kHz・16bit・モノラル）。`Resources/BattleSE/` に入っています
- 音量は種類ごとにそろえてあります（振り音は小さめ、命中・爆発は大きめ）。ピークは -1dB 以下
- 名前の末尾が `_Loop` の音はループ用です（頭とおしりがつながるように作ってあります）。Inspector で Loop にするか、`BattleSE.PlayLoop` で鳴らしてください

## 使い方（Unity）

1. このフォルダ（`battle_se`）を Assets の下に置く（`Resources` フォルダはそのまま。名前で読み込むのに使います）
2. スクリプトから名前で鳴らす：

```csharp
BattleSE.Play("Fina_Hit_A");                               // 2D で鳴らす
BattleSE.Play("Enemy_Stomp", transform.position);          // その位置で鳴らす
var h = BattleSE.PlayLoop("Flamethrower_Loop", transform); // ループ（ついていく）
BattleSE.Stop(h);                                          // ループを止める
BattleSE.PlayMagic("Impact", "Ice");                       // Magic_Impact_Ice
```

   - `BattleSE` はシーンに置かなくても、最初に鳴らしたときに自動で作られます。置いておくと Inspector で全体の音量・3D の割合・AudioMixer の出力先などを変えられます
   - 鳴らすたびに高さ（±4%）と音量を少し揺らすので、同じ音の連打が機械的に聞こえません。多段ヒットで同じ音が 0.03 秒以内に重なったときは2回目を鳴らしません
3. モーションのイベントで鳴らす：`SEEventMap` を Animator と同じ GameObject に付け、「イベント名 → SE 名」を並べる
   - 魔法陣（`MagicCircleRig`）は、コンポーネント右上の ⋮ →「魔法陣の既定を入れる」で、Appear / Charge / Fire / Impact / BeamStart / PillarStart に音が付きます。玉の音は `MagicCircleRig` の属性（Element）に合わせて切り替わります
   - `Fire:3` のような番号付きのイベントは `Fire` と書けば一致します。**Log Events** をオンにすると、届いたイベント名がコンソールに出ます

## 音の一覧

{lists}

## 作り直し方

録音素材は使わず、`tools/make_se.py`（音の作り方）と `tools/dsp.py`（道具）で一から合成しています。Python 3 ＋ numpy ＋ scipy で動きます。

```
pip install numpy scipy
python tools/make_se.py              # 全部作り直す（Resources/BattleSE/ に上書き）
python tools/make_se.py Fina_Hit     # 名前の一部を指定して作り直す
python tools/make_preview.py         # preview.html と README.md を作り直す
```

## 注意

- 音は数値で確認しています（波形・周波数の形、つなぎ目、音量）が、実際に耳で聞いての調整はしていません。イメージと違う音があれば、名前と「もっと重く」「短く」などを教えてください
- `BattleSE.cs`・`SEEventMap.cs` は Unity での動作をまだ確認できていません。エラーが出たら文面を教えてください
"""
open(os.path.join(HERE, "..", "README.md"), "w", encoding="utf-8").write(readme)
print("README.md")
