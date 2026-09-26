// 魔法陣から属性の玉・ビームを撃ち出すモーションを Unity 用アセットに書き出す。
//
//   node <このフォルダ>/export_unity.mjs
//
// ../magic_circle.html の ==POSE-BEGIN== 〜 ==POSE-END== の定義から、
//   ../unity/Clips/MagicCircle_<撃ち方>.anim … 魔法陣・輪・ルーン・中心・玉・ビームの位置／回転／大きさを動かす Generic クリップ
//   ../unity/README.md
// を出力する。撃つ・着弾などの瞬間に AnimationEvent（関数 OnMotionEvent、文字列でイベント名）を送る。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const baseDir = path.resolve(here, "..");
const outDir = path.join(baseDir, "unity");

const html = fs.readFileSync(path.join(baseDir, "magic_circle.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("magic_circle.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const { CLIPS, ELEMENTS, ORBS, evalFx } = new Function(`${m[1]}\nreturn { CLIPS, ELEMENTS, ORBS, evalFx };`)();

const RATES = [20, 30, 60, 120, 180, 240];
const TOLERANCE = 0.002;   // 2mm（部品の中心から 1m 前後の点で測る）
const EPS = 1e-4;
const DEG = Math.PI / 180;

const f = (v) => (Math.abs(v) < 1e-7 ? "0" : Number(v.toPrecision(6)).toString());
const vec = (a, names) => `{${names.map((n, i) => `${n}: ${f(a[i])}`).join(", ")}}`;
const qMul = (a, b) => [
  a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
  a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
  a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
  a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
];
const qAxis = (ax, deg) => { const h = deg * DEG / 2, s = Math.sin(h); return [ax[0] * s, ax[1] * s, ax[2] * s, Math.cos(h)]; };
// Unity の Quaternion.Euler（Z → X → Y の順）
const qEuler = (r) => qMul(qMul(qAxis([0, 1, 0], r[1]), qAxis([1, 0, 0], r[0])), qAxis([0, 0, 1], r[2]));
const qDot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
const qRotate = (q, v) => {
  const n = Math.hypot(...q); q = q.map((x) => x / n);
  const [x, y, z, w] = q, [vx, vy, vz] = v;
  const tx = 2 * (y * vz - z * vy), ty = 2 * (z * vx - x * vz), tz = 2 * (x * vy - y * vx);
  return [vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx)];
};

const PATHS = ["Circle", "Circle/RingOuter", "Circle/RingInner", "Circle/Runes", "Circle/Core", ...Array.from({ length: ORBS }, (_, i) => `Orb_${i}`), "Beam"];

function keyTimes(c, rate) {
  const ts = new Set(c.times.map((t) => t.toFixed(6)));
  const n = Math.max(2, Math.round(rate * c.dur));
  for (let i = 0; i <= n; i++) ts.add((c.dur * i / n).toFixed(6));
  return [...ts].map(Number).sort((a, b) => a - b);
}
const clampT = (c, u) => Math.min(Math.max(u, 0), c.dur);
const cache = new Map();
const fxAt = (c, t) => { const k = `${c.name}_${t.toFixed(7)}`; if (!cache.has(k)) cache.set(k, evalFx(c, t)); return cache.get(k); };
const valueOf = (c, t, p, kind) => { const o = fxAt(c, clampT(c, t))[p]; return kind === "rot" ? qEuler(o.rot) : kind === "pos" ? o.pos : o.scl; };

// 入りと出の傾きは片側差分（折れ目もそのまま）。回転は符号をそろえる
function makeKeys(c, rate, p, kind) {
  const keys = [];
  let prev = null;
  for (const t of keyTimes(c, rate)) {
    let v = valueOf(c, t, p, kind);
    if (kind === "rot" && prev && qDot(prev, v) < 0) v = v.map((x) => -x);
    prev = v;
    const align = (r) => (kind === "rot" && qDot(r, v) < 0 ? r.map((x) => -x) : r);
    const a = t - EPS < 0 ? v : align(valueOf(c, t - EPS, p, kind));
    const b = t + EPS > c.dur ? v : align(valueOf(c, t + EPS, p, kind));
    keys.push({ time: t, value: v, inSlope: v.map((x, i) => (x - a[i]) / EPS), outSlope: v.map((x, i) => (b[i] - x) / EPS) });
  }
  keys[0].inSlope = keys[0].value.map(() => 0);
  keys[keys.length - 1].outSlope = keys[0].value.map(() => 0);
  return keys;
}
function hermite(keys, t) {
  let i = keys.findIndex((k) => k.time >= t);
  if (i <= 0) return keys[i < 0 ? keys.length - 1 : 0].value;
  const a = keys[i - 1], b = keys[i], h = b.time - a.time, s = (t - a.time) / h;
  const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2;
  return a.value.map((_, j) => h00 * a.value[j] + h10 * h * a.outSlope[j] + h01 * b.value[j] + h11 * h * b.inSlope[j]);
}
// 部品ごと：位置・回転・大きさをまとめて、部品の中心から 1m 前後の点のずれで細かさを決める
function partKeys(c, p) {
  const probes = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [-0.6, 0.6, 0.5]];
  const apply = (T, v) => { const r = qRotate(T.rot, [v[0] * T.scl[0], v[1] * T.scl[1], v[2] * T.scl[2]]); return [r[0] + T.pos[0], r[1] + T.pos[1], r[2] + T.pos[2]]; };
  const n = Math.max(200, Math.round(c.dur * 400));
  let keys, err, rate;
  for (rate of RATES) {
    keys = { rot: makeKeys(c, rate, p, "rot"), pos: makeKeys(c, rate, p, "pos"), scl: makeKeys(c, rate, p, "scl") };
    err = 0;
    for (let i = 0; i <= n; i++) {
      const t = c.dur * i / n;
      const want = { rot: valueOf(c, t, p, "rot"), pos: valueOf(c, t, p, "pos"), scl: valueOf(c, t, p, "scl") };
      const got = { rot: hermite(keys.rot, t), pos: hermite(keys.pos, t), scl: hermite(keys.scl, t) };
      for (const v of probes) { const a = apply(want, v), g = apply(got, v); err = Math.max(err, Math.hypot(a[0] - g[0], a[1] - g[1], a[2] - g[2])); }
    }
    if (err <= TOLERANCE) break;
  }
  return { keys, err, rate };
}
const spread = (keys) => Math.max(...keys.map((k) => Math.max(...k.value.map((v, i) => Math.abs(v - keys[0].value[i])))));
const compact = (keys) => (spread(keys) > 1e-6 ? keys : [
  { ...keys[0], inSlope: keys[0].value.map(() => 0), outSlope: keys[0].value.map(() => 0) },
  { ...keys[keys.length - 1], value: keys[0].value, inSlope: keys[0].value.map(() => 0), outSlope: keys[0].value.map(() => 0) },
]);

function vectorCurve(keys, names, p) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${vec(k.value, names)}\n        inSlope: ${vec(k.inSlope, names)}\n        outSlope: ${vec(k.outSlope, names)}\n`;
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${p}\n`;
}
function floatCurve(keys, idx, attribute, p) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[idx])}\n        inSlope: ${f(k.inSlope[idx])}\n        outSlope: ${f(k.outSlope[idx])}\n`;
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    attribute: ${attribute}\n    path: ${p}\n    classID: 4\n    script: {fileID: 0}\n`;
}

const report = [];
fs.mkdirSync(path.join(outDir, "Clips"), { recursive: true });
let bytes = 0;
for (const c of CLIPS) {
  let rotC = "", posC = "", sclC = "", edC = "", worst = 0, maxRate = 0;
  for (const p of PATHS) {
    const pk = partKeys(c, p);
    worst = Math.max(worst, pk.err); maxRate = Math.max(maxRate, pk.rate);
    const rot = compact(pk.keys.rot), pos = compact(pk.keys.pos), scl = compact(pk.keys.scl);
    rotC += vectorCurve(rot, ["x", "y", "z", "w"], p);
    posC += vectorCurve(pos, ["x", "y", "z"], p);
    sclC += vectorCurve(scl, ["x", "y", "z"], p);
    ["x", "y", "z", "w"].forEach((a, i) => { edC += floatCurve(rot, i, `m_LocalRotation.${a}`, p); });
    ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(pos, i, `m_LocalPosition.${a}`, p); });
    ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(scl, i, `m_LocalScale.${a}`, p); });
  }
  report.push({ name: c.name, err: worst, rate: maxRate });
  const events = c.events.map(([t, n]) =>
    `  - time: ${f(t)}\n    functionName: OnMotionEvent\n    data: ${n}\n    objectReferenceParameter: {fileID: 0}\n    floatParameter: 0\n    intParameter: 0\n    messageOptions: 0\n`).join("");
  const name = `MagicCircle_${c.name}`;
  const text = `%YAML 1.1
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
  m_RotationCurves:
${rotC}  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:
${posC}  m_ScaleCurves:
${sclC}  m_FloatCurves: []
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
    m_LoopTime: 0
    m_LoopBlend: 0
    m_LoopBlendOrientation: 0
    m_LoopBlendPositionY: 0
    m_LoopBlendPositionXZ: 0
    m_KeepOriginalOrientation: 0
    m_KeepOriginalPositionY: 1
    m_KeepOriginalPositionXZ: 0
    m_HeightFromFeet: 0
    m_Mirror: 0
  m_EditorCurves:
${edC}  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events:${events ? `\n${events}` : " []\n"}`;
  fs.writeFileSync(path.join(outDir, "Clips", `${name}.anim`), text);
  bytes += text.length;
}

// README
let clipTable = "| クリップ | 長さ | 内容 | イベント |\n|---|---|---|---|\n";
for (const c of CLIPS) clipTable += `| MagicCircle_${c.name} | ${c.dur}秒 | ${c.note} | ${c.events.map(([t, n]) => `${n}（${t}秒）`).join("、")} |\n`;
let elTable = "| 属性（Element） | 色 | 味付け |\n|---|---|---|\n";
for (const e of ELEMENTS) elTable += `| ${e.key}（${e.name}） | ${e.main} | ${e.note} |\n`;
fs.writeFileSync(path.join(outDir, "README.md"), `# 魔法陣の玉とビーム（Unity 用）

\`../magic_circle.html\` をブラウザで開くと、撃ち方 × 属性の組み合わせを確認できます。
このファイルは \`../tools/export_unity.mjs\` が自動生成します。

## 仕組み

- \`MagicCircleRig\` が、魔法陣（外の輪・内の輪・六芒星・ルーン・中心の光）・玉 8 個（尾つき）・ビームを組み立てます。
- クリップはそれらの位置・回転・大きさだけを動かします（大きさ 0 のときは見えません）。属性は同じクリップのまま、色と味付けで出し分けます。
- 原点は術者の足元、+Z が正面です。術者の子に置くか、撃つ位置・向きに合わせて置いてください。
- 撃つ瞬間などに **On Motion Event** がイベント名付きで呼ばれます。玉が複数ある撃ち方は \`Fire:2\`・\`Impact:5\` のように玉の番号が付きます。
  \`GetOrb(番号)\` でその玉の Transform が取れるので、当たり判定や着弾エフェクトの位置に使えます。ビームは \`BeamTransform\`（付け根。+Z 方向へ伸びる）。

## 使い方

1. \`MagicCircleRig.cs\` と \`Clips\` フォルダを Assets に置く。
2. 空の GameObject に \`MagicCircleRig\` を付ける（Animator も自動で付きます）。
3. **Clips** に使う撃ち方のクリップを入れ、**Element** で属性を選ぶ。
4. \`Cast("Beam")\` や \`Cast("Orb_Triple", MagicCircleRig.Element.Ice)\` のように呼ぶと、その撃ち方を最初から再生します。
   **Play On Start** をオンにすると、始まったときに最初のクリップを再生します（確認用）。

## 撃ち方

${clipTable}
## 属性

${elTable}
## 作り直し方

\`../magic_circle.html\` の \`==POSE-BEGIN==\`〜\`==POSE-END==\` に撃ち方の定義があります。編集したら次を実行します（Node.js のみ必要）。

\`\`\`
node <magic_circle フォルダ>/tools/export_unity.mjs
\`\`\`

## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面や見た目を教えてください。
- 色の加算表示には、パーティクル用のシェーダー（URP の Particles/Unlit、ビルトインの Legacy Shaders/Particles/Additive）を順に探して使います。ビルドで削られる場合は Always Included Shaders に追加してください。
`);

const worst = report.reduce((a, b) => (b.err > a.err ? b : a));
console.log(`クリップ ${CLIPS.length} 本 / 合計 ${(bytes / 1024).toFixed(0)} KB → ${path.relative(process.cwd(), outDir)}`);
console.log(`ずれ 最大 ${(worst.err * 1000).toFixed(3)} mm（${worst.name}）／ いちばん細かい部品: ${report.map((r) => `${r.name}(${r.rate})`).join(", ")}`);
if (report.some((r) => r.err > TOLERANCE)) console.warn("注意: 許容値を超えたクリップがあります");
