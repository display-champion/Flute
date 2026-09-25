// 獣走りモーションを Unity 用アセットに書き出す。
//
//   node motion/beast_run/tools/export_unity.mjs
//
// motion/beast_run/beast_run.html の ==POSE-BEGIN== 〜 ==POSE-END== にある姿勢計算をそのまま使い、
// 以下を motion/beast_run/unity/ に出力する（追加パッケージ不要）。
//   BeastRun.anim      … Generic リグ用のループ AnimationClip（各関節の localPosition / localRotation）
//   BeastRigBones.cs   … クリップと対応する関節階層（BeastRig.cs が参照）

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const motionDir = path.resolve(here, "..");
const outDir = path.join(motionDir, "unity");

// ---------- HTML から姿勢計算を取り出す ----------
const html = fs.readFileSync(path.join(motionDir, "beast_run.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("beast_run.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const lib = new Function(`${m[1]}\nreturn { pose, STRIDE, BASE_FREQ, HEAD_R };`)();
const { pose, STRIDE, BASE_FREQ, HEAD_R } = lib;

const KEYS = 30;                   // 1周期あたりのキー数
const DURATION = 1 / BASE_FREQ;    // 1周期の秒数（速度1）

// ---------- 関節階層 ----------
// name, parent, 世界座標を返す関数, 骨の向きを決める子関節（null なら親の向きを継ぐ）
const joints = [];
const J = (name, parent, get, aim = null) => joints.push({ name, parent, get, aim });

J("Hips", null, (P) => P.pelvis, "Spine");
J("Spine", "Hips", (P) => P.mid, "Chest");
J("Chest", "Spine", (P) => P.chest, "Neck");
J("Neck", "Chest", (P) => P.neck, "Head");
J("Head", "Neck", (P) => P.head);
for (const [sfx, s] of [["L", -1], ["R", 1]]) {
  J(`Eye_${sfx}`, "Head", (P) => ({ x: P.head.x + s * 0.05, y: P.head.y + 0.015, z: P.head.z + HEAD_R * 0.92 }));
}
for (const [sfx, key] of [["L", "la"], ["R", "ra"]]) {
  J(`Shoulder_${sfx}`, "Chest", (P) => P[key].shoulder, `Elbow_${sfx}`);
  J(`Elbow_${sfx}`, `Shoulder_${sfx}`, (P) => P[key].elbow, `Wrist_${sfx}`);
  J(`Wrist_${sfx}`, `Elbow_${sfx}`, (P) => P[key].wrist, `Claw${sfx}2_a`);
  // claws[0..3] = 爪4本（各3関節）, claws[4] = 親指（2関節）
  for (let c = 0; c < 5; c++) {
    const base = c < 4 ? `Claw${sfx}${c + 1}` : `Thumb${sfx}`;
    const n = c < 4 ? 3 : 2;
    for (let k = 0; k < n; k++) {
      const name = `${base}_${"abc"[k]}`;
      const parent = k === 0 ? `Wrist_${sfx}` : `${base}_${"abc"[k - 1]}`;
      const next = k < n - 1 ? `${base}_${"abc"[k + 1]}` : null;
      J(name, parent, (P) => P[key].claws[c][k + 1], next);
    }
  }
}
for (const [sfx, key] of [["L", "L"], ["R", "R"]]) {
  J(`Hip_${sfx}`, "Hips", (P) => P[key].hip, `Knee_${sfx}`);
  J(`Knee_${sfx}`, `Hip_${sfx}`, (P) => P[key].knee, `Ankle_${sfx}`);
  J(`Ankle_${sfx}`, `Knee_${sfx}`, (P) => P[key].ankle, `Toe_${sfx}`);
  J(`Toe_${sfx}`, `Ankle_${sfx}`, (P) => P[key].toe);
}
const byName = Object.fromEntries(joints.map((j) => [j.name, j]));
const pathOf = (j) => (j.parent ? `${pathOf(byName[j.parent])}/${j.name}` : j.name);
for (const j of joints) j.path = pathOf(j);

// ---------- 数学 ----------
const sub = (a, b) => [a.x - b.x, a.y - b.y, a.z - b.z];
const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm3 = (a) => { const l = Math.hypot(...a) || 1; return a.map((v) => v / l); };
const FWD = [0, 0, 1], UP = [0, 1, 0];

// 列ベクトル X,Y,Z の回転行列 → クォータニオン [x,y,z,w]（Unity と同じ規約）
function matToQuat(X, Y, Z) {
  const m00 = X[0], m10 = X[1], m20 = X[2];
  const m01 = Y[0], m11 = Y[1], m21 = Y[2];
  const m02 = Z[0], m12 = Z[1], m22 = Z[2];
  const tr = m00 + m11 + m22;
  let x, y, z, w;
  if (tr > 0) {
    const s = Math.sqrt(tr + 1) * 2;
    w = 0.25 * s; x = (m21 - m12) / s; y = (m02 - m20) / s; z = (m10 - m01) / s;
  } else if (m00 > m11 && m00 > m22) {
    const s = Math.sqrt(1 + m00 - m11 - m22) * 2;
    w = (m21 - m12) / s; x = 0.25 * s; y = (m01 + m10) / s; z = (m02 + m20) / s;
  } else if (m11 > m22) {
    const s = Math.sqrt(1 + m11 - m00 - m22) * 2;
    w = (m02 - m20) / s; x = (m01 + m10) / s; y = 0.25 * s; z = (m12 + m21) / s;
  } else {
    const s = Math.sqrt(1 + m22 - m00 - m11) * 2;
    w = (m10 - m01) / s; x = (m02 + m20) / s; y = (m12 + m21) / s; z = 0.25 * s;
  }
  return [x, y, z, w];
}
const qMul = (a, b) => [
  a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
  a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
  a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
  a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
];
const qInv = (q) => [-q[0], -q[1], -q[2], q[3]];
const qRot = (q, v) => { const r = qMul(qMul(q, [v[0], v[1], v[2], 0]), qInv(q)); return [r[0], r[1], r[2]]; };

// 骨の +Y を子関節へ向ける。ねじれの基準は全フレームで平行にならない方（前 or 上）に固定する。
const sampleTimes = [];
for (let k = -1; k <= KEYS + 1; k++) sampleTimes.push(k / KEYS);
const poses = sampleTimes.map((t) => pose(((t % 1) + 1) % 1));
for (const j of joints) {
  if (!j.aim) continue;
  let worst = 0;
  for (const P of poses) worst = Math.max(worst, Math.abs(dot3(norm3(sub(byName[j.aim].get(P), j.get(P))), FWD)));
  j.ref = worst > 0.85 ? UP : FWD;
}

function frame(P) {
  const world = {};
  for (const j of joints) {
    const pos = j.get(P);
    let rot;
    if (j.aim) {
      const Y = norm3(sub(byName[j.aim].get(P), pos));
      const X = norm3(cross3(Y, j.ref));
      const Z = cross3(X, Y);
      rot = matToQuat(X, Y, Z);
    } else {
      rot = world[j.parent].rot;   // 末端は親の向きを継ぐ
    }
    world[j.name] = { pos: [pos.x, pos.y, pos.z], rot };
  }
  const local = {};
  for (const j of joints) {
    const w = world[j.name];
    if (!j.parent) { local[j.name] = w; continue; }
    const p = world[j.parent];
    const inv = qInv(p.rot);
    const lp = qRot(inv, [w.pos[0] - p.pos[0], w.pos[1] - p.pos[1], w.pos[2] - p.pos[2]]);
    const lr = j.aim ? qMul(inv, w.rot) : [0, 0, 0, 1];
    local[j.name] = { pos: lp, rot: lr };
  }
  return local;
}

const frames = poses.map(frame);
// クォータニオンの符号を連続させる（補間が遠回りしないように）
for (const j of joints) {
  for (let i = 1; i < frames.length; i++) {
    const a = frames[i - 1][j.name].rot, b = frames[i][j.name].rot;
    if (dot3(a, b) + a[3] * b[3] < 0) frames[i][j.name].rot = b.map((v) => -v);
  }
}

// ---------- .anim（YAML）書き出し ----------
const f = (v) => {
  if (Math.abs(v) < 1e-7) return "0";
  return Number(v.toPrecision(7)).toString();
};
const dt = DURATION / KEYS;
// frames[0] は t=-1/KEYS、frames[1..KEYS+1] が t=0..DURATION のキー
function keysFor(getter) {
  const keys = [];
  for (let k = 0; k <= KEYS; k++) {
    const prev = getter(frames[k]), cur = getter(frames[k + 1]), next = getter(frames[k + 2]);
    keys.push({ time: k * dt, value: cur, slope: cur.map((_, i) => (next[i] - prev[i]) / (2 * dt)) });
  }
  return keys;
}
const vec = (a, names) => `{${names.map((n, i) => `${n}: ${f(a[i])}`).join(", ")}}`;

function vectorCurve(keys, names, pathStr) {
  const w = vec(names.map(() => 1 / 3), names);
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${vec(k.value, names)}\n`;
    s += `        inSlope: ${vec(k.slope, names)}\n        outSlope: ${vec(k.slope, names)}\n`;
    s += `        tangentMode: 0\n        weightedMode: 0\n        inWeight: ${w}\n        outWeight: ${w}\n`;
  }
  s += `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${pathStr}\n`;
  return s;
}
function floatCurve(keys, idx, attribute, pathStr) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[idx])}\n`;
    s += `        inSlope: ${f(k.slope[idx])}\n        outSlope: ${f(k.slope[idx])}\n`;
    s += "        tangentMode: 0\n        weightedMode: 0\n        inWeight: 0.33333334\n        outWeight: 0.33333334\n";
  }
  s += "      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n";
  s += `    attribute: ${attribute}\n    path: ${pathStr}\n    classID: 4\n    script: {fileID: 0}\n`;
  return s;
}

let rotCurves = "", posCurves = "", editorCurves = "";
for (const j of joints) {
  const rk = keysFor((fr) => fr[j.name].rot);
  const pk = keysFor((fr) => fr[j.name].pos);
  rotCurves += vectorCurve(rk, ["x", "y", "z", "w"], j.path);
  posCurves += vectorCurve(pk, ["x", "y", "z"], j.path);
  ["x", "y", "z"].forEach((c, i) => { editorCurves += floatCurve(pk, i, `m_LocalPosition.${c}`, j.path); });
  ["x", "y", "z", "w"].forEach((c, i) => { editorCurves += floatCurve(rk, i, `m_LocalRotation.${c}`, j.path); });
}

const anim = `%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!74 &7400000
AnimationClip:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: BeastRun
  serializedVersion: 6
  m_Legacy: 0
  m_Compressed: 0
  m_UseHighQualityCurve: 1
  m_RotationCurves:
${rotCurves}  m_CompressedRotationCurves: []
  m_EulerCurves: []
  m_PositionCurves:
${posCurves}  m_ScaleCurves: []
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
    m_StopTime: ${f(DURATION)}
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
  m_EditorCurves:
${editorCurves}  m_EulerEditorCurves: []
  m_HasGenericRootTransform: 0
  m_HasMotionFloatCurves: 0
  m_Events: []
`;

// ---------- 関節表（C#） ----------
const cs = `// このファイルは motion/beast_run/tools/export_unity.mjs が自動生成します。手で編集しないでください。
// BeastRun.anim のカーブはこの階層（Animator を付けた GameObject からの相対パス）に対応します。
public static class BeastRigBones
{
    // 1周期で進む距離 (m) と、速度1での1秒あたりの周期数
    public const float Stride = ${f(STRIDE)}f;
    public const float CyclesPerSecond = ${f(BASE_FREQ)}f;
    public const float HeadRadius = ${f(HEAD_R)}f;

    // 親が先に来る順
    public static readonly string[] Paths =
    {
${joints.map((j) => `        "${j.path}",`).join("\n")}
    };
}
`;

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "BeastRun.anim"), anim);
fs.writeFileSync(path.join(outDir, "BeastRigBones.cs"), cs);

// 検算用に、キーから世界座標を組み立て直して元の姿勢との誤差を出す
let maxErr = 0;
for (let k = 0; k <= KEYS; k++) {
  const fr = frames[k + 1];
  const P = poses[k + 1];
  const world = {};
  for (const j of joints) {
    const l = fr[j.name];
    if (!j.parent) { world[j.name] = { pos: l.pos, rot: l.rot }; continue; }
    const p = world[j.parent];
    const d = qRot(p.rot, l.pos);
    world[j.name] = { pos: [p.pos[0] + d[0], p.pos[1] + d[1], p.pos[2] + d[2]], rot: qMul(p.rot, l.rot) };
    const g = j.get(P);
    maxErr = Math.max(maxErr, Math.hypot(world[j.name].pos[0] - g.x, world[j.name].pos[1] - g.y, world[j.name].pos[2] - g.z));
  }
}
console.log(`関節 ${joints.length} 個 / キー ${KEYS + 1} 個 / 周期 ${DURATION.toFixed(4)} 秒 / 再構成誤差 ${maxErr.toExponential(2)} m`);
console.log(`出力: ${path.relative(process.cwd(), outDir)}/BeastRun.anim, BeastRigBones.cs`);
