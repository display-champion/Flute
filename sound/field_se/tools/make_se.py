# -*- coding: utf-8 -*-
"""
操作系・マップ系の SE をすべて合成して ../Resources/FieldSE/ に書き出す。
  python make_se.py              … 全部作る
  python make_se.py Step_Stone   … 名前を指定して作る（部分一致）
必要なもの：Python 3 ＋ numpy ＋ scipy
方針：キンキン系（金属の響き・鈴・きらめき）は使わず、重厚に。
"""
import os
import sys
import json
import numpy as np
from dsp import *  # noqa: F401,F403
import dsp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "Resources", "FieldSE")   # Unity の Resources から名前で読めるように

SE = []

# 目標音量（50ms ごとの一番大きい所の RMS）
STEP, MOVE, MECH, BIG, LOOP, SOFT = -17, -14, -11, -9, -18, -15


def se(name, group, level, desc, use, loop=False, eq=(5.0, -5.0)):
    def reg(fn):
        SE.append(dict(name=name, group=group, level=level, desc=desc, use=use, loop=loop, eq=eq, fn=fn))
        return fn
    return reg


def J(a, b):
    """a〜b の乱数（音ごとの乱数で、足音の 4 通りが少しずつ変わる）"""
    return RNG.uniform(a, b)


# =====================================================================
# 足音（地面の種類 × 4 通り）
# =====================================================================

def heel(d, f0, f1, tau, drv=1.5):
    return thump(d, f0 * J(0.9, 1.1), f1, tau * J(0.85, 1.15), drv)


def step_grass(d=0.3):
    rustle = bp(white(d), J(1800, 2600), 0.7) * env(d, [(0, 0), (0.01, 1), (0.05, 0.6), (0.14, 0), (d, 0)])
    rustle *= 1 + 0.5 * lp(white(d), 60) * 10
    return mix(d, [(0, heel(d, 110, 60, 0.025), 0.8), (0, norm(rustle), 0.45), (J(0.02, 0.04), grains(0.12, 8, freq=(1500, 4500)), 0.15)])


def step_dirt(d=0.3):
    return mix(d, [(0, heel(d, 120, 60, 0.03, 2), 1.0), (0, burst(0.15, 250, 2200, 0.025, -3), 0.5),
                   (0.005, grains(0.14, 14, dur=(0.003, 0.012), freq=(800, 3500)), 0.25),
                   (J(0.04, 0.07), burst(0.1, 300, 1800, 0.02, -3), 0.25)])   # つま先


def step_stone(d=0.35):
    x = mix(d, [(0, heel(d, 150, 70, 0.02, 2), 1.0), (0, burst(0.1, 600, 3500, 0.01, -1), 0.45), (0, click(0.003, 800), 0.25),
                (J(0.05, 0.08), burst(0.08, 500, 2500, 0.01, -2), 0.2), (J(0.05, 0.08), heel(0.1, 130, 70, 0.015), 0.35)])
    return reverb(x, 0.6, 0.12, lpf=2500)   # 石の廊下・洞窟の響き


def step_wood(d=0.35):
    knock = partials(0.25, [J(150, 180), J(330, 380), J(560, 620)], [0.05, 0.03, 0.02], [1, 0.5, 0.25])
    creak = bp(osc(J(90, 130), 0.2, "saw"), 700, 3) * env(0.2, [(0, 0), (0.04, 1), (0.2, 0)]) * (J(0, 1) > 0.5)
    return mix(d, [(0, heel(d, 130, 70, 0.03, 2), 0.8), (0, knock, 0.7), (0, burst(0.1, 400, 2500, 0.012, -2), 0.3), (0.03, creak, 0.12)])


def step_water(d=0.4):
    splash = burst(0.3, 400, 3500, 0.05, -2) * (1 + 0.4 * np.sin(phase_of(J(20, 30), 0.3)))
    return mix(d, [(0, heel(d, 100, 55, 0.025), 0.6), (0, norm(splash), 0.8), (0.03, bubbles(0.3, 6, 400, 1500), 0.3)])


def step_mud(d=0.45):
    squelch = lp(pink(0.3), J(700, 1000)) * env(0.3, [(0, 0), (0.02, 1), (0.15, 0.4), (0.3, 0)]) * (1 + 0.8 * np.sin(phase_of(J(25, 40), 0.3)))
    suck = np.sin(phase_of(curve(0.12, [(0, 400), (0.12, 150)], "exp"), 0.12)) * expdec(0.12, 0.03)
    return mix(d, [(0, heel(d, 90, 50, 0.035), 0.7), (0, norm(squelch), 0.7), (J(0.14, 0.2), suck, 0.3), (0.05, bubbles(0.3, 3, 200, 600), 0.2)])


def step_metal(d=0.4):
    # 天界の工房の金属の床。響かせず「ゴン」と鈍く
    dull = partials(0.3, [J(140, 160), J(300, 340), J(470, 520)], [0.06, 0.04, 0.03], [1, 0.6, 0.35])
    x = mix(d, [(0, heel(d, 140, 70, 0.025, 2), 0.9), (0, dull, 0.6), (0, burst(0.1, 500, 2500, 0.012, -2), 0.3)])
    return reverb(lp(x, 2500), 0.5, 0.1, lpf=2000)


SURFACES = [
    ("Grass", "草", step_grass, "草地・森（ふさっと草を踏む）"),
    ("Dirt", "土", step_dirt, "土の道・平原・洞窟の土（ザッと砂利まじり）"),
    ("Stone", "石", step_stone, "石畳・石の廊下・洞窟の岩（コツッと硬く、少し響く）"),
    ("Wood", "木", step_wood, "木の床・橋・足場（コトッと中が空いた木の音）"),
    ("Water", "水", step_water, "浅い水・水たまり・水路の浅瀬（パシャッ）"),
    ("Mud", "泥", step_mud, "沼・泥・毒の湿地（ぐちゅっと沈む）"),
    ("Metal", "金属", step_metal, "天界の工房の金属の床（響かない鈍い「ゴン」）"),
]
for key, jp, fn, desc in SURFACES:
    for v in range(1, 5):
        se(f"Step_{key}_{v:02d}", "足音", STEP, f"{jp}の足音 {v}／4：{desc}", "歩き（走りは同じ音を少し大きく・高めに。FootstepSE が自動で選ぶ）", eq=(3.0, -3.0))((lambda f: lambda: f())(fn))


# =====================================================================
# 操作
# =====================================================================

@se("Jump", "操作", MOVE, "ジャンプの踏み切り（地面を蹴る「ザッ」と服がひるがえる風）", "ジャンプ（Space）")
def _():
    d = 0.4
    return mix(d, [(0, step_dirt(0.25), 0.8), (0.02, whoosh(0.3, [(0, 400), (0.1, 1300), (0.3, 500)], 0.1, 0.05, 1.8, q=0.8, body=0.8), 0.6)])


@se("Land", "操作", MOVE, "着地（「トッ」と軽く降りる）", "ジャンプの着地（地面の足音と重ねてもよい）")
def _():
    d = 0.4
    return mix(d, [(0, heel(d, 110, 50, 0.045, 2.5), 1.0), (0, burst(0.2, 200, 1800, 0.03, -3), 0.6), (0.01, grains(0.2, 10, freq=(500, 2500)), 0.15)])


@se("Land_Heavy", "操作", MECH, "高い所からの着地（「ドスッ」と重く、砂ぼこりが立つ）", "高い所からの落下・ジャンプ斬りの着地など")
def _():
    d = 0.8
    dust = lp(white(0.5), curve(0.5, [(0, 2000), (0.5, 500)], "exp")) * env(0.5, [(0, 0), (0.02, 1), (0.5, 0)])
    return reverb(mix(d, [(0, thump(0.6, 100, 35, 0.09, 3), 1.0), (0, burst(0.3, 150, 2000, 0.05, -3), 0.7), (0.02, norm(dust), 0.3),
                          (0.02, grains(0.4, 20, freq=(400, 2500)), 0.2)]), 0.6, 0.12, lpf=2000)


@se("Dash", "操作", MOVE, "ダッシュ（踏み込んで一気に3m、低い「ブンッ」）", "ダッシュ（L1／C、0.18秒で3m）")
def _():
    d = 0.5
    return mix(d, [(0, step_dirt(0.2), 0.7), (0, whoosh(0.4, [(0, 300), (0.08, 1400), (0.4, 350)], 0.08, 0.035, 2.2, q=0.7, body=1.2), 1.0), (0.18, step_dirt(0.2), 0.4)])


@se("Dodge_Roll", "操作", MOVE, "側転回避（服の風切り→体が転がる「ドッ、ザザッ」）", "側転回避（×／左Ctrl、0.75秒）")
def _():
    d = 0.9
    cloth = whoosh(0.5, [(0, 400), (0.15, 1100), (0.5, 400)], 0.15, 0.08, 2, q=0.6, body=1.0)
    slide = bp(pink(0.3), 900, 0.7) * env(0.3, [(0, 0), (0.03, 1), (0.3, 0)])
    return mix(d, [(0, step_dirt(0.2), 0.6), (0.02, cloth, 0.7), (0.3, heel(0.3, 100, 50, 0.04, 2), 0.7), (0.45, heel(0.3, 90, 50, 0.04, 2), 0.5),
                   (0.45, norm(slide), 0.4), (0.62, step_dirt(0.2), 0.5)])


@se("Swim_Stroke", "操作", MOVE, "泳ぐ（水をかく「ザブッ」）", "泳いでいるときのひとかき")
def _():
    d = 0.8
    swish = bp(white(0.5), curve(0.5, [(0, 500), (0.2, 1400), (0.5, 600)], "exp"), 0.7) * env(0.5, [(0, 0), (0.15, 1), (0.5, 0)])
    return mix(d, [(0, norm(swish), 0.8), (0.1, bubbles(0.5, 12, 250, 900), 0.4), (0.12, lp(pink(0.3), 600) * expdec(0.3, 0.08), 0.5)])


@se("Water_Enter", "操作", MECH, "水に入る・飛び込む（「ドボン」）", "水路・湖に入ったとき")
def _():
    d = 1.2
    return mix(d, [(0, thump(0.5, 130, 50, 0.08, 2), 0.8), (0, burst(0.5, 200, 3000, 0.1, -3), 0.9),
                   (0.03, bubbles(1.0, 35, 200, 1000), 0.5), (0.05, lp(pink(0.8), 700) * expdec(0.8, 0.2), 0.4)])


@se("Slide_Loop", "操作", LOOP, "ぬめった床を滑る（ずるずる、ループ用）", "水路ナメクジの跡など、滑る床の上にいる間", loop=True)
def _():
    def fn(d):
        return norm(lp(pink(d), 800) * (1 + 0.5 * slow_noise(d, 6))) + 0.3 * bubbles(d, int(d * 5), 200, 600)
    return make_loop(fn, 2.0, 0.3)


@se("Climb_Grab", "操作", MOVE, "よじ登る・つかまる（手が岩や縁をつかむ「ガッ」）", "段差・ツタ・崖をつかむ")
def _():
    d = 0.4
    return mix(d, [(0, heel(d, 150, 70, 0.025, 2), 0.7), (0, burst(0.2, 300, 2000, 0.03, -3), 0.7), (0.02, grains(0.2, 10, freq=(500, 2500)), 0.2),
                   (0.05, bp(white(0.2), 1500, 0.8) * env(0.2, [(0, 0), (0.03, 1), (0.2, 0)]), 0.3)])


@se("Heal_Potion", "操作", SOFT, "回復薬を使う（栓を抜く「ポン」→ ごくり → 温かく「フワァ」と広がる）", "回復薬（R2／R）")
def _():
    d = 1.6
    pop = np.sin(phase_of(curve(0.1, [(0, 500), (0.1, 180)], "exp"), 0.1)) * expdec(0.1, 0.025)
    gulp = lambda: lp(np.sin(phase_of(curve(0.15, [(0, 160), (0.15, 110)], "exp"), 0.15)) + 0.4 * pink(0.15), 700) * env(0.15, [(0, 0), (0.03, 1), (0.15, 0)])
    pad = lp(sum(osc(f * (1 + 0.003 * J(-1, 1)), 1.1, "saw") for f in (98, 147, 196, 247)), 900) * env(1.1, [(0, 0), (0.35, 1), (1.1, 0)])
    return reverb(mix(d, [(0, pop, 0.7), (0, click(0.004, 600), 0.3), (0.2, gulp(), 0.6), (0.38, gulp(), 0.5),
                          (0.45, norm(pad), 0.55), (0.45, whoosh(0.9, [(0, 300), (0.4, 1000), (0.9, 300)], 0.4, 0.15, 1.2, q=0.5, body=1.0), 0.35)]), 1.0, 0.25, lpf=2500)


@se("Item_Pickup", "操作", SOFT, "落ちている物を拾う（「ポフッ」と柔らかく）", "ドロップ品・素材を拾ったとき")
def _():
    d = 0.5
    blip = lp(osc(curve(0.25, [(0, 200), (0.06, 300), (0.25, 300)], "exp"), 0.25, "tri"), 900) * expdec(0.25, 0.08, 0.005)
    return reverb(mix(d, [(0, burst(0.15, 200, 1500, 0.03, -3), 0.6), (0, heel(0.2, 160, 90, 0.03), 0.5), (0.03, blip, 0.5)]), 0.5, 0.15, lpf=2000)


@se("Gather_Plant", "操作", MOVE, "採取する（草をかき分けて、根元から「ブチッ」と抜く）", "採取ポイント")
def _():
    d = 0.8
    rustle = bp(white(0.45), 1800, 0.7) * env(0.45, [(0, 0), (0.05, 1), (0.45, 0.2)]) * (1 + 0.6 * slow_noise(0.45, 20))
    snap = mix(0.3, [(0, burst(0.2, 300, 2500, 0.015, -2), 1.0), (0, heel(0.2, 180, 90, 0.02), 0.6)])
    return mix(d, [(0, norm(rustle), 0.5), (0.4, snap, 1.0), (0.42, grains(0.3, 12, freq=(400, 2000)), 0.25)])


@se("Player_Down", "操作", MECH, "フィナが倒れる（ひざをつき、「ドサッ」と崩れる）", "HPが0になったとき")
def _():
    d = 1.6
    low = lp(osc(curve(1.2, [(0, 90), (1.2, 45)], "exp"), 1.2, "saw"), 300) * env(1.2, [(0, 0), (0.3, 1), (1.2, 0)])
    return reverb(mix(d, [(0, heel(0.3, 120, 60, 0.04, 2), 0.6), (0.35, thump(0.6, 110, 40, 0.1, 3), 1.0), (0.35, burst(0.4, 150, 2000, 0.06, -3), 0.6),
                          (0.3, norm(low), 0.35)]), 1.2, 0.2, lpf=1800)


@se("Respawn", "操作", SOFT, "復活する（低い和音が「フワァン」と立ちのぼる）", "倒れてから2.5秒後の復活")
def _():
    d = 1.8
    pad = lp(sum(osc(f * (1 + 0.004 * J(-1, 1)), d, "saw") for f in (65.4, 98, 131, 165)), curve(d, [(0, 200), (0.8, 1400), (d, 300)], "exp"))
    return reverb(mix(d, [(0, norm(pad) * env(d, [(0, 0), (0.7, 1), (d, 0)]), 0.8),
                          (0, whoosh(1.2, [(0, 200), (0.7, 1500), (1.2, 500)], 0.7, 0.2, 1.0, q=0.5, body=1.0), 0.5)]), 1.2, 0.3, lpf=2500)


# =====================================================================
# 仕掛け（スイッチ・扉・壁など）
# =====================================================================

def grind(d, f=500, rough=1.0):
    """石がこすれる「ゴリゴリ」"""
    g = bp(brown(d) + 0.3 * white(d), f, 0.6)
    g *= 1 + rough * 0.8 * np.abs(lp(white(d), 25)) * 10
    return norm(g)


def rumble(d, f=120):
    return norm(lp(brown(d), f, stages=2))


def clunk(d=0.5, f=90, weight=1.0):
    """仕掛けが噛み合う「ガコン」"""
    return mix(d, [(0, thump(d, f * 1.6, f * 0.6, 0.06 * weight, 3), 1.0), (0, burst(0.3, 150, 1500, 0.03 * weight, -3), 0.7), (0, click(0.004, 500), 0.3)])


def creak(d, f0=110, f1=160, bright=700):
    """木がきしむ「ギィィ」"""
    f = curve(d, [(0, f0), (d * 0.5, f1), (d, f0 * 1.1)], "exp") * (1 + 0.04 * slow_noise(d, 8))
    stick = 0.55 + 0.45 * np.tanh(3 * np.sin(phase_of(J(9, 14), d) + 2 * slow_noise(d, 3)))  # 引っかかりながらきしむ（なめらかに）
    return norm(bp(osc(f, d, "saw") * stick, bright, 2) + 0.4 * bp(osc(f, d, "saw"), bright * 2, 3))


@se("Switch_On", "仕掛け", MECH, "スイッチを押す（石のボタンが「ゴトッ」と沈み、奥で「ガコン」と仕掛けが動く）", "イベントのスイッチ・仕掛けの起動")
def _():
    d = 1.2
    press = mix(0.3, [(0, heel(0.3, 160, 80, 0.03, 2), 0.8), (0, grind(0.15, 600), 0.4)])
    return reverb(mix(d, [(0, press, 0.8), (0.18, clunk(0.6, 80), 1.0), (0.25, rumble(0.7) * env(0.7, [(0, 0), (0.1, 1), (0.7, 0)]), 0.35)]), 0.9, 0.18, lpf=2000)


@se("Floor_Switch", "仕掛け", MECH, "床のスイッチを踏む（床の石板が「ゴゴッ」と沈んで止まる）", "踏むと動く床の仕掛け")
def _():
    d = 0.9
    return reverb(mix(d, [(0, grind(0.35, 400) * env(0.35, [(0, 0), (0.05, 1), (0.35, 1)]), 0.6), (0.33, clunk(0.5, 70), 1.0)]), 0.8, 0.15, lpf=2000)


@se("Lever_Pull", "仕掛け", MECH, "レバーを引く（木の柄がきしみ、歯止めが「ガッ、ガッ」→「ガコン」）", "レバーの仕掛け")
def _():
    d = 1.3
    ratchet = mix(0.5, [(0.1 * i, clunk(0.1, 200, 0.3), 0.35) for i in range(4)])
    return reverb(mix(d, [(0, creak(0.5, 100, 140, 600) * env(0.5, [(0, 0), (0.05, 1), (0.5, 0.6)]), 0.4), (0.05, ratchet, 0.8), (0.55, clunk(0.6, 70), 1.0)]), 0.9, 0.18, lpf=2000)


@se("Wall_Lower", "仕掛け", BIG, "石の壁が降りる（地響きを立てて沈み、最後に「ズゥン」と止まる、約2.5秒）", "通路をふさぐ壁が下がる・壁が沈んで道が開く")
def _():
    d = 3.2
    body = rumble(2.5, 110) * env(2.5, [(0, 0), (0.15, 1), (2.3, 1), (2.5, 0)])
    scrape = grind(2.5, 450) * env(2.5, [(0, 0), (0.2, 1), (2.3, 0.8), (2.5, 0)])
    debris = grains(2.4, 50, dur=(0.008, 0.04), freq=(300, 2000), density="flat", amp=(0.2, 0.8))
    end = mix(0.8, [(0, thump(0.8, 90, 30, 0.2, 3), 1.0), (0, burst(0.5, 100, 1500, 0.08, -4), 0.7), (0.02, grains(0.5, 20, freq=(300, 2000)), 0.3)])
    return reverb(mix(d, [(0, clunk(0.4, 80), 0.6), (0.05, body, 0.8), (0.05, scrape, 0.45), (0.1, debris, 0.25), (2.45, end, 1.0)]), 1.4, 0.2, lpf=1800)


@se("Wall_Raise", "仕掛け", BIG, "石の壁がせり上がる（地面から押し上がり、「ゴトン」と止まる、約2秒）", "壁や柱が地面からせり上がって道をふさぐ・足場ができる")
def _():
    d = 2.6
    body = rumble(2.0, 130) * env(2.0, [(0, 0), (0.1, 0.6), (1.8, 1), (2.0, 0)])
    scrape = grind(2.0, curve(2.0, [(0, 350), (2.0, 550)], "exp").mean()) * env(2.0, [(0, 0), (0.15, 1), (1.9, 0.9), (2.0, 0)])
    return reverb(mix(d, [(0, thump(0.5, 100, 40, 0.1, 3), 0.7), (0.05, body, 0.8), (0.05, scrape, 0.45),
                          (0.1, grains(1.9, 35, freq=(300, 2000), density="flat"), 0.2), (1.95, clunk(0.6, 70, 1.3), 1.0)]), 1.2, 0.2, lpf=1800)


@se("Gate_Portcullis", "仕掛け", BIG, "鉄格子の門が落ちる（鎖が鈍くほどけ、「ガシャーン」ではなく重く「ドガン」）", "落とし格子・閉じ込められるイベント")
def _():
    d = 1.8
    chain = grains(0.6, 30, dur=(0.015, 0.05), freq=(250, 1000), density="flat", amp=(0.3, 1.0))
    drop = mix(1.0, [(0, thump(1.0, 100, 30, 0.2, 3.5), 1.0), (0, partials(0.8, [95, 205, 330], [0.3, 0.2, 0.12], [1, 0.5, 0.25]), 0.5),
                     (0, burst(0.5, 150, 1800, 0.06, -3), 0.7), (0.02, grains(0.5, 15, freq=(300, 1200)), 0.4)])
    return reverb(mix(d, [(0, chain, 0.5), (0.05, whoosh(0.5, [(0, 200), (0.5, 800)], 0.45, 0.1, 0.4, body=1.2), 0.4), (0.55, lp(drop, 2000), 1.0)]), 1.3, 0.2, lpf=1800)


@se("Gate_Open_Large", "仕掛け", BIG, "大きな門が開く（重い木の門が低くきしみながら開き、止まる、約3秒）", "南門・城門・大聖堂などの大扉")
def _():
    d = 3.6
    cr = creak(2.8, 55, 75, 350) * env(2.8, [(0, 0), (0.3, 1), (2.4, 0.8), (2.8, 0)])
    return reverb(mix(d, [(0, clunk(0.6, 70, 1.3), 0.8), (0.2, cr, 0.6), (0.2, rumble(2.8, 100) * env(2.8, [(0, 0), (0.3, 1), (2.8, 0)]), 0.6),
                          (2.95, thump(0.6, 80, 35, 0.12, 2.5), 0.8)]), 1.6, 0.25, lpf=1600)


@se("Door_Open_Wood", "仕掛け", MECH, "木の扉を開ける（かんぬきが外れ、「ギィィ」ときしむ）", "家・小屋・ダンジョンの木の扉（○／F で調べる）")
def _():
    d = 1.4
    return reverb(mix(d, [(0, clunk(0.3, 140, 0.6), 0.7), (0.15, creak(0.9, 120, 170, 750) * env(0.9, [(0, 0), (0.1, 1), (0.8, 0.5), (0.9, 0)]), 0.6),
                          (0.15, whoosh(0.9, [(0, 300), (0.5, 700), (0.9, 300)], 0.45, 0.2, 1, q=0.6, body=1), 0.25)]), 0.9, 0.18, lpf=2500)


@se("Door_Close_Wood", "仕掛け", MECH, "木の扉が閉まる（「バタン」と重く、かんぬきが掛かる）", "扉が閉まる・閉じ込められる")
def _():
    d = 1.0
    return reverb(mix(d, [(0, whoosh(0.3, [(0, 300), (0.25, 800)], 0.22, 0.06, 0.4, body=1.2), 0.4), (0.25, thump(0.5, 120, 45, 0.08, 3), 1.0),
                          (0.25, burst(0.3, 200, 2000, 0.04, -3), 0.7), (0.5, clunk(0.3, 140, 0.5), 0.5)]), 0.9, 0.2, lpf=2200)


@se("Door_Open_Stone", "仕掛け", BIG, "石の扉が横に開く（重い石が「ゴゴゴ」と引きずられ、止まる、約1.6秒）", "遺跡・祠・封印された部屋の石扉")
def _():
    d = 2.2
    g = grind(1.6, 380) * env(1.6, [(0, 0), (0.15, 1), (1.5, 0.9), (1.6, 0)])
    return reverb(mix(d, [(0, clunk(0.4, 80), 0.6), (0.1, g, 0.7), (0.1, rumble(1.6, 110) * env(1.6, [(0, 0), (0.15, 1), (1.6, 0)]), 0.6),
                          (1.65, clunk(0.6, 60, 1.4), 1.0)]), 1.2, 0.2, lpf=1800)


@se("Door_Locked", "仕掛け", MECH, "鍵がかかっている（取っ手を引いても「ガタガタッ」と動かない）", "開かない扉・宝箱を調べたとき")
def _():
    d = 0.6
    return mix(d, [(0.0, clunk(0.2, 160, 0.4), 0.8), (0.1, clunk(0.2, 150, 0.4), 0.7), (0.18, clunk(0.2, 170, 0.4), 0.6)])


@se("Key_Unlock", "仕掛け", MECH, "鍵を開ける（鍵を差し込み、回して「ガチャリ」）", "鍵のかかった扉・宝箱を開けたとき")
def _():
    d = 0.8
    insert = bp(white(0.15), 1200, 1) * env(0.15, [(0, 0), (0.05, 1), (0.15, 0)])
    return reverb(mix(d, [(0, norm(insert), 0.25), (0.2, clunk(0.2, 220, 0.4), 0.5), (0.32, clunk(0.4, 120, 0.8), 1.0)]), 0.6, 0.15, lpf=2200)


@se("Chest_Open", "仕掛け", MECH, "宝箱を開ける（重いふたが「ギッ」ときしんで「ゴトン」と開ききる）", "宝箱")
def _():
    d = 1.0
    return reverb(mix(d, [(0, clunk(0.3, 130, 0.6), 0.6), (0.1, creak(0.4, 110, 150, 700) * env(0.4, [(0, 0), (0.05, 1), (0.4, 0)]), 0.5),
                          (0.5, thump(0.4, 120, 50, 0.06, 2.5), 0.9), (0.5, burst(0.2, 200, 1800, 0.03, -3), 0.5)]), 0.7, 0.15, lpf=2200)


@se("Treasure_Get", "仕掛け", SOFT, "宝を手に入れた（低い和音が温かく広がる。鈴の音は使わない）", "宝箱の中身・大事な物を手に入れたとき")
def _():
    d = 2.0
    chords = [(0, (131, 165, 196)), (0.22, (147, 196, 247)), (0.44, (131, 196, 262))]
    parts = []
    for at, ch in chords:
        dd = 1.5 - at
        p = lp(sum(osc(f * (1 + 0.003 * J(-1, 1)), dd, "saw") for f in ch), 1300) * env(dd, [(0, 0), (0.03, 1), (0.2, 0.6), (dd, 0)])
        parts.append((at, norm(p), 0.7 if at < 0.4 else 1.0))
    parts.append((0, thump(0.4, 110, 50, 0.08, 1.5), 0.5))
    parts.append((0.44, whoosh(1.0, [(0, 300), (0.3, 1000), (1.0, 300)], 0.3, 0.2, 1.5, q=0.5, body=1), 0.25))
    return reverb(mix(d, parts), 1.3, 0.3, lpf=2500)


@se("Bridge_Form", "仕掛け", BIG, "錬成の橋ができる（魔力がうなり、板や石が「ゴトッ、ゴトッ」と順に組み上がる）", "錬成の橋・足場が現れるギミック")
def _():
    d = 2.4
    hum = lp(osc(curve(1.8, [(0, 55), (1.8, 90)], "exp"), 1.8, "saw") + osc(curve(1.8, [(0, 82), (1.8, 135)], "exp"), 1.8, "saw"), 500) * env(1.8, [(0, 0), (0.3, 1), (1.8, 0)])
    parts = [(0, norm(hum), 0.4)]
    for i in range(6):
        parts.append((0.25 + 0.22 * i, clunk(0.4, 90 + 8 * i, 0.8), 0.6 + 0.06 * i))
    parts.append((1.65, clunk(0.6, 70, 1.4), 1.0))
    return reverb(mix(d, parts), 1.2, 0.2, lpf=2000)


@se("Floor_Collapse", "仕掛け", BIG, "足場が崩れる（ひびが走り、崩れ落ちて下で砕ける）", "崩れる床・落とし穴・崩れた王都")
def _():
    d = 2.8
    crack = mix(0.5, [(0.02 * i + J(0, 0.015), heel(0.08, 300, 150, 0.01, 3), J(0.3, 0.8)) for i in range(10)])
    crumble = grains(1.6, 90, dur=(0.01, 0.06), freq=(200, 2000), density="flat", amp=(0.2, 1.0)) * env(1.6, [(0, 0.3), (0.3, 1), (1.6, 0)])
    return reverb(mix(d, [(0, lp(crack, 1500), 0.8), (0.4, thump(0.8, 90, 30, 0.2, 3), 0.9), (0.4, rumble(1.6, 150) * env(1.6, [(0, 0), (0.05, 1), (1.6, 0)]), 0.7),
                          (0.4, crumble, 0.5), (1.4, thump(0.8, 70, 28, 0.2, 3), 0.7)]), 1.5, 0.22, lpf=1800)


@se("Rock_Fall", "仕掛け", BIG, "落石（岩が転がり落ちてきて、ドン、ドドンと地面を打つ）", "落石の仕掛け・崖崩れ")
def _():
    d = 2.4
    parts = [(0, rumble(1.6, 180) * env(1.6, [(0, 0), (0.3, 1), (1.6, 0)]), 0.5)]
    for i, at in enumerate([0.35, 0.7, 0.85, 1.2]):
        parts.append((at, thump(0.7, J(80, 110), 30, 0.15, 3), 1.0 - 0.15 * i))
        parts.append((at, grains(0.5, 15, freq=(300, 2000)), 0.3))
    return reverb(mix(d, parts), 1.4, 0.2, lpf=1800)


@se("Barrel_Break", "仕掛け", MECH, "樽を壊す（「バキッ」と板が割れ、たがが転がる）", "樽を叩く（樽の子を見分ける）")
def _():
    d = 1.0
    return reverb(mix(d, [(0, thump(0.4, 150, 60, 0.05, 3), 1.0), (0, burst(0.3, 300, 3000, 0.03, -2), 0.8),
                          (0.01, grains(0.7, 35, dur=(0.01, 0.04), freq=(250, 1800)), 0.5), (0.25, heel(0.2, 180, 100, 0.02), 0.3), (0.45, heel(0.2, 170, 100, 0.02), 0.2)]), 0.6, 0.15, lpf=2500)


@se("Crate_Break", "仕掛け", MECH, "木箱を壊す（「バシャッ」と板がばらける）", "木箱・箱入りの忘れ物")
def _():
    d = 0.8
    return mix(d, [(0, thump(0.3, 170, 70, 0.04, 3), 0.9), (0, burst(0.3, 400, 3500, 0.025, -1), 0.9), (0.01, grains(0.6, 30, dur=(0.008, 0.03), freq=(400, 2500)), 0.5)])


def fire_bed(d, bright=1800):
    roar = lp(brown(d), bright) * (1 + 0.3 * slow_noise(d, 6))
    return norm(roar) + 0.3 * crackle(d, 40, 1200, False)


@se("Torch_Ignite", "仕掛け", MECH, "松明・灯りに火をつける（「ボウッ」と燃え上がる）", "燭台・坑道の灯り・墓の灯り・焚き火")
def _():
    d = 1.4
    return mix(d, [(0, thump(0.4, 120, 60, 0.06, 2), 0.7), (0, burst(0.4, 150, 2000, 0.08, -4), 0.8),
                   (0.02, fire_bed(1.3, 2000) * env(1.3, [(0, 0), (0.05, 1), (0.4, 0.5), (1.3, 0)]), 0.7)])


@se("Lantern_On", "仕掛け", SOFT, "ランタンをつける（小さく「ポッ」と灯る）", "暗闇のギミックでランタンをつける")
def _():
    d = 0.8
    return mix(d, [(0, clunk(0.2, 200, 0.3), 0.4), (0.08, burst(0.2, 200, 1500, 0.04, -4), 0.6), (0.08, fire_bed(0.6, 1200) * env(0.6, [(0, 0), (0.05, 1), (0.6, 0)]), 0.4)])


@se("Lantern_Off", "仕掛け", SOFT, "ランタンを消す（「フッ」と吹き消える）", "暗い区画でランタンを消す（大蛍が寄ってこなくなる）")
def _():
    d = 0.6
    puff = lp(white(0.3), 1200) * env(0.3, [(0, 0), (0.02, 1), (0.3, 0)])
    return mix(d, [(0, norm(puff), 0.8), (0.05, clunk(0.2, 200, 0.3), 0.3)])


@se("Fire_Loop", "仕掛け", LOOP, "燃え続ける火（ぱちぱち、ループ用）", "焚き火・松明・燃える菜園・溶岩の近く", loop=True)
def _():
    return make_loop(lambda d: fire_bed(d, 1500), 3.0, 0.4)


@se("LightPath_Appear", "仕掛け", SOFT, "光の道が現れる（低い和音がふくらみ、光が奥へ伸びていく）", "光の道のギミック（出現）")
def _():
    d = 2.2
    pad = lp(sum(osc(f * (1 + 0.004 * J(-1, 1)), 1.8, "saw") for f in (98, 147, 196)), curve(1.8, [(0, 200), (0.8, 1500), (1.8, 400)], "exp"))
    return reverb(mix(d, [(0, norm(pad) * env(1.8, [(0, 0), (0.5, 1), (1.8, 0)]), 0.7), (0.1, whoosh(1.5, [(0, 300), (0.8, 1400), (1.5, 400)], 0.6, 0.25, 1.2, q=0.5, body=1), 0.5)]), 1.3, 0.3, lpf=2500)


@se("LightPath_Vanish", "仕掛け", SOFT, "光の道が消える（ふくらんだ光がしぼんで沈む）", "光の道を消す（光の番人も消える）")
def _():
    d = 1.6
    pad = lp(sum(osc(f * np.ones(N(1.2)) * curve(1.2, [(0, 1), (1.2, 0.7)], "exp"), 1.2, "saw") for f in (98, 147, 196)), 900)
    return reverb(mix(d, [(0, norm(pad) * env(1.2, [(0, 0.8), (0.1, 1), (1.2, 0)]), 0.7), (0, whoosh(1.0, [(0, 1200), (1.0, 250)], 0.1, 0.3, 1.5, q=0.5, body=1), 0.5)]), 1.0, 0.25, lpf=2000)


@se("Seal_Break", "仕掛け", BIG, "封印・結界が解ける（うなりが高まって「ドォン」とはじけ、風が吹き抜ける）", "封印の解除・結界が消える・ボス部屋が開く")
def _():
    d = 2.8
    f = curve(1.0, [(0, 45), (1.0, 110)], "exp")
    build = lp(osc(f, 1.0, "saw") + osc(f * 1.5, 1.0, "saw"), curve(1.0, [(0, 200), (1.0, 1200)], "exp")) * env(1.0, [(0, 0), (0.95, 1), (1.0, 0)])
    boom = mix(1.5, [(0, thump(1.5, 80, 28, 0.35, 3), 1.0), (0, lp(brown(1.5), 800) * expdec(1.5, 0.35), 0.8),
                     (0, whoosh(1.4, [(0, 1500), (1.4, 200)], 0.05, 0.3, 2.5, q=0.5, body=1.2), 0.6)])
    return reverb(mix(d, [(0, norm(build), 0.6), (1.0, boom, 1.0)]), 1.8, 0.25, lpf=1800)


@se("Warp_Point", "仕掛け", MECH, "転移する（低く吸い込まれて「ドゥン」と別の場所へ）", "転移の魔法陣・ワープ地点")
def _():
    d = 1.8
    f = curve(0.9, [(0, 60), (0.9, 180)], "exp")
    suck = lp(osc(f, 0.9, "saw") + osc(f * 1.01, 0.9, "saw"), 700) * env(0.9, [(0, 0), (0.85, 1), (0.9, 0)])
    return reverb(mix(d, [(0, norm(suck), 0.6), (0, whoosh(0.9, [(0, 250), (0.85, 1800)], 0.8, 0.2, 0.2, q=0.5, body=1), 0.6),
                          (0.88, thump(0.8, 90, 30, 0.2, 2.5), 1.0), (0.88, lp(brown(0.6), 600) * expdec(0.6, 0.15), 0.5)]), 1.4, 0.25, lpf=1800)


@se("Save_Point", "仕掛け", SOFT, "休憩所で休む・記録する（温かい和音が「フワァン」と包む）", "休憩所・セーブ")
def _():
    d = 2.6
    parts = []
    for i, ch in enumerate([(98, 131, 165, 196), (110, 147, 175, 220)]):
        dd = 2.0
        p = lp(sum(osc(f * (1 + 0.003 * J(-1, 1)), dd, "saw") for f in ch), 1000) * env(dd, [(0, 0), (0.5, 1), (dd, 0)])
        parts.append((0.45 * i, norm(p), 0.6))
    parts.append((0, whoosh(1.5, [(0, 250), (0.8, 900), (1.5, 300)], 0.7, 0.3, 1.2, q=0.5, body=1), 0.3))
    return reverb(mix(d, parts), 1.6, 0.3, lpf=2200)


@se("Bell_Toll", "仕掛け", BIG, "低い鐘（遠くで「ゴォォン」と鳴る。高い響きは入れない）", "町の鐘・夜明け・イベントの合図")
def _():
    d = 5.0
    b = partials(4.5, [73, 146, 176, 219, 293], [2.2, 1.6, 1.2, 0.9, 0.6], [1, 0.6, 0.35, 0.3, 0.15], detune=0.002)
    b *= 1 + 0.15 * np.sin(phase_of(1.3, 4.5))   # うなり
    return reverb(mix(d, [(0, lp(b, 900), 1.0), (0, thump(0.3, 120, 60, 0.05, 1.5), 0.4)]), 2.5, 0.35, lpf=1200)


@se("Quake_Rumble", "仕掛け", BIG, "地響き（地面が大きく揺れる、約2.5秒）", "大きな仕掛けが動く・ボスの登場・遺跡が崩れる")
def _():
    d = 3.0
    r = rumble(2.8, 90) * env(2.8, [(0, 0), (0.4, 1), (2.0, 0.8), (2.8, 0)]) * (1 + 0.3 * np.sin(phase_of(7, 2.8)))
    return mix(d, [(0, r, 1.0), (0.2, grains(2.4, 40, dur=(0.01, 0.05), freq=(200, 1500), density="flat", amp=(0.2, 0.7)), 0.3)])


# ---------------- 空鯨戦のバリスタ ----------------

@se("Ballista_Place", "バリスタ", MECH, "バリスタを据える（重い木の台を「ドスン」と下ろし、きしむ）", "アスカがバリスタを運んで設置")
def _():
    d = 1.2
    return reverb(mix(d, [(0, thump(0.6, 110, 40, 0.1, 3), 1.0), (0, burst(0.3, 150, 1800, 0.05, -3), 0.7),
                          (0.15, creak(0.5, 90, 120, 600) * env(0.5, [(0, 0), (0.05, 1), (0.5, 0)]), 0.3)]), 0.8, 0.15, lpf=2000)


@se("Ballista_Load", "バリスタ", MECH, "銛を装填する（巻き上げの歯止めが「ガッガッガッ」と鳴り、「ガコン」と固定）", "バリスタの装填（R1）")
def _():
    d = 1.4
    parts = [(0.1 * i, clunk(0.12, 180 - 5 * i, 0.35), 0.45) for i in range(7)]
    parts.append((0, creak(0.8, 80, 110, 500) * env(0.8, [(0, 0), (0.1, 1), (0.8, 0.5)]), 0.25))
    parts.append((0.8, clunk(0.6, 70, 1.4), 1.0))
    return reverb(mix(d, parts), 0.8, 0.15, lpf=2000)


@se("Ballista_Fire", "バリスタ", BIG, "銛を撃ち出す（太い弦がはじけて「ドンッ」、銛が低くうなって飛ぶ）", "バリスタの射出（○）")
def _():
    d = 1.6
    string = karplus(55, 0.8, 0.994, 0.3) * expdec(0.8, 0.25)
    return reverb(mix(d, [(0, thump(0.6, 120, 40, 0.1, 3.5), 1.0), (0, lp(norm(string), 700), 0.6), (0, burst(0.3, 150, 2000, 0.04, -3), 0.7),
                          (0.02, whoosh(1.2, [(0, 700), (0.1, 1200), (1.2, 250)], 0.08, 0.25, 2.5, q=0.8, body=1.2), 0.6)]), 1.2, 0.2, lpf=2000)


@se("Harpoon_Hit", "バリスタ", BIG, "銛が刺さる（巨体に深く「ドスッ」と突き刺さる）", "銛が空鯨に刺さったとき")
def _():
    d = 1.4
    return reverb(mix(d, [(0, thump(1.0, 90, 30, 0.2, 4), 1.0), (0, burst(0.5, 120, 1500, 0.08, -4), 0.9), (0, click(0.006, 500), 0.4),
                          (0.02, lp(pink(0.6), 500) * expdec(0.6, 0.15), 0.5)]), 1.3, 0.2, lpf=1600)


@se("Ballista_Break", "バリスタ", BIG, "バリスタが壊れる（木の台が「バキバキッ」と砕け、部品が散らばる）", "尾の薙ぎ払いでバリスタが壊れる")
def _():
    d = 2.0
    return reverb(mix(d, [(0, thump(0.8, 130, 40, 0.15, 3.5), 1.0), (0, burst(0.5, 250, 3000, 0.05, -2), 0.8),
                          (0.01, grains(1.5, 70, dur=(0.01, 0.05), freq=(250, 2000)), 0.55),
                          (0.4, heel(0.3, 150, 70, 0.03), 0.4), (0.7, heel(0.3, 140, 70, 0.03), 0.3)]), 1.0, 0.2, lpf=2200)


# ---------------- 環境のループ ----------------

@se("Water_Stream_Loop", "環境", LOOP, "水路の流れ（さらさら・ごぼごぼ、ループ用）", "王都の地下水路・虹の水路・井戸・川", loop=True)
def _():
    def fn(d):
        flow = bp(pink(d), 900, 0.5) * (1 + 0.3 * slow_noise(d, 3))
        return norm(flow) + 0.5 * bubbles(d, int(d * 25), 250, 1200) + 0.3 * norm(lp(brown(d), 200))
    return make_loop(fn, 4.0, 0.5)


@se("Lava_Loop", "環境", LOOP, "溶岩がぼこぼこ煮える（重い泡がはじける、ループ用）", "炎胎の火口・溶岩洞・燃えがら坑道", loop=True)
def _():
    def fn(d):
        bed = norm(lp(brown(d), 150)) * 0.8
        blorps = np.zeros(N(d))
        for _ in range(int(d * 3)):
            at = N(J(0, d - 0.4))
            b = lp(np.sin(phase_of(curve(0.3, [(0, J(60, 90)), (0.3, J(150, 220))], "exp"), 0.3)) + 0.5 * pink(0.3), 600) * expdec(0.3, 0.08, 0.01)
            blorps[at:at + len(b)] += b * J(0.5, 1)
        return bed + norm(blorps) * 0.8 + 0.15 * crackle(d, 15, 800, False)
    return make_loop(fn, 4.0, 0.5)


@se("Swamp_Loop", "環境", LOOP, "沼の泡（どろっとした泡がときどき浮かぶ、ループ用）", "毒の湿地・蛍の沼・沈んだ村", loop=True)
def _():
    def fn(d):
        bed = norm(lp(pink(d), 300)) * 0.4
        return bed + bubbles(d, int(d * 4), 90, 300) * 1.2
    return make_loop(fn, 4.0, 0.5)


@se("Wind_Loop", "環境", LOOP, "吹き抜ける風（低くうなる、ループ用）", "山嶺・雲の裏側・高台・平原", loop=True)
def _():
    def fn(d):
        fc = 380 + 200 * slow_noise(d, 0.6)
        return norm(bp(pink(d), np.clip(fc, 150, 900), 0.8) * (1 + 0.45 * slow_noise(d, 1.2))) + 0.4 * norm(lp(brown(d), 150))
    return make_loop(fn, 5.0, 0.8)


@se("Gear_Loop", "環境", LOOP, "大きな歯車の仕掛け（重く回り、歯が「ゴトン、ゴトン」と噛む、ループ用）", "歯車の仕掛け・天界の工房・時計塔", loop=True)
def _():
    def fn(d):
        hum = norm(lp(brown(d), 120)) * 0.6
        teeth = np.zeros(N(d))
        per = 0.5
        for i in range(int(d / per) + 1):
            c = clunk(0.3, 80 if i % 2 else 95, 0.7)
            at = N(i * per)
            e = min(len(teeth), at + len(c))
            teeth[at:e] += c[: e - at]
        return hum + teeth * 0.8
    return make_loop(fn, 4.0, 0.5)


@se("Windmill_Loop", "環境", LOOP, "風車が回る（木の軸がゆっくりきしむ、ループ用）", "風車の丘", loop=True)
def _():
    def fn(d):
        per = 2.0
        out = np.zeros(N(d))
        for i in range(int(d / per) + 1):
            c = creak(1.2, 70, 95, 500) * env(1.2, [(0, 0), (0.3, 1), (1.2, 0)])
            at = N(i * per)
            e = min(len(out), at + len(c))
            out[at:e] += c[: e - at]
        wind = norm(bp(pink(d), 400, 0.7)) * 0.4
        return out * 0.5 + wind
    return make_loop(fn, 4.0, 0.5)


@se("Elevator_Loop", "環境", LOOP, "昇降機が動く（綱が巻かれ、床がごとごと揺れる、ループ用）", "昇降機・跳ね橋を上げ下げしている間", loop=True)
def _():
    def fn(d):
        rope = creak(d, 90, 100, 450) * 0.2
        rum = norm(lp(brown(d), 150)) * 0.7
        bumps = np.zeros(N(d))
        for i in range(int(d / 0.7) + 1):
            c = heel(0.2, 110, 60, 0.03)
            at = N(i * 0.7)
            e = min(len(bumps), at + len(c))
            bumps[at:e] += c[: e - at]
        return rum + rope + bumps * 0.4
    return make_loop(fn, 2.8, 0.35)


@se("Elevator_Stop", "環境", MECH, "昇降機が止まる（「ガコン」と止まって揺れが収まる）", "昇降機・跳ね橋が止まったとき")
def _():
    d = 1.0
    return reverb(mix(d, [(0, clunk(0.6, 65, 1.4), 1.0), (0.2, heel(0.3, 100, 50, 0.04), 0.3)]), 0.9, 0.15, lpf=1800)


# =====================================================================

def build(filters=None):
    os.makedirs(OUT, exist_ok=True)
    meta = []
    for s in SE:
        if filters and not any(f in s["name"] for f in filters):
            continue
        dsp.seed(s["name"])
        x = s["fn"]()
        x = weight_eq(x, s["eq"][0], s["eq"][1], loop=s["loop"])
        x = finish(x, s["level"], loop=s["loop"])
        write_wav(os.path.join(OUT, s["name"] + ".wav"), x)
        peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
        meta.append(dict(name=s["name"], group=s["group"], desc=s["desc"], use=s["use"], loop=s["loop"], sec=round(len(x) / SR, 3), peak_db=round(peak, 2)))
        print(f"{s['name']:22s} {len(x) / SR:5.2f}秒 ピーク {peak:6.2f}dB")
    if not filters:
        with open(os.path.join(HERE, "se_list.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"{len(meta)} 音 → {os.path.normpath(OUT)}")


if __name__ == "__main__":
    build(sys.argv[1:] or None)
