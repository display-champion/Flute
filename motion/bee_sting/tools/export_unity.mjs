// 蜂の針攻撃モーションを Unity 用アセットに書き出す。
//
//   node motion/bee_sting/tools/export_unity.mjs
//
// motion/bee_sting/bee_sting.html の ==POSE-BEGIN== 〜 ==POSE-END== にある姿勢計算をそのまま使い、
// 以下を motion/bee_sting/unity/ に出力する（追加パッケージ不要）。
//   BeeSting.anim     … Generic リグ用のループ AnimationClip（1回の攻撃サイクル）
//   BeeRigBones.cs    … クリップと対応する関節階層・初期姿勢・見た目の指定（BeeRig.cs が参照）

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const motionDir = path.resolve(here, "..");
const outDir = path.join(motionDir, "unity");

// ---------- HTML から姿勢計算を取り出す ----------
const html = fs.readFileSync(path.join(motionDir, "bee_sting.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("bee_sting.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const lib = new Function(`${m[1]}\nreturn { pose, CYCLE_SEC, FLAPS, THORAX_R, HEAD_R, EYE_R, ABD_LEN, ABD_R, ABD_COL, WINGS, HIT_T };`)();
const { pose, CYCLE_SEC, FLAPS, THORAX_R, HEAD_R, EYE_R, ABD_LEN, ABD_R, ABD_COL, WINGS, HIT_T } = lib;

const RATE = 30;            // 通常の関節のキー数/秒
const FAST_RATE = 120;      // 胴体（刺した直後の震え）
const WING_KEYS_PER_FLAP = 8;

// ---------- 関節階層 ----------
// frame: "aim"（+Y を aim 関節へ向ける）/ "axes"（Y, Z を直接指定）/ "inherit"（親と同じ向き）
// vis:   Unity 側の見た目。sphere / line（親からこの関節まで）/ wing / none
// color: 0 黒, 1 黄, 2 琥珀, 3 アクセント, 4 羽
const COL = { black: 0, yellow: 1, amber: 2, accent: 3, wing: 4 };
const joints = [];
const J = (o) => joints.push({ rate: RATE, vis: "none", size: 0, size2: 0, offset: 0, color: 0, ...o });

J({ name: "Body", parent: null, get: (P) => P.root, frame: "axes", axes: (P) => ({ Y: P.up, Z: P.fwd }),
  rate: FAST_RATE, vis: "sphere", size: THORAX_R, color: COL.amber });
J({ name: "Head", parent: "Body", get: (P) => P.head, frame: "inherit", vis: "sphere", size: HEAD_R, color: COL.black });
["L", "R"].forEach((sfx, i) => {
  J({ name: `Eye_${sfx}`, parent: "Head", get: (P) => P.eyes[i], frame: "inherit", vis: "sphere", size: EYE_R, color: COL.accent });
  J({ name: `Antenna_${sfx}_a`, parent: "Head", get: (P) => P.antennae[i][0], frame: "aim", aim: `Antenna_${sfx}_b` });
  J({ name: `Antenna_${sfx}_b`, parent: `Antenna_${sfx}_a`, get: (P) => P.antennae[i][1], frame: "aim", aim: `Antenna_${sfx}_c`,
    vis: "line", size: 0.012 });
  J({ name: `Antenna_${sfx}_c`, parent: `Antenna_${sfx}_b`, get: (P) => P.antennae[i][2], frame: "inherit", vis: "line", size: 0.01 });
});
for (let k = 0; k < 5; k++) {
  J({ name: `Abdomen_${k + 1}`, parent: k === 0 ? "Body" : `Abdomen_${k}`, get: (P) => P.abd[k], frame: "aim",
    aim: k < 4 ? `Abdomen_${k + 2}` : "Stinger", vis: "sphere", size: ABD_R[k], offset: ABD_LEN[k] / 2, color: COL[ABD_COL[k]] });
}
J({ name: "Stinger", parent: "Abdomen_5", get: (P) => P.abd[5], frame: "aim", aim: "StingerTip" });
J({ name: "StingerTip", parent: "Stinger", get: (P) => P.stingTip, frame: "inherit", vis: "line", size: 0.03, color: COL.accent });
WINGS.forEach((wg, i) => {
  J({ name: wg.name, parent: "Body", get: (P) => P.wings[i].root, frame: "axes",
    axes: (P) => ({ Y: P.wings[i].span, Z: P.wings[i].chord }),
    rate: FLAPS / CYCLE_SEC * WING_KEYS_PER_FLAP, vis: "wing", size: wg.L, size2: wg.W, color: COL.wing });
});
for (let i = 0; i < 6; i++) {
  const n = `Leg_${i < 3 ? "L" : "R"}${(i % 3) + 1}`;
  J({ name: `${n}_a`, parent: "Body", get: (P) => P.legs[i].pts[0], frame: "aim", aim: `${n}_b` });
  J({ name: `${n}_b`, parent: `${n}_a`, get: (P) => P.legs[i].pts[1], frame: "aim", aim: `${n}_c`, vis: "line", size: 0.018 });
  J({ name: `${n}_c`, parent: `${n}_b`, get: (P) => P.legs[i].pts[2], frame: "inherit", vis: "line", size: 0.014 });
}
const byName = Object.fromEntries(joints.map((j) => [j.name, j]));
const pathOf = (j) => (j.parent ? `${pathOf(byName[j.parent])}/${j.name}` : j.name);
for (const j of joints) j.path = pathOf(j);

// ---------- 数学 ----------
const arr = (v) => [v.x, v.y, v.z];
const sub3 = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm3 = (a) => { const l = Math.hypot(...a) || 1; return a.map((v) => v / l); };
function matToQuat(X, Y, Z) {
  const [m00, m10, m20] = X, [m01, m11, m21] = Y, [m02, m12, m22] = Z;
  const tr = m00 + m11 + m22;
  if (tr > 0) { const s = Math.sqrt(tr + 1) * 2; return [(m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, 0.25 * s]; }
  if (m00 > m11 && m00 > m22) { const s = Math.sqrt(1 + m00 - m11 - m22) * 2; return [0.25 * s, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s]; }
  if (m11 > m22) { const s = Math.sqrt(1 + m11 - m00 - m22) * 2; return [(m01 + m10) / s, 0.25 * s, (m12 + m21) / s, (m02 - m20) / s]; }
  const s = Math.sqrt(1 + m22 - m00 - m11) * 2; return [(m02 + m20) / s, (m12 + m21) / s, 0.25 * s, (m10 - m01) / s];
}
const qMul = (a, b) => [
  a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
  a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
  a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
  a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
];
const qInv = (q) => [-q[0], -q[1], -q[2], q[3]];
const qRot = (q, v) => { const r = qMul(qMul(q, [v[0], v[1], v[2], 0]), qInv(q)); return [r[0], r[1], r[2]]; };
const qDot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
const fromAxes = (Y, Zref) => {
  const y = norm3(Y);
  const x = norm3(cross3(y, Zref));
  return matToQuat(x, y, cross3(x, y));
};

// aim 関節のねじれ基準：体の前・上・横のうち、全フレームを通して骨と平行に最も近づかない軸
// （腹や針は体の縦断面で丸まるので横方向になる）
const refAxis = (P, kind) => arr(kind === "fwd" ? P.fwd : kind === "up" ? P.up : P.right);
const probe = Array.from({ length: 240 }, (_, i) => pose(i / 240));
for (const P of probe) { const r = cross3(arr(P.up), arr(P.fwd)); P.right = { x: r[0], y: r[1], z: r[2] }; }
for (const j of joints) {
  if (j.frame !== "aim") continue;
  let best = null;
  for (const kind of ["fwd", "up", "right"]) {
    let worst = 0;
    for (const P of probe) worst = Math.max(worst, Math.abs(dot3(norm3(sub3(arr(byName[j.aim].get(P)), arr(j.get(P)))), refAxis(P, kind))));
    if (!best || worst < best.worst - 1e-9) best = { kind, worst };
  }
  j.ref = best.kind;
  j.refWorst = best.worst;
}

// 時刻 u（0〜1）の各関節のローカル位置・回転
function localAt(u) {
  const P = pose(((u % 1) + 1) % 1);
  const r = cross3(arr(P.up), arr(P.fwd));
  P.right = { x: r[0], y: r[1], z: r[2] };
  const world = {};
  for (const j of joints) {
    const pos = arr(j.get(P));
    let rot;
    if (j.frame === "axes") { const a = j.axes(P); rot = fromAxes(arr(a.Y), arr(a.Z)); }
    else if (j.frame === "aim") rot = fromAxes(sub3(arr(byName[j.aim].get(P)), pos), refAxis(P, j.ref));
    else rot = world[j.parent].rot;
    world[j.name] = { pos, rot };
  }
  const local = {};
  for (const j of joints) {
    const w = world[j.name];
    if (!j.parent) { local[j.name] = w; continue; }
    const p = world[j.parent];
    const inv = qInv(p.rot);
    local[j.name] = { pos: qRot(inv, sub3(w.pos, p.pos)), rot: j.frame === "inherit" ? [0, 0, 0, 1] : qMul(inv, w.rot) };
  }
  return local;
}

// ---------- キー作成（傾きは前後の微小時間から求める） ----------
const EPS = 1e-4;   // サイクル単位
const cache = new Map();
const L = (u) => { const k = u.toFixed(9); if (!cache.has(k)) cache.set(k, localAt(u)); return cache.get(k); };

function buildKeys(j) {
  const n = Math.max(2, Math.round(j.rate * CYCLE_SEC));
  const rot = [], pos = [];
  let prevQ = null;
  for (let i = 0; i <= n; i++) {
    const u = i / n;
    const cur = L(u)[j.name];
    let q = cur.rot;
    if (prevQ && qDot(prevQ, q) < 0) q = q.map((v) => -v);
    prevQ = q;
    const align = (r) => (qDot(r, q) < 0 ? r.map((v) => -v) : r);
    const qa = align(L(u - EPS)[j.name].rot), qb = align(L(u + EPS)[j.name].rot);
    const pa = L(u - EPS)[j.name].pos, pb = L(u + EPS)[j.name].pos;
    const dt = 2 * EPS * CYCLE_SEC;
    rot.push({ time: u * CYCLE_SEC, value: q, slope: q.map((_, c) => (qb[c] - qa[c]) / dt) });
    pos.push({ time: u * CYCLE_SEC, value: cur.pos, slope: cur.pos.map((_, c) => (pb[c] - pa[c]) / dt) });
  }
  return { rot, pos };
}
const spread = (keys) => {
  let d = 0;
  for (const k of keys) d = Math.max(d, Math.hypot(...sub3(k.value, keys[0].value)), k.value.length === 4 ? Math.abs(k.value[3] - keys[0].value[3]) : 0);
  return d;
};

// ---------- .anim（YAML）書き出し ----------
const f = (v) => (Math.abs(v) < 1e-7 ? "0" : Number(v.toPrecision(7)).toString());
const vec = (a, names) => `{${names.map((n, i) => `${n}: ${f(a[i])}`).join(", ")}}`;
function vectorCurve(keys, names, pathStr) {
  const w = vec(names.map(() => 1 / 3), names);
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${vec(k.value, names)}\n`;
    s += `        inSlope: ${vec(k.slope, names)}\n        outSlope: ${vec(k.slope, names)}\n`;
    s += `        tangentMode: 0\n        weightedMode: 0\n        inWeight: ${w}\n        outWeight: ${w}\n`;
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${pathStr}\n`;
}
function floatCurve(keys, idx, attribute, pathStr) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[idx])}\n`;
    s += `        inSlope: ${f(k.slope[idx])}\n        outSlope: ${f(k.slope[idx])}\n`;
    s += "        tangentMode: 0\n        weightedMode: 0\n        inWeight: 0.33333334\n        outWeight: 0.33333334\n";
  }
  return s + "      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n" +
    `    attribute: ${attribute}\n    path: ${pathStr}\n    classID: 4\n    script: {fileID: 0}\n`;
}

let rotCurves = "", posCurves = "", editorCurves = "", nRot = 0, nPos = 0;
for (const j of joints) {
  const { rot, pos } = buildKeys(j);
  j.animRot = spread(rot) > 1e-6;
  j.animPos = spread(pos) > 1e-6;
  if (j.animRot) {
    nRot++;
    rotCurves += vectorCurve(rot, ["x", "y", "z", "w"], j.path);
    ["x", "y", "z", "w"].forEach((c, i) => { editorCurves += floatCurve(rot, i, `m_LocalRotation.${c}`, j.path); });
  }
  if (j.animPos) {
    nPos++;
    posCurves += vectorCurve(pos, ["x", "y", "z"], j.path);
    ["x", "y", "z"].forEach((c, i) => { editorCurves += floatCurve(pos, i, `m_LocalPosition.${c}`, j.path); });
  }
  j.rest = L(0)[j.name];
}
const list = (s) => (s ? `\n${s}` : " []\n");

const anim = `%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: BeeSting
  serializedVersion: 6
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves:${list(rotCurves)}  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:${list(posCurves)}  m_ScaleCurves: []
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
    m_StopTime: ${f(CYCLE_SEC)}
    m_OrientationOffsetY: 0
    m_Level: 0
    m_CycleOffset: 0
    m_HasAdditiveReferencePose: 0
    m_LoopTime: 1
    m_LoopBlend: 0
    m_LoopBlendOrientation: 0
    m_LoopBlendPositionY: 0
    m_LoopBlendPositionXZ: 0
    m_KeepOriginalOrientation: 0
    m_KeepOriginalPositionY: 1
    m_KeepOriginalPositionXZ: 0
    m_HeightFromFeet: 0
    m_Mirror: 0
  m_EditorCurves:${list(editorCurves)}  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events: []
`;

// ---------- 関節表（C#） ----------
const v3 = (a) => `new Vector3(${a.map((v) => `${f(v)}f`).join(", ")})`;
const q4 = (a) => `new Quaternion(${a.map((v) => `${f(v)}f`).join(", ")})`;
const VIS = { none: "Vis.None", sphere: "Vis.Sphere", line: "Vis.Line", wing: "Vis.Wing" };
const cs = `// このファイルは motion/bee_sting/tools/export_unity.mjs が自動生成します。手で編集しないでください。
// BeeSting.anim のカーブはこの階層（Animator を付けた GameObject からの相対パス）に対応します。
using UnityEngine;

public static class BeeRigBones
{
    public enum Vis { None, Sphere, Line, Wing }

    public struct Bone
    {
        public string path;
        public Vector3 restPosition;     // 初期姿勢（クリップで動かない値はこのまま使われる）
        public Quaternion restRotation;
        public Vis vis;
        public float size;               // Sphere: 半径 / Line: 太さ / Wing: 長さ
        public float size2;              // Wing: 幅
        public float offset;             // Sphere: 骨方向(+Y)へのずらし
        public int color;                // 0 黒, 1 黄, 2 琥珀, 3 アクセント, 4 羽

        public Bone(string path, Vector3 restPosition, Quaternion restRotation, Vis vis, float size, float size2, float offset, int color)
        {
            this.path = path; this.restPosition = restPosition; this.restRotation = restRotation;
            this.vis = vis; this.size = size; this.size2 = size2; this.offset = offset; this.color = color;
        }
    }

    public const float CycleSeconds = ${f(CYCLE_SEC)}f;
    public const float HitTime = ${f(HIT_T * CYCLE_SEC)}f;   // 針が最も突き出る時刻（秒）

    // 親が先に来る順
    public static readonly Bone[] Bones =
    {
${joints.map((j) => `        new Bone("${j.path}", ${v3(j.rest.pos)}, ${q4(j.rest.rot)}, ${VIS[j.vis]}, ${f(j.size)}f, ${f(j.size2)}f, ${f(j.offset)}f, ${j.color}),`).join("\n")}
    };
}
`;

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "BeeSting.anim"), anim);
fs.writeFileSync(path.join(outDir, "BeeRigBones.cs"), cs);
const kb = (fs.statSync(path.join(outDir, "BeeSting.anim")).size / 1024).toFixed(0);
const risky = joints.filter((j) => j.frame === "aim" && j.refWorst > 0.95).map((j) => j.name);
if (risky.length) console.warn(`注意: ねじれ基準と平行に近づく関節があります: ${risky.join(", ")}`);
console.log(`関節 ${joints.length} 個（回転カーブ ${nRot} / 位置カーブ ${nPos}）/ 周期 ${CYCLE_SEC} 秒 / ${kb} KB`);
console.log(`出力: ${path.relative(process.cwd(), outDir)}/BeeSting.anim, BeeRigBones.cs`);
