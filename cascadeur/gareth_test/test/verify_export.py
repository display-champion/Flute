"""動作確認用：make_test_motion.py が書き出した FBX を読み直して、ポーズが意図どおりか調べる。

  blender -b -P verify_export.py -- <元の骨格.fbx> <書き出したフォルダ>

調べること
- 骨の名前と本数が元の骨格と同じ
- キーの間は直前のポーズのまま（ステップ）になっている
- 腰の高さ・足首の位置が、ポーズ定義どおりになっている（腰の高さの 2% 以内）
- 書き出し前（Blender 上）と読み直した後で、骨の位置がずれていない
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import make_test_motion as m  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
src, outdir = argv[0], argv[1]
TOL = 0.02
failures = []


def check(ok, msg):
    print(("  OK  " if ok else "  NG  ") + msg)
    if not ok:
        failures.append(msg)


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # anim_offset の既定は 1 フレーム後ろへずらすので、0 にして書き出したままのフレームで読む
    bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=False, automatic_bone_orientation=False, anim_offset=0)
    return [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]


src_rig = m.Rig(load(src))
src_names = sorted(b.name for b in src_rig.arm.data.bones)

for clip, keys in m.CLIPS.items():
    print("==", clip)
    # 書き出し前の位置（Blender 上で直接ポーズを付けたもの）
    rig = m.Rig(load(src))
    expected = {}
    for frame, label, p in keys:
        m.apply_pose(rig, p)
        expected[frame] = m.snapshot(rig)

    arm = load(os.path.join(outdir, clip + "_keys.fbx"))
    got_rig = m.Rig(arm)
    check(sorted(b.name for b in arm.data.bones) == src_names, "骨の名前と本数が元と同じ（%d 本）" % len(src_names))
    rest_err = max((got_rig.rest_head[n] - src_rig.rest_head[n]).length for n in src_rig.names) / src_rig.hip_h
    check(rest_err < 1e-3, "基本姿勢（T ポーズ）が元と同じ（差 %.5f）" % rest_err)
    sc = bpy.context.scene

    def at(f):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        # 読み直した骨格の位置を、元の骨格の基準（前・上・左、腰の高さ）で測る
        return m.snapshot(got_rig)

    worst = 0.0
    for i, (frame, label, p) in enumerate(keys):
        s = at(frame)
        for n, v in expected[frame].items():
            worst = max(worst, max(abs(a - b) for a, b in zip(v, s[n])))
        hips_u = s["Hips"][1] - 1.0
        want_u = p.get("hips", (0, 0, 0))[1]
        check(abs(hips_u - want_u) < TOL, "%dF %s：腰の上下 %.3f（定義 %.3f）" % (frame, label, hips_u, want_u))
        for side, key in (("Left", "foot_L"), ("Right", "foot_R")):
            want = m.Vector(p.get(key, {}).get("pos", (0, 0, 0)))
            rest = m.Vector(src_rig.rest_head[side + "Foot"])
            base = ((rest - (src_rig.rest_head["Hips"] - src_rig.up * src_rig.hip_h)).dot(src_rig.fwd) / src_rig.hip_h,
                    (rest - (src_rig.rest_head["Hips"] - src_rig.up * src_rig.hip_h)).dot(src_rig.up) / src_rig.hip_h,
                    (rest - (src_rig.rest_head["Hips"] - src_rig.up * src_rig.hip_h)).dot(src_rig.left) / src_rig.hip_h)
            got = m.Vector(s[side + "Foot"]) - m.Vector(base)
            err = (got - want).length
            check(err < TOL, "%dF %s：%s の足首 ずれ %.3f" % (frame, label, side, err))
        if i + 1 < len(keys):
            mid = (frame + keys[i + 1][0]) // 2
            s2 = at(mid)
            hold = max(max(abs(a - b) for a, b in zip(s[n], s2[n])) for n in s)
            check(hold < 1e-3, "%dF→%dF：次のキーまでポーズを保持（差 %.4f）" % (frame, mid, hold))
    check(worst < TOL, "書き出し前と読み直し後の骨の位置の差 最大 %.4f（腰の高さ比）" % worst)

print("\n結果:", "すべて OK" if not failures else "NG %d 件" % len(failures))
sys.exit(1 if failures else 0)
