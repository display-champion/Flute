// 魔術師の術発動モーションを Unity 用アセットに書き出す。
//
//   node motion/mage_cast/tools/export_unity.mjs
//
// motion/mage_cast/mage_cast.html の ==POSE-BEGIN== 〜 ==POSE-END== にある姿勢計算をそのまま使い、
// 以下を motion/mage_cast/unity/ に出力する（追加パッケージ不要）。
//   MageCast.anim     … Generic リグ用のループ AnimationClip（待機 → 掲げる → ゆらゆら → 振り下ろして発動 → 戻る）
//   MageRigBones.cs   … クリップと対応する関節階層・初期姿勢・見た目の指定（MageRig.cs が参照）

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const motionDir = path.resolve(here, "..");
const outDir = path.join(motionDir, "unity");

// ---------- HTML から姿勢計算を取り出す ----------
const html = fs.readFileSync(path.join(motionDir, "mage_cast.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("mage_cast.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const lib = new Function(`${m[1]}\nreturn { pose, CYCLE_SEC, HEAD_R, HAT_R, HAT_H, T_CAST, T_SWAY0, T_SWAY1, T_ORB_END,
  TRACKS: [ARM_E, ARM_A, ARM_R, WRIST, LEAN, HEAD_UP, CROUCH, STEP, LIFT, ORB_R, ORB_UP, ORB_FWD] };`)();
const { pose, CYCLE_SEC, HEAD_R, HAT_R, HAT_H, T_CAST, T_SWAY0, T_SWAY1, T_ORB_END, TRACKS } = lib;

// キーの時刻：普段は 20 回/秒、振りかぶり〜発動直後（速く動く区間）だけ 90 回/秒
const RATE = 20, FAST_RATE = 90, FAST_FROM = 0.69, FAST_TO = 0.82;

// ---------- 関節階層（名前は Unity の Humanoid ボーン名に合わせる） ----------
// frame: "aim"（+Y を aim 関節へ向ける）/ "axes"（Y, Z を直接指定）/ "inherit"（親と同じ向き）
// vis:   Unity 側の見た目。sphere / line（親からこの関節まで）/ hat / none
// color: 0 体, 1 帽子, 2 アクセント, 3 魔力
const COL = { body: 0, hat: 1, accent: 2, magic: 3 };
const joints = [];
const J = (o) => joints.push({ vis: "none", size: 0, size2: 0, offset: 0, color: 0, ...o });

J({ name: "Hips", parent: null, get: (P) => P.pelvis, frame: "aim", aim: "Spine" });
J({ name: "Spine", parent: "Hips", get: (P) => P.mid, frame: "aim", aim: "Chest", vis: "line", size: 0.055 });
J({ name: "Chest", parent: "Spine", get: (P) => P.chest, frame: "aim", aim: "Neck", vis: "line", size: 0.055 });
J({ name: "Neck", parent: "Chest", get: (P) => P.neck, frame: "aim", aim: "Head", vis: "line", size: 0.05 });
J({ name: "Head", parent: "Neck", get: (P) => P.head, frame: "axes", axes: (P) => ({ Y: P.headAxis, Z: P.face }),
  vis: "hat", size: HEAD_R, color: COL.body });
["Left", "Right"].forEach((side, i) => {
  J({ name: `${side}Eye`, parent: "Head", get: (P) => P.eyes[i], frame: "inherit", vis: "sphere", size: 0.018, color: COL.magic });
});
["Left", "Right"].forEach((side, i) => {
  const A = (P) => P.arms[i];
  J({ name: `${side}UpperArm`, parent: "Chest", get: (P) => A(P).shoulder, frame: "aim", aim: `${side}LowerArm`, vis: "line", size: 0.05 });
  J({ name: `${side}LowerArm`, parent: `${side}UpperArm`, get: (P) => A(P).elbow, frame: "aim", aim: `${side}Hand`, vis: "line", size: 0.048 });
  J({ name: `${side}Hand`, parent: `${side}LowerArm`, get: (P) => A(P).wrist, frame: "aim", aim: `${side}HandTip`, vis: "line", size: 0.044 });
  J({ name: `${side}HandTip`, parent: `${side}Hand`, get: (P) => A(P).palm, frame: "aim", aim: `${side}Finger2`, vis: "line", size: 0.04 });
  for (let k = 0; k < 3; k++) {
    J({ name: `${side}Finger${k + 1}`, parent: `${side}HandTip`, get: (P) => A(P).fingers[k], frame: "inherit", vis: "line", size: 0.018 });
  }
});
["Left", "Right"].forEach((side, i) => {
  const L = (P) => P.legs[i];
  J({ name: `${side}UpperLeg`, parent: "Hips", get: (P) => L(P).hip, frame: "aim", aim: `${side}LowerLeg`, vis: "line", size: 0.05 });
  J({ name: `${side}LowerLeg`, parent: `${side}UpperLeg`, get: (P) => L(P).knee, frame: "aim", aim: `${side}Foot`, vis: "line", size: 0.05 });
  J({ name: `${side}Foot`, parent: `${side}LowerLeg`, get: (P) => L(P).ankle, frame: "aim", aim: `${side}Toes`, vis: "line", size: 0.045 });
  J({ name: `${side}Toes`, parent: `${side}Foot`, get: (P) => L(P).toe, frame: "inherit", vis: "line", size: 0.04 });
});
// 魔力の玉：直径 1 の球をスケールで大きさを変える（0 のときは消えている）
J({ name: "Orb", parent: null, get: (P) => P.orb, frame: "identity", scale: (P) => P.orbR * 2, vis: "sphere", size: 0.5, color: COL.magic });

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

// aim 関節のねじれ基準：前・上・横のうち、全フレームを通して骨と平行に最も近づかない軸
const AXES = { fwd: [0, 0, 1], up: [0, 1, 0], right: [1, 0, 0] };
const probe = Array.from({ length: 400 }, (_, i) => pose(i / 400));
for (const j of joints) {
  if (j.frame !== "aim") continue;
  let best = null;
  for (const kind of Object.keys(AXES)) {
    let worst = 0;
    for (const P of probe) worst = Math.max(worst, Math.abs(dot3(norm3(sub3(arr(byName[j.aim].get(P)), arr(j.get(P)))), AXES[kind])));
    if (!best || worst < best.worst - 1e-9) best = { kind, worst };
  }
  j.ref = best.kind;
  j.refWorst = best.worst;
}

// 時刻 u（0〜1）の各関節のローカル位置・回転・スケール
function localAt(u) {
  const P = pose(((u % 1) + 1) % 1);
  const world = {};
  for (const j of joints) {
    const pos = arr(j.get(P));
    let rot;
    if (j.frame === "axes") { const a = j.axes(P); rot = fromAxes(arr(a.Y), arr(a.Z)); }
    else if (j.frame === "aim") rot = fromAxes(sub3(arr(byName[j.aim].get(P)), pos), AXES[j.ref]);
    else if (j.frame === "identity") rot = [0, 0, 0, 1];
    else rot = world[j.parent].rot;
    world[j.name] = { pos, rot };
  }
  const local = {};
  for (const j of joints) {
    const w = world[j.name];
    const scl = j.scale ? j.scale(P) : 1;
    if (!j.parent) { local[j.name] = { ...w, scl: [scl, scl, scl] }; continue; }
    const p = world[j.parent];
    const inv = qInv(p.rot);
    local[j.name] = { pos: qRot(inv, sub3(w.pos, p.pos)), rot: j.frame === "inherit" ? [0, 0, 0, 1] : qMul(inv, w.rot), scl: [scl, scl, scl] };
  }
  return local;
}

// ---------- キー作成（傾きは前後の微小時間から求める） ----------
const EPS = 1e-4;
const cache = new Map();
const L = (u) => { const k = u.toFixed(9); if (!cache.has(k)) cache.set(k, localAt(u)); return cache.get(k); };

const KEY_TIMES = (() => {
  const ts = new Set();
  const n = Math.round(RATE * CYCLE_SEC);
  for (let i = 0; i <= n; i++) { const u = i / n; if (u <= FAST_FROM || u >= FAST_TO) ts.add(u.toFixed(9)); }
  const m = Math.round(FAST_RATE * CYCLE_SEC * (FAST_TO - FAST_FROM));
  for (let i = 0; i <= m; i++) ts.add((FAST_FROM + (FAST_TO - FAST_FROM) * i / m).toFixed(9));
  // 動きの区切り（急停止など速度が急に変わる点）は必ずキーにする
  for (const tr of TRACKS) for (const [t] of tr) ts.add(t.toFixed(9));
  ts.add(T_ORB_END.toFixed(9));
  return [...ts].map(Number).sort((x, y) => x - y);
})();

function buildKeys(j) {
  const rot = [], pos = [], scl = [];
  let prevQ = null;
  const dt = EPS * CYCLE_SEC;
  for (const u of KEY_TIMES) {
    const cur = L(u)[j.name], a = L(u - EPS)[j.name], b = L(u + EPS)[j.name];
    let q = cur.rot;
    if (prevQ && qDot(prevQ, q) < 0) q = q.map((v) => -v);
    prevQ = q;
    const align = (r) => (qDot(r, q) < 0 ? r.map((v) => -v) : r);
    const qa = align(a.rot), qb = align(b.rot);
    const time = u * CYCLE_SEC;
    // 入りと出の傾きを別々に（片側差分）とるので、急停止のような折れ目もそのまま再現できる
    const key = (v, va, vb) => ({ time, value: v, inSlope: v.map((_, c) => (v[c] - va[c]) / dt), outSlope: v.map((_, c) => (vb[c] - v[c]) / dt) });
    rot.push(key(q, qa, qb));
    pos.push(key(cur.pos, a.pos, b.pos));
    scl.push(key(cur.scl, a.scl, b.scl));
  }
  return { rot, pos, scl };
}
const spread = (keys) => {
  let d = 0;
  for (const k of keys) for (let c = 0; c < k.value.length; c++) d = Math.max(d, Math.abs(k.value[c] - keys[0].value[c]));
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
    s += `        inSlope: ${vec(k.inSlope, names)}\n        outSlope: ${vec(k.outSlope, names)}\n`;
    s += `        tangentMode: 0\n        weightedMode: 0\n        inWeight: ${w}\n        outWeight: ${w}\n`;
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${pathStr}\n`;
}
function floatCurve(keys, idx, attribute, pathStr) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[idx])}\n`;
    s += `        inSlope: ${f(k.inSlope[idx])}\n        outSlope: ${f(k.outSlope[idx])}\n`;
    s += "        tangentMode: 0\n        weightedMode: 0\n        inWeight: 0.33333334\n        outWeight: 0.33333334\n";
  }
  return s + "      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n" +
    `    attribute: ${attribute}\n    path: ${pathStr}\n    classID: 4\n    script: {fileID: 0}\n`;
}

let rotCurves = "", posCurves = "", sclCurves = "", editorCurves = "";
const counts = { rot: 0, pos: 0, scl: 0 };
for (const j of joints) {
  const { rot, pos, scl } = buildKeys(j);
  if (spread(rot) > 1e-6) {
    counts.rot++;
    rotCurves += vectorCurve(rot, ["x", "y", "z", "w"], j.path);
    ["x", "y", "z", "w"].forEach((c, i) => { editorCurves += floatCurve(rot, i, `m_LocalRotation.${c}`, j.path); });
  }
  if (spread(pos) > 1e-6) {
    counts.pos++;
    posCurves += vectorCurve(pos, ["x", "y", "z"], j.path);
    ["x", "y", "z"].forEach((c, i) => { editorCurves += floatCurve(pos, i, `m_LocalPosition.${c}`, j.path); });
  }
  if (spread(scl) > 1e-6) {
    counts.scl++;
    sclCurves += vectorCurve(scl, ["x", "y", "z"], j.path);
    ["x", "y", "z"].forEach((c, i) => { editorCurves += floatCurve(scl, i, `m_LocalScale.${c}`, j.path); });
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
  m_Name: MageCast
  serializedVersion: 6
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves:${list(rotCurves)}  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:${list(posCurves)}  m_ScaleCurves:${list(sclCurves)}  m_FloatCurves: []
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
const VIS = { none: "Vis.None", sphere: "Vis.Sphere", line: "Vis.Line", hat: "Vis.Hat" };
const cs = `// このファイルは motion/mage_cast/tools/export_unity.mjs が自動生成します。手で編集しないでください。
// MageCast.anim のカーブはこの階層（Animator を付けた GameObject からの相対パス）に対応します。
using UnityEngine;

public static class MageRigBones
{
    public enum Vis { None, Sphere, Line, Hat }

    public struct Bone
    {
        public string path;
        public Vector3 restPosition;     // 初期姿勢（クリップで動かない値はこのまま使われる）
        public Quaternion restRotation;
        public Vector3 restScale;
        public Vis vis;
        public float size;               // Sphere: 半径 / Line: 太さ / Hat: 頭の半径
        public int color;                // 0 体, 1 帽子, 2 アクセント, 3 魔力

        public Bone(string path, Vector3 restPosition, Quaternion restRotation, Vector3 restScale, Vis vis, float size, int color)
        {
            this.path = path; this.restPosition = restPosition; this.restRotation = restRotation; this.restScale = restScale;
            this.vis = vis; this.size = size; this.color = color;
        }
    }

    public const float CycleSeconds = ${f(CYCLE_SEC)}f;
    public const float GatherStartTime = ${f(T_SWAY0 * CYCLE_SEC)}f;   // ゆらゆら（魔力を溜める）開始
    public const float GatherEndTime = ${f(T_SWAY1 * CYCLE_SEC)}f;
    public const float CastTime = ${f(T_CAST * CYCLE_SEC)}f;           // 胸の前へ振り下ろして術が発動する時刻
    public const float HatRadius = ${f(HAT_R)}f;
    public const float HatHeight = ${f(HAT_H)}f;

    // 親が先に来る順
    public static readonly Bone[] Bones =
    {
${joints.map((j) => `        new Bone("${j.path}", ${v3(j.rest.pos)}, ${q4(j.rest.rot)}, ${v3(j.rest.scl)}, ${VIS[j.vis]}, ${f(j.size)}f, ${j.color}),`).join("\n")}
    };
}
`;

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "MageCast.anim"), anim);
fs.writeFileSync(path.join(outDir, "MageRigBones.cs"), cs);
const risky = joints.filter((j) => j.frame === "aim" && j.refWorst > 0.95).map((j) => `${j.name}(${j.refWorst.toFixed(3)})`);
if (risky.length) console.warn(`注意: ねじれ基準と平行に近づく関節があります: ${risky.join(", ")}`);
const kb = (fs.statSync(path.join(outDir, "MageCast.anim")).size / 1024).toFixed(0);
console.log(`関節 ${joints.length} 個（回転 ${counts.rot} / 位置 ${counts.pos} / スケール ${counts.scl} カーブ）/ 周期 ${CYCLE_SEC} 秒 / ${kb} KB`);
console.log(`出力: ${path.relative(process.cwd(), outDir)}/MageCast.anim, MageRigBones.cs`);
