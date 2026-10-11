"""ガレスのテストモーション（キーポーズだけ）を作り、Cascadeur に読み込む FBX を書き出す。

HELLEDEN の export_cascadeur_rig.py と同じく、Blender をバックグラウンドで動かして使う:

  blender -b -P cascadeur/gareth_test/make_test_motion.py -- ^
      --input D:/HELLEDEN/Cascadeur/rigs/gareth_cascadeur.fbx ^
      --outdir D:/HELLEDEN/Cascadeur/export/gareth_test

入力は Cascadeur 用に整えた FBX（骨の名前が Mixamo 式、T ポーズ）。フィナの
fina_cascadeur.fbx と同じ形式を想定している。

出力（クリップごと）:
  <clip>_keys.fbx   キーポーズだけを持つアニメーション（メッシュなし）。
                    キーとキーの間は「直前のポーズのまま」（ステップ補間）。
                    Cascadeur で間を補間（Inbetweening / AutoPhysics）させる前提
  <clip>_keys.svg   キーポーズの横・正面からの棒人間図（読み込む前の確認用）
  <clip>_keys.txt   キーのフレーム番号とポーズ名（Cascadeur での作業用）

ポーズは骨の向きではなく「キャラクターの前・上・左」を基準に書いてあるので、
Mixamo 式の骨であれば体格が違っても同じ動きになる。
"""

import argparse
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

FPS = 30

# Mixamo 式の骨（接頭辞 "mixamorig:" などは無視して照合する）
REQUIRED = [
    "Hips", "Spine", "Neck", "Head",
    "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot",
    "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand",
]
SPINES = ["Spine", "Spine1", "Spine2"]

# ---------------------------------------------------------------------------
# ポーズの書き方
#   hips      腰の移動 (前, 上, 左)。単位は「腰の高さ」（1.0 = 立った時の腰の高さ）
#   hips_rot  腰の回転 (前傾, 左向き, 右へ傾く) 度
#   spine     背骨全体の回転 (前傾, 左向き, 右へ傾く) 度。背骨の骨に等分する
#   head      首と頭の回転 (うつむく, 左向き, 右へ傾く) 度
#   arm_L/R   上腕 upper と前腕 fore の向き (前, 上, 左)。胸の向きが基準
#             "space": "world" を付けると、体のひねりに関係なく地面に対する向きになる
#   foot_L/R  足首の位置 pos (前, 上, 左)。立った時の位置からのずれ（腰の高さ単位）
#             pitch はつま先の上げ下げ（度、正でつま先が下がる）
# 書かなかった項目は「立ったまま」になる（腕だけは下ろした形）
# ---------------------------------------------------------------------------
ARMS_DOWN = {
    "arm_L": {"upper": (0.05, -1, 0.18), "fore": (0.25, -1, 0.05)},
    "arm_R": {"upper": (0.05, -1, -0.18), "fore": (0.25, -1, -0.05)},
}


def pose(**kw):
    p = dict(ARMS_DOWN)
    p.update(kw)
    return p


CLIPS = {
    # 名前に jump を含むので、HELLEDEN の取り込みでは高さ (Y) の動きが残る
    "gareth_test_jump": [
        (0, "立ち", pose()),
        (8, "溜め（しゃがむ）", pose(
            hips=(-0.04, -0.28, 0), hips_rot=(18, 0, 0), spine=(22, 0, 0), head=(-20, 0, 0),
            arm_L={"upper": (-0.6, -0.8, 0.2), "fore": (-0.2, -1, 0.05)},
            arm_R={"upper": (-0.6, -0.8, -0.2), "fore": (-0.2, -1, -0.05)})),
        (12, "踏み切り（伸び上がる）", pose(
            hips=(0.04, 0.06, 0), hips_rot=(-4, 0, 0), spine=(-6, 0, 0), head=(-8, 0, 0),
            arm_L={"upper": (0.5, 1, 0.15), "fore": (0.4, 1, 0.05)},
            arm_R={"upper": (0.5, 1, -0.15), "fore": (0.4, 1, -0.05)},
            foot_L={"pos": (0, 0.06, 0), "pitch": 40}, foot_R={"pos": (0, 0.06, 0), "pitch": 40})),
        (20, "頂点（膝を抱える）", pose(
            hips=(0.08, 0.62, 0), hips_rot=(10, 0, 0), spine=(14, 0, 0), head=(-6, 0, 0),
            arm_L={"upper": (0.7, 0.3, 0.45), "fore": (0.6, 0.6, 0.1)},
            arm_R={"upper": (0.7, 0.3, -0.45), "fore": (0.6, 0.6, -0.1)},
            foot_L={"pos": (0.12, 0.92, 0.02), "pitch": 15}, foot_R={"pos": (0.12, 0.92, -0.02), "pitch": 15})),
        (28, "着地の瞬間", pose(
            hips=(0.1, -0.02, 0), hips_rot=(6, 0, 0), spine=(6, 0, 0),
            arm_L={"upper": (0.4, -0.3, 0.6), "fore": (0.5, 0, 0.3)},
            arm_R={"upper": (0.4, -0.3, -0.6), "fore": (0.5, 0, -0.3)},
            foot_L={"pos": (0.1, 0, 0)}, foot_R={"pos": (0.1, 0, 0)})),
        (32, "着地の沈み込み", pose(
            hips=(0.06, -0.34, 0), hips_rot=(24, 0, 0), spine=(24, 0, 0), head=(-24, 0, 0),
            arm_L={"upper": (0.5, -0.6, 0.45), "fore": (0.6, -0.3, 0.1)},
            arm_R={"upper": (0.5, -0.6, -0.45), "fore": (0.6, -0.3, -0.1)},
            foot_L={"pos": (0.1, 0, 0)}, foot_R={"pos": (0.1, 0, 0)})),
        (44, "立ち直り", pose(hips=(0.1, 0, 0), foot_L={"pos": (0.1, 0, 0)}, foot_R={"pos": (0.1, 0, 0)})),
    ],
    # 1 回再生（前後の移動は体に焼き込む）。振り抜きは 3 フレームで一気に
    "gareth_test_punch": [
        (0, "構え", pose(
            hips=(0, -0.06, 0), hips_rot=(4, 25, 0), spine=(6, -10, 0), head=(0, -15, 0),
            arm_L={"upper": (0.45, -0.75, 0.2), "fore": (0.6, 0.8, -0.05)},
            arm_R={"upper": (0.1, -0.85, -0.3), "fore": (0.75, 0.6, 0.05)},
            foot_L={"pos": (0.22, 0, 0.04)}, foot_R={"pos": (-0.18, 0, -0.04), "pitch": 15})),
        (6, "引き（溜め）", pose(
            hips=(-0.03, -0.1, 0), hips_rot=(6, 35, 0), spine=(8, -5, 0), head=(0, -30, 0),
            arm_L={"upper": (0.6, -0.6, 0.1), "fore": (0.5, 0.85, -0.2)},
            arm_R={"upper": (-0.5, -0.75, -0.3), "fore": (0.7, 0.4, 0.05)},
            foot_L={"pos": (0.22, 0, 0.04)}, foot_R={"pos": (-0.18, 0, -0.04), "pitch": 20})),
        (9, "打ち抜き", pose(
            hips=(0.1, -0.08, 0), hips_rot=(8, -20, 0), spine=(10, -20, 0), head=(0, 10, 0),
            arm_L={"upper": (-0.3, -0.8, 0.3), "fore": (0.6, 0.6, 0.1)},
            arm_R={"upper": (1, 0.05, 0.04), "fore": (1, 0.05, 0.02), "space": "world"},
            foot_L={"pos": (0.24, 0, 0.04)}, foot_R={"pos": (-0.1, 0.02, -0.04), "pitch": 35})),
        (15, "止め", pose(
            hips=(0.12, -0.1, 0), hips_rot=(10, -24, 0), spine=(12, -22, 0), head=(0, 12, 0),
            arm_L={"upper": (-0.3, -0.8, 0.3), "fore": (0.6, 0.6, 0.1)},
            arm_R={"upper": (1, 0.0, 0.04), "fore": (1, 0.02, 0.02), "space": "world"},
            foot_L={"pos": (0.24, 0, 0.04)}, foot_R={"pos": (-0.1, 0.02, -0.04), "pitch": 35})),
        (26, "構えに戻る", pose(
            hips=(0, -0.06, 0), hips_rot=(4, 25, 0), spine=(6, -10, 0), head=(0, -15, 0),
            arm_L={"upper": (0.45, -0.75, 0.2), "fore": (0.6, 0.8, -0.05)},
            arm_R={"upper": (0.1, -0.85, -0.3), "fore": (0.75, 0.6, 0.05)},
            foot_L={"pos": (0.22, 0, 0.04)}, foot_R={"pos": (-0.18, 0, -0.04), "pitch": 15})),
    ],
}


# ---------------------------------------------------------------------------
# 骨格の読み取り
# ---------------------------------------------------------------------------
class Rig:
    def __init__(self, arm):
        self.arm = arm
        self.names = {}
        for b in arm.data.bones:
            self.names.setdefault(b.name.split(":")[-1], b.name)
        missing = [n for n in REQUIRED if n not in self.names]
        if missing:
            raise SystemExit("Mixamo 式の骨が見つかりません: %s\n骨の一覧: %s"
                             % (", ".join(missing), ", ".join(sorted(self.names))))
        self.spines = [n for n in SPINES if n in self.names]
        bone = lambda n: arm.data.bones[self.names[n]]
        self.rest_head = {n: bone(n).head_local.copy() for n in self.names}
        self.rest_rot = {n: bone(n).matrix_local.to_3x3() for n in self.names}

        h = self.rest_head
        self.left = (h["LeftUpLeg"] - h["RightUpLeg"]).normalized()
        up = h["Head"] - h["Hips"]
        self.up = (up - self.left * up.dot(self.left)).normalized()
        self.fwd = self.left.cross(self.up)
        ground = (h["LeftFoot"] + h["RightFoot"]) / 2
        self.hip_h = (h["Hips"] - ground).dot(self.up)

    def pb(self, n):
        return self.arm.pose.bones[self.names[n]]

    def vec(self, flu, frame=None):
        f, u, l = flu
        v = self.fwd * f + self.up * u + self.left * l
        return frame @ v if frame is not None else v


def update():
    bpy.context.view_layer.update()


def axis_rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def turn(rig, pyr, parent):
    """親の回転 parent を基準に (前傾, 左向き, 右へ傾く) だけ回した回転を返す。"""
    pitch, yaw, roll = pyr
    d = (axis_rot(parent @ rig.left, pitch) @ axis_rot(parent @ rig.up, yaw)
         @ axis_rot(parent @ rig.fwd, roll))
    return d @ parent


def place(pb, head, rot3):
    pb.matrix = Matrix.Translation(head) @ rot3.to_4x4()
    update()


def aim(pb, child_pb, direction):
    """pb の向き（頭→子の頭）を direction に合わせる。ねじれは最小限。"""
    cur = child_pb.head - pb.head
    q = cur.rotation_difference(direction).to_matrix()
    place(pb, pb.head.copy(), q @ pb.matrix.to_3x3())


def two_bone(rig, side, target, pole):
    up_n, lo_n, ft_n = side + "UpLeg", side + "Leg", side + "Foot"
    l1 = (rig.rest_head[lo_n] - rig.rest_head[up_n]).length
    l2 = (rig.rest_head[ft_n] - rig.rest_head[lo_n]).length
    p0 = rig.pb(up_n).head.copy()
    to = target - p0
    d = min(max(to.length, 1e-4), (l1 + l2) * 0.999)
    direction = to.normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    side_dir = (pole - direction * pole.dot(direction)).normalized()
    knee = p0 + direction * a + side_dir * h
    foot = p0 + direction * d
    aim(rig.pb(up_n), rig.pb(lo_n), knee - p0)
    aim(rig.pb(lo_n), rig.pb(ft_n), foot - knee)


def apply_pose(rig, p):
    for pb in rig.arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    update()
    ident = Matrix.Identity(3)

    # 腰
    d_hips = turn(rig, p.get("hips_rot", (0, 0, 0)), ident)
    hips_head = rig.rest_head["Hips"] + rig.vec(p.get("hips", (0, 0, 0))) * rig.hip_h
    place(rig.pb("Hips"), hips_head, d_hips @ rig.rest_rot["Hips"])

    # 背骨（等分）
    d = d_hips
    sp = p.get("spine", (0, 0, 0))
    for n in rig.spines:
        d = turn(rig, [x / len(rig.spines) for x in sp], d)
        place(rig.pb(n), rig.pb(n).head.copy(), d @ rig.rest_rot[n])
    d_chest = d

    # 首と頭（等分）
    hd = p.get("head", (0, 0, 0))
    dh = d_chest
    for n in ("Neck", "Head"):
        dh = turn(rig, [x / 2 for x in hd], dh)
        place(rig.pb(n), rig.pb(n).head.copy(), dh @ rig.rest_rot[n])

    # 腕（胸の向きを基準に上腕・前腕の向きを合わせる）
    for side, key in (("Left", "arm_L"), ("Right", "arm_R")):
        a = p.get(key)
        if not a:
            continue
        frame = ident if a.get("space") == "world" else d_chest
        aim(rig.pb(side + "Arm"), rig.pb(side + "ForeArm"), rig.vec(a["upper"], frame).normalized())
        aim(rig.pb(side + "ForeArm"), rig.pb(side + "Hand"), rig.vec(a["fore"], frame).normalized())

    # 脚（足首の位置を決めて膝を解く。膝は腰の正面側へ曲げる）
    pole = d_hips @ rig.fwd
    for side, key in (("Left", "foot_L"), ("Right", "foot_R")):
        f = p.get(key, {})
        target = rig.rest_head[side + "Foot"] + rig.vec(f.get("pos", (0, 0, 0))) * rig.hip_h
        two_bone(rig, side, target, pole)
        foot = rig.pb(side + "Foot")
        place(foot, foot.head.copy(), axis_rot(rig.left, f.get("pitch", 0)) @ rig.rest_rot[side + "Foot"])


# ---------------------------------------------------------------------------
# 書き出し
# ---------------------------------------------------------------------------
CHAINS = [
    ["Hips"] + SPINES + ["Neck", "Head"],
    ["LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase"],
    ["RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"],
    ["Spine2", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand"],
    ["Spine2", "RightShoulder", "RightArm", "RightForeArm", "RightHand"],
    ["Hips", "LeftUpLeg"], ["Hips", "RightUpLeg"],
]


def snapshot(rig):
    """骨の頭の位置を (前, 上, 左) で返す。地面・腰の真下を原点、腰の高さを 1 とする。"""
    h = rig.rest_head
    origin = rig.rest_head["Hips"] - rig.up * rig.hip_h
    out = {}
    for n in rig.names:
        v = rig.pb(n).head - origin
        out[n] = (v.dot(rig.fwd) / rig.hip_h, v.dot(rig.up) / rig.hip_h, v.dot(rig.left) / rig.hip_h)
    return out


def write_svg(path, clip, shots):
    cell, pad = 150, 10
    w = cell * 2 * len(shots) + pad * 2
    hgt = cell * 2 + 70
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" font-family="sans-serif">' % (w, hgt),
         '<rect width="100%" height="100%" fill="#fbf8f2"/>',
         '<text x="%d" y="22" font-size="16" fill="#222">%s（左：横から、右：正面から）</text>' % (pad, clip)]
    for i, (frame, label, pts) in enumerate(shots):
        for view in (0, 1):
            ox = pad + (i * 2 + view) * cell + cell / 2
            oy = hgt - 40
            k = cell * 0.55

            def xy(p):
                f, u, l = p
                x = f if view == 0 else -l
                return ox + x * k, oy - u * k

            s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#bbb"/>'
                     % (ox - cell / 2 + 6, oy, ox + cell / 2 - 6, oy))
            for chain in CHAINS:
                c = [n for n in chain if n in pts]
                for a, b in zip(c, c[1:]):
                    side = "#2f6fb5" if "Left" in a + b else "#c0503c" if "Right" in a + b else "#333"
                    (x1, y1), (x2, y2) = xy(pts[a]), xy(pts[b])
                    s.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3" '
                             'stroke-linecap="round"/>' % (x1, y1, x2, y2, side))
            hx, hy = xy(pts["Head"])
            s.append('<circle cx="%.1f" cy="%.1f" r="9" fill="none" stroke="#333" stroke-width="2.5"/>' % (hx, hy - 6))
        s.append('<text x="%d" y="%d" font-size="13" fill="#222">%dF %s</text>'
                 % (pad + i * 2 * cell + 8, hgt - 14, frame, label))
    s.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(s))


def make_clip(rig, clip, keys, outdir):
    arm = rig.arm
    arm.animation_data_clear()
    arm.animation_data_create()
    action = bpy.data.actions.new(clip)
    arm.animation_data.action = action
    shots = []
    for frame, label, p in keys:
        apply_pose(rig, p)
        for pb in arm.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
            pb.keyframe_insert("location", frame=frame, group=pb.name)
        shots.append((frame, label, snapshot(rig)))
    for fc in fcurves_of(arm, action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = keys[0][0]
    scene.frame_end = keys[-1][0]

    # 書き出す瞬間に画面上にあるポーズが FBX の基本姿勢（T ポーズ）として書かれてしまうので、
    # アクションを NLA に移し、範囲の外のフレーム（＝ポーズなし）にしてから書き出す
    track = arm.animation_data.nla_tracks.new()
    strip = track.strips.new(clip, keys[0][0], action)
    strip.extrapolation = "NOTHING"
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    scene.frame_set(keys[0][0] - 10)

    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    fbx = os.path.join(outdir, clip + "_keys.fbx")
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, object_types={"ARMATURE"}, add_leaf_bones=False,
        bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=True,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0)
    write_svg(os.path.join(outdir, clip + "_keys.svg"), clip, shots)
    with open(os.path.join(outdir, clip + "_keys.txt"), "w", encoding="utf-8") as f:
        f.write("%s  %d fps  0〜%dF\n" % (clip, FPS, keys[-1][0]))
        for frame, label, _ in keys:
            f.write("%4dF  %s\n" % (frame, label))
    return fbx


def fcurves_of(obj, action):
    """Blender 4.4 以降のスロット付きアクションにも、それ以前にも対応する。"""
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="make_test_motion.py")
    ap.add_argument("--input", required=True, help="Cascadeur 用のガレスの FBX（Mixamo 式の骨、T ポーズ）")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--clips", default=",".join(CLIPS), help="作るクリップ（カンマ区切り）")
    a = ap.parse_args(argv)

    os.makedirs(a.outdir, exist_ok=True)
    clips = [c.strip() for c in a.clips.split(",")]
    for clip in clips:
        if clip not in CLIPS:
            raise SystemExit("知らないクリップです: %s（%s）" % (clip, ", ".join(CLIPS)))
    for clip in clips:
        # 前のクリップの状態が残ると書き出しが崩れるので、クリップごとに読み込み直す
        rig = load_rig(a.input)
        print("骨 %d 本、腰の高さ %.3f（アーマチュア座標）" % (len(rig.names), rig.hip_h))
        print("書き出し:", make_clip(rig, clip, CLIPS[clip], a.outdir))


def load_rig(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=False, ignore_leaf_bones=False,
                             automatic_bone_orientation=False)
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if len(arms) != 1:
        raise SystemExit("アーマチュアが %d 個あります（1 個を想定）" % len(arms))
    return Rig(arms[0])


if __name__ == "__main__":
    main()
