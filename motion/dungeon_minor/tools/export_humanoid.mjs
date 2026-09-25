// ダンジョン雑魚・人型（名前に「人」を含む敵）のモーションを Unity 用に書き出す。
//
//   node <このフォルダ>/export_humanoid.mjs
//
// ../dungeon_humanoid.html の ==POSE-BEGIN== 〜 ==POSE-END== の定義から、
//   ../unity/Humanoid/<骨組み>_<クリップ>.anim   … 代理の骨組み「Proxy」の関節位置を動かす Generic クリップ
//   ../unity/Humanoid/HumanoidProxyBones.cs       … 代理の骨組みの階層と初期位置（HumanoidRetarget.cs が使う）
//   ../unity/Humanoid/README.md
// を出力する。代理の骨組みは回転を持たず、各関節の位置（親からのずれ）だけで姿勢を表す。
// HumanoidRetarget.cs がその位置から骨の向きを求め、モデルの Humanoid ボーンを同じ向きに回す。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const baseDir = path.resolve(here, "..");
const outDir = path.join(baseDir, "unity", "Humanoid");

const html = fs.readFileSync(path.join(baseDir, "dungeon_humanoid.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("dungeon_humanoid.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const { CLIPS, ENEMIES, RIGS, JOINTS, REST, evalClip } = new Function(`${m[1]}\nreturn { CLIPS, ENEMIES, RIGS, JOINTS, REST, evalClip };`)();

const RATES = [20, 30, 60, 120, 180];
const TOLERANCE = 0.002;   // 2mm（身長 1.7m 前後の人型なので見た目には影響しない）
const EPS = 1e-4;

const parentOf = Object.fromEntries(JOINTS);
const pathOf = (j) => (parentOf[j] ? `${pathOf(parentOf[j])}/${j}` : `Proxy/${j}`);
const localOf = (P, j) => (parentOf[j] ? P[j].map((v, i) => v - P[parentOf[j]][i]) : P[j]);

const f = (v) => (Math.abs(v) < 1e-7 ? "0" : Number(v.toPrecision(7)).toString());
const vec = (a) => `{x: ${f(a[0])}, y: ${f(a[1])}, z: ${f(a[2])}}`;

function keyTimes(c, rate) {
  const ts = new Set(c.times.map((t) => t.toFixed(6)));
  const n = Math.max(2, Math.round(rate * c.dur));
  for (let i = 0; i <= n; i++) ts.add((c.dur * i / n).toFixed(6));
  return [...ts].map(Number).sort((a, b) => a - b);
}
function buildKeys(c, rate) {
  const at = (u) => evalClip(c, c.loop ? ((u % c.dur) + c.dur) % c.dur : Math.min(Math.max(u, 0), c.dur));
  const keys = Object.fromEntries(JOINTS.map(([j]) => [j, []]));
  for (const t of keyTimes(c, rate)) {
    const cur = at(t);
    const a = !c.loop && t - EPS < 0 ? cur : at(t - EPS);
    const b = !c.loop && t + EPS > c.dur ? cur : at(t + EPS);
    for (const [j] of JOINTS) {
      const v = localOf(cur, j), va = localOf(a, j), vb = localOf(b, j);
      keys[j].push({ time: t, value: v, inSlope: v.map((x, i) => (x - va[i]) / EPS), outSlope: v.map((x, i) => (vb[i] - x) / EPS) });
    }
  }
  for (const [j] of JOINTS) {
    const ks = keys[j];
    if (c.loop) { ks[0].inSlope = ks[ks.length - 1].inSlope; ks[ks.length - 1].outSlope = ks[0].outSlope; }
    else { ks[0].inSlope = [0, 0, 0]; ks[ks.length - 1].outSlope = [0, 0, 0]; }
  }
  return keys;
}
function hermite(keys, t) {
  let i = keys.findIndex((k) => k.time >= t);
  if (i <= 0) return keys[i < 0 ? keys.length - 1 : 0].value;
  const a = keys[i - 1], b = keys[i], h = b.time - a.time, s = (t - a.time) / h;
  const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2;
  return a.value.map((_, k) => h00 * a.value[k] + h10 * h * a.outSlope[k] + h01 * b.value[k] + h11 * h * b.inSlope[k]);
}
// 関節の位置（親から足し合わせた世界位置）で元の姿勢とのずれを測る
function maxError(c, keys) {
  let worst = 0;
  const n = Math.max(200, Math.round(c.dur * 300));
  for (let i = 0; i <= n; i++) {
    const t = c.dur * i / n, want = evalClip(c, t), got = {};
    for (const [j, p] of JOINTS) {
      const l = hermite(keys[j], t);
      got[j] = p ? l.map((v, k) => v + got[p][k]) : l;
      worst = Math.max(worst, Math.hypot(...got[j].map((v, k) => v - want[j][k])));
    }
  }
  return worst;
}
const spread = (ks) => Math.max(...ks.map((k) => Math.max(...k.value.map((v, i) => Math.abs(v - ks[0].value[i])))));
const compact = (ks) => (spread(ks) > 1e-6 ? ks : [
  { ...ks[0], inSlope: [0, 0, 0], outSlope: [0, 0, 0] },
  { ...ks[ks.length - 1], value: ks[0].value, inSlope: [0, 0, 0], outSlope: [0, 0, 0] },
]);

function vectorCurve(ks, p) {
  const w = "{x: 0.3333333, y: 0.3333333, z: 0.3333333}";
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of ks) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${vec(k.value)}\n        inSlope: ${vec(k.inSlope)}\n        outSlope: ${vec(k.outSlope)}\n`;
    s += `        tangentMode: 0\n        weightedMode: 0\n        inWeight: ${w}\n        outWeight: ${w}\n`;
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${p}\n`;
}
function floatCurve(ks, i, attr, p) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of ks) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[i])}\n        inSlope: ${f(k.inSlope[i])}\n        outSlope: ${f(k.outSlope[i])}\n`;
    s += "        tangentMode: 0\n        weightedMode: 0\n        inWeight: 0.33333334\n        outWeight: 0.33333334\n";
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    attribute: ${attr}\n    path: ${p}\n    classID: 4\n    script: {fileID: 0}\n`;
}

const report = [];
fs.mkdirSync(outDir, { recursive: true });
let bytes = 0;
for (const c of CLIPS) {
  const name = `${c.rig}_${c.name}`;
  let keys, err, rate;
  for (rate of RATES) { keys = buildKeys(c, rate); err = maxError(c, keys); if (err <= TOLERANCE) break; }
  report.push({ name, rate, err });
  let posC = "", edC = "";
  for (const [j] of JOINTS) {
    const ks = compact(keys[j]), p = pathOf(j);
    posC += vectorCurve(ks, p);
    ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(ks, i, `m_LocalPosition.${a}`, p); });
  }
  const events = c.events.map(([t, n]) =>
    `  - time: ${f(t)}\n    functionName: OnMotionEvent\n    data: ${n}\n    objectReferenceParameter: {fileID: 0}\n    floatParameter: 0\n    intParameter: 0\n    messageOptions: 0\n`).join("");
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
  m_RotationCurves: []
  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:
${posC}  m_ScaleCurves: []
  m_FloatCurves: []
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
  m_EditorCurves:
${edC}  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events:${events ? `\n${events}` : " []\n"}`;
  fs.writeFileSync(path.join(outDir, `${name}.anim`), text);
  bytes += text.length;
}

// 代理の骨組みの表（C#）
const cs = `// このファイルは tools/export_humanoid.mjs が自動生成します。手で編集しないでください。
// 代理の骨組み（Proxy）の階層と、立ち姿での各関節の位置（親からのずれ、m）。回転は使いません。
using UnityEngine;

public static class HumanoidProxyBones
{
    public static readonly string[] Paths =
    {
${JOINTS.map(([j]) => `        "${pathOf(j)}",`).join("\n")}
    };

    public static readonly Vector3[] RestLocalPositions =
    {
${JOINTS.map(([j]) => { const v = localOf(REST, j); return `        new Vector3(${v.map((x) => `${f(x)}f`).join(", ")}),`; }).join("\n")}
    };
}
`;
fs.writeFileSync(path.join(outDir, "HumanoidProxyBones.cs"), cs);

let table = "| ID | 名前 | 骨組み | クリップ（Humanoid/<骨組み>_<名前>.anim） |\n|---|---|---|---|\n";
for (const e of ENEMIES) table += `| ${e.id} | ${e.name} | ${e.rig}（${RIGS[e.rig].name}） | ${e.clips.join(" / ")} |\n`;
let list = "| クリップ | 長さ | ループ | イベント |\n|---|---|---|---|\n";
for (const c of CLIPS) list += `| ${c.rig}_${c.name} | ${c.dur}秒 | ${c.loop ? "する" : "しない"} | ${c.events.map(([t, n]) => `${n}（${t}秒）`).join("、") || "―"} |\n`;
fs.writeFileSync(path.join(outDir, "README.md"), `# ダンジョン雑魚・人型（Unity 用）

名前に「人」を含む敵（EN-09 / 12 / 13 / 33 / 54）用です。\`../../dungeon_humanoid.html\` で動きを確認できます。
このファイルは \`../../tools/export_humanoid.mjs\` が自動生成します。

## 仕組み

- 見えない「代理の骨組み（Proxy）」を Generic クリップで動かします（関節の位置だけ。回転は持たない）。
- \`HumanoidRetarget\` が毎フレーム（LateUpdate）、モデルの Humanoid ボーンを代理の骨と同じ向きに回します。
  - 骨の向きだけを写すので、モデルの体格・骨の軸の向きが違っても使えます。腰の上下・前後の動きは脚の長さの比で合わせます。
  - 腕や脚のねじれ（手のひらの向きなど）はモデルの元の姿勢のままです。

## 使い方

1. \`EnemyMotion.cs\`（ひとつ上のフォルダ）と、このフォルダの \`HumanoidRetarget.cs\`・\`HumanoidProxyBones.cs\`・使うクリップを Assets に置く。
2. 敵の本体（空の GameObject）に \`EnemyMotion\` と \`HumanoidRetarget\` を付ける。
3. 人型モデル（Rig が Humanoid のもの）を本体の子に置く。モデルの正面を +Z、足元を本体の原点に合わせる。
   - モデル自身の Animator には Controller を入れないでください（入れても LateUpdate で上書きしますが、無駄な計算になります）。
4. \`HumanoidRetarget\` の **Target** にモデルの Animator を入れる（空なら子から自動で探します）。
5. \`EnemyMotion\` の **Clips** にその敵のクリップを入れ、\`Play("Attack_Punch")\` のように再生する。イベントの受け取りは人型以外と同じです。

## 敵ごとのクリップ

${table}
## クリップ一覧

${list}
## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面や見た目を教えてください。
`);

const worst = report.reduce((a, b) => (b.err > a.err ? b : a));
console.log(`人型クリップ ${CLIPS.length} 本 / 合計 ${(bytes / 1024).toFixed(0)} KB → ${path.relative(process.cwd(), outDir)}`);
console.log(`関節位置のずれ 最大 ${(worst.err * 1000).toFixed(3)} mm（${worst.name}）`);
console.log(`キーを細かくしたクリップ: ${report.filter((r) => r.rate > RATES[0]).map((r) => `${r.name}(${r.rate})`).join(", ") || "なし"}`);
if (report.some((r) => r.err > TOLERANCE)) console.warn("注意: 許容値を超えたクリップがあります");
