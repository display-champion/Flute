// ダンジョン雑魚（人型以外）のモーションを Unity 用アセットに書き出す。
//
//   node <このフォルダ>/export_unity.mjs
//
// ../dungeon_minor.html の ==POSE-BEGIN== 〜 ==POSE-END== の定義から、
//   ../unity/<体の種類>/<体の種類>_<クリップ名>.anim
//       子「Motion」の位置・回転・大きさ（体全体の動き）と、
//       子「Motion/Limbs/...」の手足の代理の関節の位置（回転なし）を動かす Generic クリップ。
//       攻撃が当たる瞬間などに AnimationEvent（関数 OnMotionEvent、文字列でイベント名）を送る
//   ../unity/LimbRigs.cs   … 体の種類ごとの手足（鎖）の名前と、代理の関節の初期位置（LimbRetarget.cs が使う）
//   ../unity/README.md
// を出力する（追加パッケージ不要）。キーの細かさは、体全体と関節ごとに、補間のずれが許容値に収まるまで自動で上げる。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const baseDir = path.resolve(here, "..");
const outDir = path.join(baseDir, "unity");

const html = fs.readFileSync(path.join(baseDir, "dungeon_minor.html"), "utf8");
const m = html.match(/\/\/ ==POSE-BEGIN==[^\n]*\n([\s\S]*?)\/\/ ==POSE-END==/);
if (!m) throw new Error("dungeon_minor.html に POSE-BEGIN / POSE-END の目印が見つかりません");
const { CLIPS, ENEMIES, BODIES, LIMBS, evalClip, evalLimbs } =
  new Function(`${m[1]}\nreturn { CLIPS, ENEMIES, BODIES, LIMBS, evalClip, evalLimbs };`)();

const RATES = [20, 30, 60, 120, 180, 240];
const BODY_TOLERANCE = 0.001;    // 体全体：軸から 1m 前後の点で 1mm
const JOINT_TOLERANCE = 0.0005;  // 手足の関節：親の関節からの位置で 0.5mm
const EPS = 1e-4;                // 傾きを求める微小時間（秒）

const f = (v) => (Math.abs(v) < 1e-7 ? "0" : Number(v.toPrecision(6)).toString());
const vec = (a, names) => `{${names.map((n, i) => `${n}: ${f(a[i])}`).join(", ")}}`;
const qDot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];

function keyTimes(c, rate) {
  const ts = new Set(c.times.map((t) => t.toFixed(6)));
  const n = Math.max(2, Math.round(rate * c.dur));
  for (let i = 0; i <= n; i++) ts.add((c.dur * i / n).toFixed(6));
  return [...ts].map(Number).filter((t) => t >= 0 && t <= c.dur).sort((a, b) => a - b);
}
// ループは端の外側を反対側から取る（つなぎ目をなめらかに）。1回きりは端で止める
const clampT = (c, u) => (c.loop ? ((u % c.dur) + c.dur) % c.dur : Math.min(Math.max(u, 0), c.dur));

// 入りと出の傾きを別々に（片側差分）とる。折れ目（急停止・着地）もそのまま再現できる
function makeKeys(c, rate, sample, isQuat = false) {
  const keys = [];
  let prev = null;
  for (const t of keyTimes(c, rate)) {
    let v = sample(t);
    if (isQuat && prev && qDot(prev, v) < 0) v = v.map((x) => -x);
    prev = v;
    const align = (r) => (isQuat && qDot(r, v) < 0 ? r.map((x) => -x) : r);
    const a = !c.loop && t - EPS < 0 ? v : align(sample(clampT(c, t - EPS)));
    const b = !c.loop && t + EPS > c.dur ? v : align(sample(clampT(c, t + EPS)));
    keys.push({ time: t, value: v, inSlope: v.map((x, i) => (x - a[i]) / EPS), outSlope: v.map((x, i) => (b[i] - x) / EPS) });
  }
  if (c.loop) { keys[0].inSlope = keys[keys.length - 1].inSlope; keys[keys.length - 1].outSlope = keys[0].outSlope; }
  else { keys[0].inSlope = keys[0].value.map(() => 0); keys[keys.length - 1].outSlope = keys[0].value.map(() => 0); }
  return keys;
}
// Unity と同じエルミート補間
function hermite(keys, t) {
  let i = keys.findIndex((k) => k.time >= t);
  if (i <= 0) return keys[i < 0 ? keys.length - 1 : 0].value;
  const a = keys[i - 1], b = keys[i], h = b.time - a.time, s = (t - a.time) / h;
  const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2;
  return a.value.map((_, j) => h00 * a.value[j] + h10 * h * a.outSlope[j] + h01 * b.value[j] + h11 * h * b.inSlope[j]);
}
const qRotate = (q, v) => {
  const n = Math.hypot(...q); q = q.map((x) => x / n);
  const [x, y, z, w] = q, [vx, vy, vz] = v;
  const tx = 2 * (y * vz - z * vy), ty = 2 * (z * vx - x * vz), tz = 2 * (x * vy - y * vx);
  return [vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx)];
};
const samplesOf = (c) => { const n = Math.max(200, Math.round(c.dur * 400)); return Array.from({ length: n + 1 }, (_, i) => c.dur * i / n); };

// 体全体（Motion）のキー。軸から 1m 前後の点がどれだけずれるかで細かさを決める
function motionKeys(c) {
  const pv = BODIES[c.body].pivot;
  const probes = [[0.8, 0, 0], [-0.5, 0.7, 0.5], [0, -0.6, -0.8]].map((d) => [pv[0] + d[0], pv[1] + d[1], pv[2] + d[2]]);
  const apply = (T, p) => { const r = qRotate(T.rot, [p[0] * T.scl[0], p[1] * T.scl[1], p[2] * T.scl[2]]); return [r[0] + T.pos[0], r[1] + T.pos[1], r[2] + T.pos[2]]; };
  let keys, err, rate;
  for (rate of RATES) {
    keys = {
      rot: makeKeys(c, rate, (t) => evalClip(c, t).rot, true),
      pos: makeKeys(c, rate, (t) => evalClip(c, t).pos),
      scl: makeKeys(c, rate, (t) => evalClip(c, t).scl),
    };
    err = 0;
    for (const t of samplesOf(c)) {
      const want = evalClip(c, t), got = { rot: hermite(keys.rot, t), pos: hermite(keys.pos, t), scl: hermite(keys.scl, t) };
      for (const p of probes) { const a = apply(want, p), g = apply(got, p); err = Math.max(err, Math.hypot(a[0] - g[0], a[1] - g[1], a[2] - g[2])); }
    }
    if (err <= BODY_TOLERANCE) break;
  }
  return { keys, err, rate };
}

// 手足の代理の関節。パスと、親の関節からの位置（鎖の付け根は Limbs から見た位置）
function limbJoints(body) {
  const L = LIMBS[body];
  if (!L) return [];
  const out = [];
  for (const [chain, pts] of Object.entries(L.chains)) {
    pts.forEach((_, i) => out.push({ chain, i, path: `Motion/Limbs/${Array.from({ length: i + 1 }, (_, k) => `${chain}_${k}`).join("/")}` }));
  }
  return out;
}
const jointLocal = (P, j) => (j.i === 0 ? P[j.chain][0] : P[j.chain][j.i].map((v, k) => v - P[j.chain][j.i - 1][k]));
function jointKeys(c, j) {
  const sample = (t) => jointLocal(evalLimbs(c, t), j);
  let keys, err, rate;
  for (rate of RATES) {
    keys = makeKeys(c, rate, sample);
    err = 0;
    for (const t of samplesOf(c)) { const a = sample(t), g = hermite(keys, t); err = Math.max(err, Math.hypot(a[0] - g[0], a[1] - g[1], a[2] - g[2])); }
    if (err <= JOINT_TOLERANCE) break;
  }
  return { keys, err, rate };
}

const spread = (keys) => Math.max(...keys.map((k) => Math.max(...k.value.map((v, i) => Math.abs(v - keys[0].value[i])))));
// 動かない項目は最初と最後の2キーだけにする（省略はしない：クリップを切り替えたとき前の値が残らないように）
const compact = (keys) => (spread(keys) > 1e-6 ? keys : [
  { ...keys[0], inSlope: keys[0].value.map(() => 0), outSlope: keys[0].value.map(() => 0) },
  { ...keys[keys.length - 1], value: keys[0].value, inSlope: keys[0].value.map(() => 0), outSlope: keys[0].value.map(() => 0) },
]);

// キーは time / value / inSlope / outSlope だけ書く（重みは使わないので省く）
function vectorCurve(keys, names, p) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${vec(k.value, names)}\n        inSlope: ${vec(k.inSlope, names)}\n        outSlope: ${vec(k.outSlope, names)}\n`;
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    path: ${p}\n`;
}
function floatCurve(keys, idx, attribute, p) {
  let s = "  - curve:\n      serializedVersion: 2\n      m_Curve:\n";
  for (const k of keys) {
    s += `      - serializedVersion: 3\n        time: ${f(k.time)}\n        value: ${f(k.value[idx])}\n        inSlope: ${f(k.inSlope[idx])}\n        outSlope: ${f(k.outSlope[idx])}\n`;
  }
  return s + `      m_PreInfinity: 2\n      m_PostInfinity: 2\n      m_RotationOrder: 4\n    attribute: ${attribute}\n    path: ${p}\n    classID: 4\n    script: {fileID: 0}\n`;
}
const list = (s) => (s ? `\n${s}` : " []\n");

const report = [];
function animYaml(c) {
  const name = `${c.body}_${c.name}`;
  const mk = motionKeys(c);
  const rot = compact(mk.keys.rot), pos = compact(mk.keys.pos), scl = compact(mk.keys.scl);
  const rotC = vectorCurve(rot, ["x", "y", "z", "w"], "Motion");
  let posC = vectorCurve(pos, ["x", "y", "z"], "Motion");
  const sclC = vectorCurve(scl, ["x", "y", "z"], "Motion");
  let edC = "";
  ["x", "y", "z", "w"].forEach((a, i) => { edC += floatCurve(rot, i, `m_LocalRotation.${a}`, "Motion"); });
  ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(pos, i, `m_LocalPosition.${a}`, "Motion"); });
  ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(scl, i, `m_LocalScale.${a}`, "Motion"); });
  let jointErr = 0, jointRate = 0;
  for (const j of limbJoints(c.body)) {
    const jk = jointKeys(c, j);
    jointErr = Math.max(jointErr, jk.err); jointRate = Math.max(jointRate, jk.rate);
    const ks = compact(jk.keys);
    posC += vectorCurve(ks, ["x", "y", "z"], j.path);
    ["x", "y", "z"].forEach((a, i) => { edC += floatCurve(ks, i, `m_LocalPosition.${a}`, j.path); });
  }
  report.push({ name, bodyErr: mk.err, bodyRate: mk.rate, jointErr, jointRate });
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
  const text = animYaml(c);
  fs.writeFileSync(path.join(dir, `${c.body}_${c.name}.anim`), text);
  total++; bytes += text.length;
}

// ---------- 手足の表（C#） ----------
const bodiesWithLimbs = Object.keys(LIMBS).filter((b) => BODIES[b]);
const v3s = (a) => `new Vector3(${a.map((x) => `${f(x)}f`).join(", ")})`;
const cs = `// このファイルは tools/export_unity.mjs が自動生成します。手で編集しないでください。
// 体の種類ごとの手足（鎖）と、代理の関節の初期位置（Motion から見た位置、m）。
using UnityEngine;

public static class LimbRigs
{
    public struct Chain
    {
        public string name;
        public Vector3[] rest;   // 付け根から先へ

        public Chain(string name, params Vector3[] rest) { this.name = name; this.rest = rest; }
    }

    public static readonly string[] Bodies = { ${bodiesWithLimbs.map((b) => `"${b}"`).join(", ")} };

    public static Chain[] Get(string body)
    {
        switch (body)
        {
${bodiesWithLimbs.map((b) => `            case "${b}": return new[]
            {
${Object.entries(LIMBS[b].chains).map(([n, pts]) => `                new Chain("${n}", ${pts.map(v3s).join(", ")}),`).join("\n")}
            };`).join("\n")}
            default: return new Chain[0];
        }
    }
}
`;
fs.writeFileSync(path.join(outDir, "LimbRigs.cs"), cs);

// ---------- README ----------
let table = "| ID | 名前 | 体の種類 | クリップ（unity/<体>/<体>_<名前>.anim） | 大きさ |\n|---|---|---|---|---|\n";
for (const e of ENEMIES) table += `| ${e.id} | ${e.name} | ${e.body} | ${e.clips.join(" / ")} | ${e.scale}倍 |\n`;
let events = "| クリップ | 長さ | ループ | イベント |\n|---|---|---|---|\n";
for (const c of CLIPS) events += `| ${c.body}_${c.name} | ${c.dur}秒 | ${c.loop ? "する" : "しない"} | ${c.events.map(([t, n]) => `${n}（${t}秒）`).join("、") || "―"} |\n`;
let bodies = "| 体の種類 | 軸の位置（足元が原点） | モデルの置き方 | 手足（LimbRetarget の鎖） |\n|---|---|---|---|\n";
for (const [k, b] of Object.entries(BODIES)) {
  const ch = LIMBS[k] ? Object.entries(LIMBS[k].chains).map(([n, p]) => `${n}（骨${p.length - 1}本）`).join("、") : "―";
  bodies += `| ${k}（${b.name}） | (${b.pivot.join(", ")}) | ${b.note} | ${ch} |\n`;
}
fs.writeFileSync(path.join(outDir, "README.md"), `# ダンジョン雑魚モーション（Unity 用）

\`../dungeon_minor.html\` をブラウザで開くと、敵ごとに全クリップの動き（手足を含む）を確認できます。
このファイルは \`../tools/export_unity.mjs\` が自動生成します（手で編集しても作り直すと消えます）。

人の形をした敵（名前に「人」を含む5体と、人の形の骨で動かす12体）は、人型モデルの骨を動かす別の仕組みです。\`Humanoid/README.md\` を見てください。

## 仕組み

- **体全体**：子 \`Motion\` の位置・回転・伸び縮みで動かします。どのモデルにも付けられます。
- **手足**：\`Motion/Limbs/\` の下の「代理の関節」も動かします。\`LimbRetarget\` が、Inspector で割り当てたモデルの骨を、
  代理の関節の「初期からの向きの変化」と同じだけ回します（モデルの骨の軸や初期の曲がり方が違っても使えます）。
  - 割り当てなかった手足は動きません（体全体の動きだけになります）。
- 構成：\`敵の本体（Animator ＋ EnemyMotion ＋ LimbRetarget）\` → 子 \`Motion\`（体全体）→ モデル
- 回転や伸び縮みの中心（軸）は体の種類ごとに決めてあり、クリップに織り込み済みです（下の表）。
- 敵の大きさ（1.3倍・2倍など）は、敵の本体の Scale で変えてください。動きの幅も一緒に大きくなります。

## 使い方

1. \`EnemyMotion.cs\`・\`LimbRetarget.cs\`・\`LimbRigs.cs\` と、使う体の種類のフォルダ（例：\`Creature/\`）を Assets に置く。
2. 敵の本体の GameObject に \`EnemyMotion\` と \`LimbRetarget\` を付ける（Animator も自動で付きます）。
   - 子に \`Motion\` が無ければ自動で作り、今ある子（モデル）をその下へ移します。
   - モデルは \`Motion\` の下に、足元が原点・+Z が正面になるよう置く（浮く敵は下の表の高さに体の中心を合わせる）。
3. **Clips** にその敵のクリップを入れる（下の「敵ごとのクリップ」）。
4. \`LimbRetarget\` の **Body** に体の種類（例：Creature）を入れると、**Chains** に手足の欄が並びます。
   各欄の **Bones** に、付け根から先へ順にモデルの骨を入れてください（例：LegFL なら 前左脚の付け根・ひじ（ひざ））。
   骨の本数は下の表の「骨○本」です。足りない分は空のままで構いません。
5. ゲーム側から \`GetComponent<EnemyMotion>().Play("Attack_Bite")\` のように名前の末尾で再生する。
   - \`Play("Death")\` で Death_SporeBurst、\`Play("Move")\` で Move_Flee なども再生されるので、どの敵も同じ名前（Idle / Move / Hit / Death）で呼べます。
   - 1回きりのクリップが終わると自動で待機（Idle）に戻ります。名前に Death を含むクリップは最後の姿勢で止まります。
6. **On Motion Event** に処理をつなぐと、攻撃が当たる瞬間などにイベント名（Hit / Stomp など）付きで呼ばれます。
   **On Motion Finished** は1回きりのクリップが終わったときに呼ばれます。

長い突進（ハチの Attack_Charge）、転がり（岩・樽の Attack_Roll）、大跳躍（Attack_Pounce）、跳ねての体当たり（Attack_LeapTackle）は、
クリップはその場で「構え → 突進中の姿勢 → 止まる」だけを動かします。イベントの間にゲーム側で敵の本体を前へ動かしてください。
短い飛びかかり・噛みつき・刺す動きは、クリップの中で前に出て元の位置に戻ります。

## 敵ごとのクリップ

${table}
## クリップ一覧

${events}
## 体の種類と手足

${bodies}
## 作り直し方

\`../dungeon_minor.html\` の \`==POSE-BEGIN==\`〜\`==POSE-END==\` にクリップと手足の定義があります。編集したら次を実行すると .anim・LimbRigs.cs・この README が作り直されます（Node.js のみ必要）。

\`\`\`
node <dungeon_minor フォルダ>/tools/export_unity.mjs
\`\`\`

## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面や見た目を教えてください。
- 手足の初期の向きは、代理の関節とモデルで違っていても構いません（向きの「変化」だけを写すため）。ただし、代理の関節とモデルで骨の付き方（どちらへ伸びているか）が大きく違うと、曲がる向きがずれることがあります。
`);

const worstB = report.reduce((a, b) => (b.bodyErr > a.bodyErr ? b : a));
const worstJ = report.reduce((a, b) => (b.jointErr > a.jointErr ? b : a));
console.log(`クリップ ${total} 本 / 合計 ${(bytes / 1024).toFixed(0)} KB → ${path.relative(process.cwd(), outDir)}`);
console.log(`体全体のずれ 最大 ${(worstB.bodyErr * 1000).toFixed(3)} mm（${worstB.name}）／ 手足の関節のずれ 最大 ${(worstJ.jointErr * 1000).toFixed(3)} mm（${worstJ.name}）`);
console.log(`手足のキーが 120/秒 以上のクリップ: ${report.filter((r) => r.jointRate >= 120).map((r) => `${r.name}(${r.jointRate})`).join(", ") || "なし"}`);
if (report.some((r) => r.bodyErr > BODY_TOLERANCE || r.jointErr > JOINT_TOLERANCE)) console.warn("注意: 許容値を超えたクリップがあります");
