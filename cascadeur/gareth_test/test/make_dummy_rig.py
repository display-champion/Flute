"""動作確認用：Mixamo 式の骨を持つ人型の骨格（T ポーズ、メッシュなし）を FBX で書き出す。

ガレス本体のモデルが手元に無い環境で make_test_motion.py を試すためのもの。
  blender -b -P make_dummy_rig.py -- <出力.fbx> [身長m]
"""

import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
height = float(argv[1]) if len(argv) > 1 else 1.8
k = height / 1.8

# (名前, 親, 頭, 尾)  Blender 座標：Z が上、キャラクターは -Y を向き、+X が左手側
L = 1
BONES = [
    ("Hips", None, (0, 0, 1.00), (0, 0, 1.10)),
    ("Spine", "Hips", (0, 0, 1.10), (0, 0, 1.22)),
    ("Spine1", "Spine", (0, 0, 1.22), (0, 0, 1.34)),
    ("Spine2", "Spine1", (0, 0, 1.34), (0, 0, 1.46)),
    ("Neck", "Spine2", (0, 0, 1.50), (0, 0, 1.60)),
    ("Head", "Neck", (0, 0, 1.60), (0, 0, 1.80)),
]
for side, s in (("Left", 1), ("Right", -1)):
    BONES += [
        (side + "Shoulder", "Spine2", (s * 0.03, 0, 1.44), (s * 0.17, 0, 1.44)),
        (side + "Arm", side + "Shoulder", (s * 0.17, 0, 1.44), (s * 0.45, 0, 1.44)),
        (side + "ForeArm", side + "Arm", (s * 0.45, 0, 1.44), (s * 0.71, 0, 1.44)),
        (side + "Hand", side + "ForeArm", (s * 0.71, 0, 1.44), (s * 0.80, 0, 1.44)),
        (side + "UpLeg", "Hips", (s * 0.10, 0, 0.98), (s * 0.10, 0, 0.53)),
        (side + "Leg", side + "UpLeg", (s * 0.10, 0, 0.53), (s * 0.10, 0, 0.09)),
        (side + "Foot", side + "Leg", (s * 0.10, 0, 0.09), (s * 0.10, -0.13, 0.02)),
        (side + "ToeBase", side + "Foot", (s * 0.10, -0.13, 0.02), (s * 0.10, -0.20, 0.02)),
    ]

bpy.ops.wm.read_factory_settings(use_empty=True)
data = bpy.data.armatures.new("Armature")
obj = bpy.data.objects.new("Armature", data)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode="EDIT")
eb = {}
for name, parent, head, tail in BONES:
    b = data.edit_bones.new("mixamorig:" + name)
    b.head = [c * k for c in head]
    b.tail = [c * k for c in tail]
    if parent:
        b.parent = eb[parent]
        b.use_connect = tuple(b.head) == tuple(eb[parent].tail)
    eb[name] = b
bpy.ops.object.mode_set(mode="OBJECT")
obj.select_set(True)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, object_types={"ARMATURE"}, add_leaf_bones=False,
                         bake_anim=False)
print("書き出し:", out)
