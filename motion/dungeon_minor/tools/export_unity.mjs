// ダンジョン雑魚のモーションを Unity 用アセットに書き出す。
//
//   node <このフォルダ>/export_unity.mjs
//
// ../dungeon_minor.html の ==POSE-BEGIN== 〜 ==POSE-END== にあるクリップ定義をそのまま使い、
// ../unity/<体の種類>/<体の種類>_<クリップ名>.anim を出力する（追加パッケージ不要）。
// クリップは子オブジェクト「Motion」の localPosition / localRotation / localScale を動かし、
// 攻撃が当たる瞬間などに AnimationEvent（関数 OnMotionEvent、文字列でイベント名）を送る。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const baseDir = path.resolve(here, "..");
const outDir = path.join(baseDir, "unity");

const html = fs.readFileSync(path.join(baseDir, "dungeon_minor.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("dungeon_minor.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const { CLIPS, ENEMIES, BODIES, evalClip } = new Function(`${m[1]}\nreturn { CLIPS, ENEMIES, BODIES, evalClip };`)();

const RATE = 60;          // キー数/秒
// 小刻みな震え（毎秒14〜25回）を含むクリップはキーを細かくする
const RATE_OVERRIDE = { Bee_Attack_Sting: 180, Bee_Attack_Charge: 120, RockBall_Death: 120, RockBall_Attack_Roll: 120 };
const EPS = 1e-4;         // 傾きを求める微小時間（秒）
const PATH = "Motion";

const f = (v) => (Math.abs(v) < 1e-7 ? "0" : Number(v.toPrecision(7)).toString());
const vec = (a, names) => `{${names.map((n, i) => `${n}: ${f(a[i])}`).join(", ")}}`;
const qDot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];

function keyTimes(c) {
  const ts = new Set(c.times.map((t) => t.toFixed(6)));
  const n = Math.max(2, Math.round((RATE_OVERRIDE[`${c.body}_${c.name}`] || RATE) * c.dur));
  for (let i = 0; i <= n; i++) ts.add((c.dur * i / n).toFixed(6));
  return [...ts].map(Number).filter((t) => t >= 0 && t <= c.dur).sort((a, b) => a - b);
}

// 入りと出の傾きを別々に（片側差分）とる。折れ目（急停止・着地）もそのまま再現できる
function buildKeys(c) {
  const rot = [], pos = [], scl = [];
  let prevQ = null;
  for (const t of keyTimes(c)) {
    const cur = evalClip(c, t);
    // ループするクリップは端の外側を反対側から取る（つなぎ目をなめらかに）
    const at = (u) => {
      if (c.loop) u = ((u % c.dur) + c.dur) % c.dur;
      return evalClip(c, Math.min(Math.max(u, 0), c.dur));
    };
    const a = t - EPS < 0 && !c.loop ? cur : at(t - EPS);
    const b = t + EPS > c.dur && !c.loop ? cur : at(t + EPS);
    let q = cur.rot;
    if (prevQ && qDot(prevQ, q) < 0) q = q.map((v) => -v);
    prevQ = q;
    const align = (r) => (qDot(r, q) < 0 ? r.map((v) => -v) : r);
    const key = (v, va, vb) => ({ time: t, value: v, inSlope: v.map((_, i) => (v[i] - va[i]) / EPS), outSlope: v.map((_, i) => (vb[i] - v[i]) / EPS) });
    rot.push(key(q, align(a.rot), align(b.rot)));
    pos.push(key(cur.pos, a.pos, b.pos));
    scl.push(key(cur.scl, a.scl, b.scl));
  }
  // 端の傾き：1回きりは外側を平らに、ループは反対の端と同じにする
  for (const ks of [rot, pos, scl]) {
    if (c.loop) { ks[0].inSlope = ks[ks.length - 1].inSlope; ks[ks.length - 1].outSlope = ks[0].outSlope; }
    else { ks[0].inSlope = ks[0].value.map(() => 0); ks[ks.length - 1].outSlope = ks[0].value.map(() => 0); }
  }
  return { rot, pos, scl };
}

const spread = (keys) => {
  let d = 0;
  for (const k of keys) for (let i = 0; i < k.value.length; i++) d = Math.max(d, Math.abs(k.value[i] - keys[0].value[i]));
  return d;
};
// 動かない項目でも初期値（回転なし・位置 0・大きさ 1）と違えばカーブを残す
const needed = (keys, rest) => spread(keys) > 1e-6 || keys[0].value.some((v, i) => Math.abs(v - rest[i]) > 1e-6);

function vectorCurve(keys, names) {
  const w = vec(names.map(() => 1 / 3), names);
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${vec(k.value, names)}\n`;
    s += `        inSlope: ${vec(k.inSlope, names)}\n        outSlope: ${vec(k.outSlope, names)}\n`;
    s += `        tangentMode: 0\n        weightedMode: 0\n        inWeight: ${w}\n        outWeight: ${w}\n`;
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${PATH}\n`;
}
function floatCurve(keys, idx, attribute) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[idx])}\n`;
    s += `        inSlope: ${f(k.inSlope[idx])}\n        outSlope: ${f(k.outSlope[idx])}\n`;
    s += "        tangentMode: 0\n        weightedMode: 0\n        inWeight: 0.33333334\n        outWeight: 0.33333334\n";
  }
  return s + "      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n" +
    `    attribute: ${attribute}\n    path: ${PATH}\n    classID: 4\n    script: {fileID: 0}\n`;
}
const list = (s) => (s ? `\n${s}` : " []\n");

function animYaml(c) {
  const name = `${c.body}_${c.name}`;
  const { rot, pos, scl } = buildKeys(c);
  let rotC = "", posC = "", sclC = "", edC = "";
  if (needed(rot, [0, 0, 0, 1])) {
    rotC = vectorCurve(rot, ["x", "y", "z", "w"]);
    ["x", "y", "z", "w"].forEach((a, i) => { edC += floatCurve(rot, i, `m_LocalRotation.${a}`); });
  }
  if (needed(pos, [0, 0, 0])) {
    posC = vectorCurve(pos, ["x", "y", "z"]);
    ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(pos, i, `m_LocalPosition.${a}`); });
  }
  if (needed(scl, [1, 1, 1])) {
    sclC = vectorCurve(scl, ["x", "y", "z"]);
    ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(scl, i, `m_LocalScale.${a}`); });
  }
  const events = c.events.map(([t, n]) =>
    `  - time: ${f(t)}\n    functionName: OnMotionEvent\n    data: ${n}\n    objectReferenceParameter: {fileID: 0}\n    floatParameter: 0\n    intParameter: 0\n    messageOptions: 0\n`).join("");
  return `%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: ${name}
  serializedVersion: 6
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves:${list(rotC)}  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:${list(posC)}  m_ScaleCurves:${list(sclC)}  m_FloatCurves: []
  m_PPtrCurves: []
  m_SampleRate: 60
  m_WrapMode: 0
  m_Bounds:
    m_Center: {x: 0, y: 0, z: 0}
    m_Extent: {x: 0, y: 0, z: 0}
  m_ClipBindingConstant:
    genericBindings: []
    pptrCurveMapping: []
  m_AnimationClipSettings:
    serializedVersion: 2
    m_AdditiveReferencePoseClip: {fileID: 0}
    m_AdditiveReferencePoseTime: 0
    m_StartTime: 0
    m_StopTime: ${f(c.dur)}
    m_OrientationOffsetY: 0
    m_Level: 0
    m_CycleOffset: 0
    m_HasAdditiveReferencePose: 0
    m_LoopTime: ${c.loop ? 1 : 0}
    m_LoopBlend: 0
    m_LoopBlendOrientation: 0
    m_LoopBlendPositionY: 0
    m_LoopBlendPositionXZ: 0
    m_KeepOriginalOrientation: 0
    m_KeepOriginalPositionY: 1
    m_KeepOriginalPositionXZ: 0
    m_HeightFromFeet: 0
    m_Mirror: 0
  m_EditorCurves:${list(edC)}  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events:${list(events)}`;
}

let total = 0, bytes = 0;
for (const c of CLIPS) {
  const dir = path.join(outDir, c.body);
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${c.body}_${c.name}.anim`);
  const text = animYaml(c);
  fs.writeFileSync(file, text);
  total++; bytes += text.length;
}

// 敵ごとの割り当て表（README に貼る用）
let table = "| ID | 名前 | 体の種類 | クリップ（unity/<体>/<体>_<名前>.anim） | 大きさ |\n|---|---|---|---|---|\n";
for (const e of ENEMIES) table += `| ${e.id} | ${e.name} | ${e.body} | ${e.clips.join(" / ")} | ${e.scale}倍 |\n`;
let events = "| クリップ | 長さ | ループ | イベント |\n|---|---|---|---|\n";
for (const c of CLIPS) events += `| ${c.body}_${c.name} | ${c.dur}秒 | ${c.loop ? "する" : "しない"} | ${c.events.map(([t, n]) => `${n}（${t}秒）`).join("、") || "―"} |\n`;
let bodies = "| 体の種類 | 軸の位置（足元が原点） | モデルの置き方 |\n|---|---|---|\n";
for (const [k, b] of Object.entries(BODIES)) bodies += `| ${k}（${b.name}） | (${b.pivot.join(", ")}) | ${b.note} |\n`;
const readme = `# ダンジョン雑魚モーション（Unity 用）

\`../dungeon_minor.html\` をブラウザで開くと、敵ごとに全クリップの動きを確認できます。
このファイルは \`../tools/export_unity.mjs\` が自動生成します（手で編集しても作り直すと消えます）。

## 仕組み

- 骨を使わず、モデル全体の位置・回転・伸び縮みだけで動かす方式です。どのモデルにも付けられます。
- 構成：\`敵の本体（Animator ＋ EnemyMotion）\` → 子 \`Motion\`（クリップが動かす） → モデル
- 回転や伸び縮みの中心（軸）は体の種類ごとに決めてあり、クリップに織り込み済みです（下の表）。
- 敵の大きさ（1.3倍・2倍など）は、敵の本体の Scale で変えてください。動きの幅も一緒に大きくなります。

## 使い方

1. \`EnemyMotion.cs\` と、使う体の種類のフォルダ（例：\`Mushroom/\`）を Assets に置く。
2. 敵の本体の GameObject に \`EnemyMotion\` を付ける（Animator も自動で付きます）。
   - 子に \`Motion\` が無ければ自動で作り、今ある子（モデル）をその下へ移します。
   - モデルは \`Motion\` の下に、足元が原点・+Z が正面になるよう置く（浮く敵は下の表の高さに体の中心を合わせる）。
3. **Clips** にその敵のクリップを入れる（下の「敵ごとのクリップ」）。
4. ゲーム側から \`GetComponent<EnemyMotion>().Play("Attack_Lunge")\` のように名前の末尾で再生する。
   - 1回きりのクリップが終わると自動で待機（Idle）に戻ります。名前に Death を含むクリップは最後の姿勢で止まります。
   - 移動中は \`Play("Move")\`、止まったら \`Play("Idle")\`。
5. **On Motion Event** に処理をつなぐと、攻撃が当たる瞬間などにイベント名（Hit / Stomp など）付きで呼ばれます。
   **On Motion Finished** は1回きりのクリップが終わったときに呼ばれます。

長い突進（ハチの Attack_Charge）と転がり（岩ダンゴの Attack_Roll）は、クリップはその場で「構え → 突進中の姿勢 → 止まる」だけを動かします。
ChargeStart〜ChargeEnd、RollStart〜RollEnd の間に、ゲーム側で敵の本体を前へ動かしてください。
短い飛びかかり・噛みつき・刺す動きは、クリップの中で前に出て元の位置に戻ります。

## 敵ごとのクリップ

${table}
## クリップ一覧

${events}
## 体の種類

${bodies}
## 作り直し方

\`../dungeon_minor.html\` の \`==POSE-BEGIN==\`〜\`==POSE-END==\` にクリップ定義があります。編集したら次を実行すると .anim とこの README が作り直されます（Node.js のみ必要）。

\`\`\`
node <dungeon_minor フォルダ>/tools/export_unity.mjs
\`\`\`

## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面を教えてください。
`;
fs.writeFileSync(path.join(outDir, "README.md"), readme);

console.log(`クリップ ${total} 本 / 合計 ${(bytes / 1024).toFixed(0)} KB → ${path.relative(process.cwd(), outDir)}`);
