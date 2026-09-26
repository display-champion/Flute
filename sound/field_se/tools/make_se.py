# -*- coding: utf-8 -*-
"""
操作系・マップ系の SE をすべて合成して ../Resources/FieldSE/ に書き出す（第2版）。
  python make_se.py              … 全部作る
  python make_se.py Step_Stone   … 名前を指定して作る（部分一致）
必要なもの：Python 3 ＋ numpy ＋ scipy

方針
- キンキン系（金属の響き・鈴・きらめき）は使わない
- 第2版：音の高さが下がる正弦波の「ドッ」（thump）と泡の「ポコッ」（bubbles）は使わない（どれも同じ「ドポン」に聞こえるため）。
  かわりに材質ごとの鳴り方で作る：木の共鳴（コトッ）、石の共鳴（ゴトッ）、鉄の仕掛け（ガチャ）、布のこすれ、雑音の重さ（ドサッ）、水のしずく
- 足音はずっと鳴るので、小さく・短く・柔らかく（低い「ドン」を入れず、高い所も抑える）
"""
import os
import sys
import json
import numpy as np
from dsp import *  # noqa: F401,F403
import dsp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "Resources", "FieldSE")

SE = []

# 目標音量（50ms ごとの一番大きい所の RMS）
STEP, MOVE, MECH, BIG, LOOP, SOFT = -22, -15, -12, -10, -19, -15


def se(name, group, level, desc, use, loop=False, eq=(3.0, -4.0)):
    def reg(fn):
        SE.append(dict(name=name, group=group, level=level, desc=desc, use=use, loop=loop, eq=eq, fn=fn))
        return fn
    return reg


def J(a, b):
    return RNG.uniform(a, b)


def put(out, at, sig, g=1.0):
    s = N(at)
    e = min(len(out), s + len(sig))
    if e > s:
        out[s:e] += g * sig[: e - s]


# =====================================================================
# 材質の部品
# =====================================================================

def wood(d=0.3, size=1.0):
    """木を叩く「コトッ」（size が大きいほど低く長い）"""
    f = [J(170, 210) / size, J(390, 450) / size, J(640, 740) / size, J(1050, 1200) / size]
    return modal(d, f, [0.05 * size, 0.035 * size, 0.022 * size, 0.012 * size], [1, 0.7, 0.45, 0.25], length=0.004, bright=3500)


def stone(d=0.3, size=1.0):
    """石がぶつかる「ゴトッ」（雑音が多く、共鳴は短い）"""
    f = [J(120, 150) / size, J(290, 340) / size, J(520, 600) / size, J(900, 1000) / size]
    m = modal(d, f, [0.03 * size, 0.022 * size, 0.014 * size, 0.008 * size], [1, 0.8, 0.5, 0.3], length=0.006, bright=2500)
    return norm(m + 0.8 * body(d, 400 / size, 0.03 * size) + 0.25 * burst(d, 500, 2500, 0.01 * size, -2))


def iron(d=0.3, size=1.0):
    """鉄の仕掛けが噛み合う「ガチャッ」（響かせず、すぐ止める）"""
    f = [J(230, 270) / size, J(480, 540) / size, J(780, 860) / size, J(1150, 1300) / size]
    m = modal(d, f, [0.04 * size, 0.028 * size, 0.018 * size, 0.01 * size], [1, 0.8, 0.5, 0.3], length=0.002, bright=3000)
    return norm(lp(m, 2500) + 0.35 * burst(d, 700, 3000, 0.004, -1))


def ratchet(n, gap=0.09, size=1.0):
    """歯止め「カタ、カタ、カタ」（木と鉄の混ざった小さな音の連続）"""
    out = np.zeros(N(n * gap + 0.2))
    for i in range(n):
        put(out, i * gap + J(-0.008, 0.008), iron(0.08, 0.6 * size) * 0.6 + wood(0.08, 0.5 * size) * 0.4, J(0.6, 1))
    return out


def cloth(d, peak, width, lo=500, hi=1600):
    """服・体の動きの「サッ」（whoosh より柔らかく低い）"""
    fc = curve(d, [(0, lo), (peak, hi), (d, lo)], "exp")
    return norm(bp(pink(d), fc, 0.8) * bell_env(d, peak, width, 1.4))


def scrape(d, fc=900, rough=20):
    """こすれる「ザッ」「ズズッ」"""
    return norm(bp(white(d) * (0.6 + 0.4 * slow_noise(d, rough)), fc, 0.9))


def grind(d, f=450, rough=12):
    """石と石がこすれる「ゴリゴリ」（高さが揺れる、ざらついた雑音）"""
    fc = f * (1 + 0.25 * slow_noise(d, 2))
    g = bp(brown(d) + 0.25 * white(d), fc, 0.7) * (0.5 + 0.5 * np.abs(slow_noise(d, rough)))
    return norm(g + 0.3 * grains(d, int(d * 40), dur=(0.004, 0.02), freq=(400, 1500), density="flat", amp=(0.2, 0.8)))


def rumble(d, f=120):
    return norm(lp(brown(d), f, stages=2))


def creak(d, f0=110, f1=160, bright=700):
    """木がきしむ「ギィィ」"""
    f = curve(d, [(0, f0), (d * 0.5, f1), (d, f0 * 1.1)], "exp") * (1 + 0.04 * slow_noise(d, 8))
    stick = 0.55 + 0.45 * np.tanh(3 * np.sin(phase_of(J(9, 14), d) + 2 * slow_noise(d, 3)))
    return norm(bp(osc(f, d, "saw") * stick, bright, 2) + 0.4 * bp(osc(f, d, "saw"), bright * 2, 3))


def dust(d, fc0=2500, fc1=500):
    """砂ぼこり・土が落ちる「サァッ」"""
    return norm(lp(white(d), curve(d, [(0, fc0), (d, fc1)], "exp")) * env(d, [(0, 0), (0.02, 1), (d, 0)]))


def whoomph(d, top=1500):
    """火が燃え上がる「ボウッ」（雑音がふくらむ。音程はない）"""
    fc = curve(d, [(0, 150), (0.08, top), (d, top * 0.5)], "exp")
    return norm(lp(brown(d) + 0.2 * white(d), fc, stages=2) * env(d, [(0, 0), (0.06, 1), (d, 0)]))


def fire_bed(d, bright=1800):
    roar = lp(brown(d), bright) * (1 + 0.3 * slow_noise(d, 6))
    return norm(roar) + 0.3 * crackle(d, 40, 1200, False)


def pad(d, freqs, cut=1000):
    """低い和音（鈴を使わない温かい音）"""
    return norm(lp(sum(osc(f * (1 + 0.003 * J(-1, 1)), d, "saw") for f in freqs), cut))


# =====================================================================
# 足音（地面の種類 × 4 通り）
#   かかと → つま先 の2つで1歩。低い「ドン」は入れず、小さく短く柔らかく
# =====================================================================

def footfall(d, heel_fn, toe_fn, gap=(0.05, 0.09), toe_gain=(0.35, 0.6)):
    out = np.zeros(N(d))
    put(out, 0, heel_fn(), 1.0)
    put(out, J(*gap), toe_fn(), J(*toe_gain))
    return out


def leaves(d, n, lo=1300, hi=2800):
    """葉がこすれる柔らかいかけら（立ち上がりをなだらかに）"""
    out = np.zeros(N(d))
    for _ in range(n):
        gd = J(0.015, 0.035)
        g = bp(pink(gd), J(lo, hi), 1.2) * np.sin(np.pi * T(gd) / gd) ** 2
        put(out, J(0, d - gd), norm(g), J(0.3, 1.0))
    return out


def step_grass():
    def part(n, d):
        return norm(leaves(d, n) + 0.5 * cloth(d, 0.03, 0.025, 700, 1500)) + 0.15 * body(d, 280, 0.02)
    return footfall(0.3, lambda: part(int(J(6, 9)), 0.13), lambda: part(int(J(3, 5)), 0.09), toe_gain=(0.4, 0.55))


def step_dirt():
    def part(g):
        x = grains(0.08, int(J(12, 18)), dur=(0.006, 0.014), freq=(600, 2000), density="decay", amp=(0.2, 1.0))
        return norm(0.7 * x + 0.6 * burst(0.08, 350, 1800, 0.012 * g, -3) + 0.35 * body(0.08, 350, 0.012))
    return footfall(0.3, lambda: part(1.0), lambda: part(0.7))


def step_stone():
    def heel_():
        return norm(0.7 * modal(0.1, [J(650, 800), J(1250, 1450), J(2000, 2300)], [0.01, 0.007, 0.004], [1, 0.6, 0.3], length=0.003, bright=3000)
                    + 0.5 * body(0.1, 350, 0.01) + 0.2 * burst(0.1, 900, 2800, 0.004, -1))
    def toe_():
        return norm(0.6 * modal(0.06, [J(800, 950), J(1500, 1700)], [0.006, 0.004], length=0.003, bright=2500) + 0.2 * burst(0.06, 800, 2500, 0.004, -1))
    x = footfall(0.3, heel_, toe_, gap=(0.06, 0.1), toe_gain=(0.3, 0.45))
    return reverb(x, 0.5, 0.08, lpf=2200)   # 石の廊下の少しの響き


def step_wood():
    def heel_():
        return norm(0.8 * wood(0.15, J(0.9, 1.1)) + 0.4 * body(0.15, 350, 0.015) + 0.2 * burst(0.15, 800, 3000, 0.004))
    x = footfall(0.35, heel_, lambda: wood(0.1, J(0.6, 0.75)), gap=(0.06, 0.1), toe_gain=(0.3, 0.45))
    if J(0, 1) > 0.5:   # 2回に1回ほど、板が小さくきしむ
        put(x, J(0.08, 0.14), creak(0.16, 140, 170, 900) * env(0.16, [(0, 0), (0.04, 1), (0.16, 0)]), 0.08)
    return x


def step_water():
    d = 0.35
    sp = bp(white(d), J(900, 1400), 0.7) * env(d, [(0, 0), (0.006, 1), (0.05, 0.4), (0.14, 0), (d, 0)]) * (0.6 + 0.4 * slow_noise(d, 45))
    x = mix(d, [(0, norm(sp), 1.0), (0.06, gurgle(0.15, 350, 800, 30) * env(0.15, [(0, 0), (0.04, 1), (0.15, 0)]), 0.35),
                (0.08, droplets(0.25, int(J(2, 4)), 700, 1600), 0.2), (0, body(0.1, 280, 0.02), 0.2)])
    return x


def step_mud():
    d = 0.4
    fc = curve(0.2, [(0, J(800, 1000)), (0.2, J(300, 380))], "exp")
    squelch = bp(pink(0.2), fc, 1.4) * env(0.2, [(0, 0), (0.01, 1), (0.08, 0.6), (0.2, 0)]) * (0.6 + 0.4 * slow_noise(0.2, 40))
    suck = bp(white(0.12), curve(0.12, [(0, 650), (0.12, 260)], "exp"), 3) * env(0.12, [(0, 0), (0.03, 1), (0.12, 0)])
    return mix(d, [(0, norm(squelch), 1.0), (J(0.15, 0.2), norm(suck), 0.3), (0, body(0.12, 250, 0.03), 0.3)])


def step_metal():
    # 天界の工房の金属の網床：鈍い「ゴッ」と、網が小さくカタつく音（響かせない）
    def heel_():
        m = modal(0.12, [J(250, 290), J(520, 590), J(880, 980)], [0.025, 0.018, 0.01], [1, 0.6, 0.35], length=0.002, bright=2500)
        return norm(lp(m, 2000) + 0.4 * body(0.12, 350, 0.012))
    def rattle():
        out = np.zeros(N(0.1))
        for i in range(int(J(2, 4))):
            put(out, 0.012 * i + J(0, 0.006), modal(0.03, [J(1100, 1400)], [0.004], length=0.001, bright=3000), J(0.3, 0.6))
        return out
    x = footfall(0.3, heel_, lambda: heel_() * 0.6, gap=(0.06, 0.09), toe_gain=(0.3, 0.4))
    put(x, 0.01, rattle(), 0.2)
    return lp(x, 3000)


SURFACES = [
    ("Grass", "草", step_grass, "草地・森（草の葉がこすれる「サクッ」。低い音は入れない）"),
    ("Dirt", "土", step_dirt, "土の道・平原・洞窟の土（細かい砂利の「ジャリッ」）"),
    ("Stone", "石", step_stone, "石畳・石の廊下・洞窟の岩（靴底が当たる短い「コツッ」、少し響く）"),
    ("Wood", "木", step_wood, "木の床・橋・足場（板の「コトッ」。ときどき小さくきしむ）"),
    ("Water", "水", step_water, "浅い水・水たまり・水路の浅瀬（「パシャッ」としずく）"),
    ("Mud", "泥", step_mud, "沼・泥・毒の湿地（「ぐちゅっ」と沈んで引き抜く）"),
    ("Metal", "金属", step_metal, "天界の工房の金属の網床（鈍い「ゴッ」と網のカタつき。響かない）"),
]
STEP_LP = dict(Grass=3800, Dirt=3500, Stone=3500, Wood=3000, Water=3500, Mud=3000, Metal=2800)   # 耳障りにならないよう、上を落とす
for key, jp, fn, desc in SURFACES:
    for v in range(1, 5):
        se(f"Step_{key}_{v:02d}", "足音", STEP, f"{jp}の足音 {v}／4：{desc}", "歩き（走りは同じ音を少し大きく・高めに。FootstepSE が自動で選ぶ）", eq=(0.0, -4.0))((lambda f, c: lambda: lp(f(), c, stages=2))(fn, STEP_LP[key]))


# =====================================================================
# 操作
# =====================================================================

@se("Jump", "操作", MOVE, "ジャンプの踏み切り（つま先が地面を「ザッ」と蹴り、服と髪が下から「ファッ」とあおられる）", "ジャンプ（Space）")
def _():
    d = 0.5
    kick = scrape(0.08, 1000) * env(0.08, [(0, 0), (0.004, 1), (0.08, 0)])
    flutter = bp(pink(0.4), curve(0.4, [(0, 350), (0.15, 900), (0.4, 500)], "exp"), 1.0) * bell_env(0.4, 0.13, 0.06, 1.6) * (0.7 + 0.3 * np.sin(phase_of(22, 0.4)))
    return mix(d, [(0, kick, 0.8), (0, step_dirt(), 0.4), (0.04, norm(flutter), 0.9)])


@se("Land", "操作", MOVE, "着地（靴底が「ザッ」と着いて、服が落ちつく）", "ジャンプの着地（地面の足音も一緒に鳴る）")
def _():
    d = 0.4
    return mix(d, [(0, body(0.15, 320, 0.025), 0.6), (0, step_dirt(), 0.8), (0.02, cloth(0.2, 0.04, 0.03, 400, 1000), 0.4)])


@se("Land_Heavy", "操作", MECH, "高い所からの着地（ひざで受ける「ドサッ」と砂ぼこり）", "高い所からの落下など")
def _():
    d = 0.9
    return mix(d, [(0, body(0.5, 250, 0.07), 1.0), (0, step_dirt(), 0.8), (0.03, scrape(0.25, 800) * env(0.25, [(0, 0), (0.02, 1), (0.25, 0)]), 0.4),
                   (0.03, dust(0.6, 2000, 400), 0.35), (0.02, cloth(0.3, 0.06, 0.04, 400, 1100), 0.5)])


@se("Dash", "操作", MOVE, "ダッシュ（空気を押しのける鋭い「シュバッ」と、靴底が地面を「ズザーッ」とすべって止まる）", "ダッシュ（L1／C、0.18秒で3m）")
def _():
    d = 0.6
    air = whoosh(0.3, [(0, 600), (0.06, 2200), (0.3, 500)], 0.06, 0.025, 2.5, q=1.0, body=0.3)
    skid = scrape(0.28, 700, 35) * env(0.28, [(0, 0), (0.02, 1), (0.2, 0.6), (0.28, 0)])
    return mix(d, [(0, step_dirt(), 0.5), (0, air, 1.0), (0.17, skid, 0.7), (0.17, dust(0.3, 1500, 400), 0.25)])


@se("Dodge_Roll", "操作", MOVE, "側転回避（服がひるがえり、手と背で地面を転がって、足で着く）", "側転回避（×／左Ctrl、0.75秒）")
def _():
    d = 0.85
    return mix(d, [(0, step_dirt(), 0.6), (0.03, cloth(0.5, 0.15, 0.08, 400, 1200), 0.8),
                   (0.25, scrape(0.1, 1300) * env(0.1, [(0, 0), (0.01, 1), (0.1, 0)]), 0.4),    # 手をつく
                   (0.35, body(0.25, 300, 0.035), 0.5), (0.35, scrape(0.25, 700) * env(0.25, [(0, 0), (0.03, 1), (0.25, 0)]), 0.4),  # 背で転がる
                   (0.62, step_dirt(), 0.7)])


@se("Swim_Stroke", "操作", MOVE, "泳ぐ（腕が水を押す「ザブッ」と、したたるしずく）", "泳いでいるときのひとかき")
def _():
    d = 0.8
    push = bp(white(0.4), curve(0.4, [(0, 500), (0.18, 1300), (0.4, 600)], "exp"), 0.8) * env(0.4, [(0, 0), (0.15, 1), (0.4, 0)])
    return mix(d, [(0, norm(push), 0.8), (0.05, gurgle(0.35, 300, 800) * env(0.35, [(0, 0), (0.1, 1), (0.35, 0)]), 0.35), (0.2, droplets(0.5, 10), 0.3)])


@se("Water_Enter", "操作", MECH, "水に入る（水面が「バシャーン」と割れ、しぶきが降ってくる）", "水路・湖に入ったとき")
def _():
    d = 1.3
    crash = bp(white(0.5), curve(0.5, [(0, 1700), (0.5, 700)], "exp"), 0.7) * env(0.5, [(0, 0), (0.005, 1), (0.1, 0.5), (0.5, 0)])
    return mix(d, [(0, norm(crash), 1.0), (0, body(0.3, 350, 0.05), 0.4), (0.05, gurgle(0.6, 250, 700) * env(0.6, [(0, 0), (0.05, 1), (0.6, 0)]), 0.35),
                   (0.12, droplets(1.0, 30, 700, 2200) * env(1.0, [(0, 1), (1.0, 0.2)]), 0.4)])


@se("Slide_Loop", "操作", LOOP, "ぬめった床を滑る（ぬるぬるとこすれる、ループ用）", "水路ナメクジの跡など、滑る床の上にいる間", loop=True)
def _():
    def fn(d):
        return gurgle(d, 300, 800, 10) * 0.8 + 0.3 * norm(lp(pink(d), 500) * (1 + 0.5 * slow_noise(d, 4)))
    return make_loop(fn, 2.0, 0.3)


@se("Climb_Grab", "操作", MOVE, "よじ登る・つかまる（手のひらが縁を「パシッ」とつかみ、体を引き上げる）", "段差・ツタ・崖をつかむ")
def _():
    d = 0.5
    return mix(d, [(0, burst(0.05, 500, 3000, 0.006, -1), 0.8), (0.005, grains(0.1, 8, freq=(600, 2500)), 0.3),
                   (0.08, cloth(0.35, 0.12, 0.06, 400, 1100), 0.6), (0.1, scrape(0.2, 700) * env(0.2, [(0, 0), (0.05, 1), (0.2, 0)]), 0.3)])


@se("Heal_Potion", "操作", SOFT, "回復薬を使う（栓を「キュポッ」と抜き、ごくりと飲み、温かく「フワァ」と広がる）", "回復薬（R2／R）")
def _():
    d = 1.7
    cork = modal(0.08, [J(650, 750), J(1300, 1450)], [0.012, 0.006], [1, 0.4], length=0.004, bright=2500) + 0.4 * burst(0.08, 600, 2500, 0.01)
    gulp = lambda: gurgle(0.13, 220, 420, 30) * env(0.13, [(0, 0), (0.03, 1), (0.13, 0)])
    warm = pad(1.1, (98, 147, 196, 247), 900) * env(1.1, [(0, 0), (0.35, 1), (1.1, 0)])
    return reverb(mix(d, [(0, norm(cork), 0.6), (0.2, gulp(), 0.5), (0.36, gulp(), 0.45), (0.5, warm, 0.6),
                          (0.5, whoosh(0.9, [(0, 300), (0.4, 900), (0.9, 300)], 0.4, 0.15, 1.2, q=0.5, body=1.0), 0.3)]), 1.0, 0.25, lpf=2500)


@se("Item_Pickup", "操作", SOFT, "物を拾う（革の袋の口を開けて「ガサッ」と入れ、中の物が「コトッ」と当たる）", "ドロップ品・素材を拾ったとき")
def _():
    d = 0.6
    crinkle = bp(pink(0.2), 750, 1.2) * env(0.2, [(0, 0), (0.02, 1), (0.2, 0)]) * (0.5 + 0.5 * np.abs(slow_noise(0.2, 70)))
    pull = bp(white(0.1), curve(0.1, [(0, 700), (0.1, 1300)], "exp"), 2) * env(0.1, [(0, 0), (0.03, 1), (0.1, 0)])
    return mix(d, [(0, norm(pull), 0.35), (0.08, norm(crinkle), 0.8), (0.2, wood(0.15, 0.9), 0.45), (0.26, wood(0.1, 0.8), 0.15)])


@se("Gather_Plant", "操作", MOVE, "採取する（草をかき分け、根が「ブチブチッ」とちぎれる）", "採取ポイント")
def _():
    d = 0.8
    rustle = grains(0.4, 40, dur=(0.004, 0.015), freq=(1000, 3500), density="flat", amp=(0.2, 1.0)) * env(0.4, [(0, 0.3), (0.1, 1), (0.4, 0.4)])
    tear = grains(0.12, 12, dur=(0.003, 0.012), freq=(300, 1500), density="decay", amp=(0.5, 1.0))
    return mix(d, [(0, norm(rustle), 0.5), (0, cloth(0.3, 0.1, 0.06, 600, 1500), 0.3), (0.4, norm(tear), 1.0), (0.42, dust(0.25, 1500, 400), 0.25)])


@se("Player_Down", "操作", MECH, "フィナが倒れる（ひざをつき、体が「ドサッ」と地面に崩れる）", "HPが0になったとき")
def _():
    d = 1.6
    low = pad(1.2, (41, 62), 250) * env(1.2, [(0, 0), (0.3, 1), (1.2, 0)])
    return reverb(mix(d, [(0, cloth(0.4, 0.1, 0.06, 400, 1000), 0.5), (0.12, body(0.2, 300, 0.03), 0.5),
                          (0.38, body(0.6, 220, 0.08), 1.0), (0.38, scrape(0.3, 600) * env(0.3, [(0, 0), (0.02, 1), (0.3, 0)]), 0.4),
                          (0.4, dust(0.5, 1500, 300), 0.25), (0.3, low, 0.3)]), 1.0, 0.15, lpf=1800)


@se("Respawn", "操作", SOFT, "復活する（低い和音が「フワァン」と立ちのぼる）", "倒れてから2.5秒後の復活")
def _():
    d = 1.8
    p = lp(pad(d, (65.4, 98, 131, 165), 4000), curve(d, [(0, 200), (0.8, 1400), (d, 300)], "exp"))
    return reverb(mix(d, [(0, norm(p) * env(d, [(0, 0), (0.7, 1), (d, 0)]), 0.8),
                          (0, whoosh(1.2, [(0, 200), (0.7, 1500), (1.2, 500)], 0.7, 0.2, 1.0, q=0.5, body=1.0), 0.5)]), 1.2, 0.3, lpf=2500)


# =====================================================================
# 仕掛け（スイッチ・扉・壁など）
# =====================================================================

@se("Switch_On", "仕掛け", MECH, "スイッチを押す（石のボタンが「ゴリッ、ゴトッ」と沈み、奥で鉄の仕掛けが「ガチャン」と外れて、遠くが鳴り出す）", "イベントのスイッチ・仕掛けの起動")
def _():
    d = 1.4
    return reverb(mix(d, [(0, grind(0.12, 600) * env(0.12, [(0, 0), (0.02, 1), (0.12, 1)]), 0.35), (0.1, stone(0.3, 0.8), 0.8),
                          (0.3, iron(0.3, 1.2), 0.9), (0.42, ratchet(3, 0.07), 0.4),
                          (0.45, rumble(0.9, 90) * env(0.9, [(0, 0), (0.2, 1), (0.9, 0)]), 0.3)]), 0.9, 0.15, lpf=2200)


@se("Floor_Switch", "仕掛け", MECH, "床のスイッチを踏む（石板が「ズズッ」と沈み、すき間から空気が抜けて「ゴトン」と止まる）", "踏むと動く床の仕掛け")
def _():
    d = 1.0
    return reverb(mix(d, [(0, grind(0.35, 380) * env(0.35, [(0, 0), (0.05, 1), (0.35, 0.8)]), 0.6), (0.05, dust(0.3, 1800, 600), 0.25),
                          (0.35, stone(0.4, 1.3), 1.0)]), 0.7, 0.12, lpf=2000)


@se("Lever_Pull", "仕掛け", MECH, "レバーを引く（木の柄がきしみ、歯止めが「カタカタ」と送られ、最後に「ガコン」と倒れる）", "レバーの仕掛け")
def _():
    d = 1.3
    return reverb(mix(d, [(0, creak(0.55, 100, 140, 650) * env(0.55, [(0, 0), (0.05, 1), (0.55, 0.5)]), 0.35), (0.05, ratchet(5, 0.1), 0.7),
                          (0.58, iron(0.4, 1.4), 0.8), (0.58, wood(0.4, 1.3), 0.6)]), 0.8, 0.15, lpf=2200)


@se("Wall_Lower", "仕掛け", BIG, "石の壁が降りる（止め金が外れ、重い石が地響きを立てて沈み、底で「ズシン」と止まって砂が落ちる、約2.5秒）", "通路をふさぐ壁が下がる・壁が沈んで道が開く")
def _():
    d = 3.4
    body_ = rumble(2.5, 100) * env(2.5, [(0, 0), (0.15, 1), (2.3, 1), (2.5, 0)])
    g = grind(2.5, 420) * env(2.5, [(0, 0), (0.2, 1), (2.3, 0.8), (2.5, 0)])
    debris = grains(2.4, 45, dur=(0.008, 0.04), freq=(300, 1800), density="flat", amp=(0.2, 0.8))
    end = mix(1.0, [(0, stone(0.6, 2.0), 1.0), (0, body(0.8, 180, 0.15), 0.8), (0.05, dust(0.9, 1800, 300), 0.4),
                    (0.1, grains(0.8, 25, freq=(400, 1800)), 0.25)])
    return reverb(mix(d, [(0, iron(0.3, 1.5), 0.6), (0.05, body_, 0.8), (0.05, g, 0.45), (0.1, debris, 0.2), (2.45, end, 1.0)]), 1.3, 0.18, lpf=1800)


@se("Wall_Raise", "仕掛け", BIG, "石の壁がせり上がる（下から押し上げられて「ギギギ」とこすれ、上で「ガコン」と固定、約2秒）", "壁や柱が地面からせり上がって道をふさぐ・足場ができる")
def _():
    d = 2.8
    body_ = rumble(2.0, 130) * env(2.0, [(0, 0), (0.1, 0.6), (1.8, 1), (2.0, 0)])
    g = grind(2.0, 520, 20) * env(2.0, [(0, 0), (0.15, 1), (1.9, 0.9), (2.0, 0)])
    return reverb(mix(d, [(0, dust(0.4, 1500, 400), 0.3), (0.05, body_, 0.7), (0.05, g, 0.55), (0.1, grains(1.9, 30, freq=(300, 1600), density="flat"), 0.15),
                          (1.95, stone(0.5, 1.4), 0.8), (1.97, iron(0.4, 1.6), 0.7)]), 1.1, 0.18, lpf=1800)


@se("Gate_Portcullis", "仕掛け", BIG, "鉄格子の門が落ちる（巻き上げの歯止めが外れて「ガラガラ」と走り、格子が「ズドン」と刺さってカタカタ揺れる）", "落とし格子・閉じ込められるイベント")
def _():
    d = 2.0
    run = ratchet(9, 0.05, 0.9)
    drop = mix(1.0, [(0, iron(0.6, 2.2), 1.0), (0, body(0.8, 220, 0.12), 0.9), (0, stone(0.4, 1.2), 0.5)])
    settle = np.zeros(N(0.6))
    for i in range(4):
        put(settle, 0.08 + 0.1 * i, iron(0.1, 1.2), 0.35 * (0.6 ** i))
    return reverb(mix(d, [(0, run, 0.6), (0.48, drop, 1.0), (0.5, settle, 1.0), (0.5, dust(0.6, 1500, 400), 0.2)]), 1.2, 0.18, lpf=1800)


@se("Gate_Open_Large", "仕掛け", BIG, "大きな門が開く（かんぬきが「ゴトン」と外れ、重い木の門が低くきしみながら開ききる、約3秒）", "南門・城門・大聖堂などの大扉")
def _():
    d = 3.6
    cr = creak(2.8, 55, 75, 350) * env(2.8, [(0, 0), (0.3, 1), (2.4, 0.8), (2.8, 0)])
    return reverb(mix(d, [(0, wood(0.5, 2.0), 0.9), (0.03, iron(0.3, 1.8), 0.4), (0.3, cr, 0.6),
                          (0.3, rumble(2.8, 90) * env(2.8, [(0, 0), (0.3, 1), (2.8, 0)]), 0.5), (3.05, wood(0.6, 2.4), 0.8)]), 1.5, 0.22, lpf=1600)


@se("Door_Open_Wood", "仕掛け", MECH, "木の扉を開ける（取っ手の金具が「カチャ」と外れ、「ギィィ」ときしんで開く）", "家・小屋・ダンジョンの木の扉（○／F で調べる）")
def _():
    d = 1.4
    return reverb(mix(d, [(0, iron(0.15, 0.7), 0.6), (0.12, creak(0.9, 120, 170, 750) * env(0.9, [(0, 0), (0.1, 1), (0.8, 0.5), (0.9, 0)]), 0.5),
                          (0.12, cloth(0.9, 0.45, 0.2, 250, 600), 0.2)]), 0.8, 0.15, lpf=2500)


@se("Door_Close_Wood", "仕掛け", MECH, "木の扉が閉まる（風を押して「バタン」と板が当たり、かんぬきが「カチャン」と掛かる）", "扉が閉まる・閉じ込められる")
def _():
    d = 1.0
    return reverb(mix(d, [(0, cloth(0.3, 0.22, 0.06, 250, 700), 0.4), (0.25, wood(0.5, 1.6), 1.0), (0.25, body(0.3, 300, 0.04), 0.5),
                          (0.45, iron(0.2, 0.8), 0.5)]), 0.9, 0.18, lpf=2200)


@se("Door_Open_Stone", "仕掛け", BIG, "石の扉が横に開く（重い石が「ズズズ」と引きずられ、端で「ゴトン」と止まる、約1.6秒）", "遺跡・祠・封印された部屋の石扉")
def _():
    d = 2.2
    g = grind(1.6, 350, 8) * env(1.6, [(0, 0), (0.15, 1), (1.5, 0.9), (1.6, 0)])
    return reverb(mix(d, [(0, stone(0.3, 1.0), 0.5), (0.1, g, 0.7), (0.1, rumble(1.6, 100) * env(1.6, [(0, 0), (0.15, 1), (1.6, 0)]), 0.5),
                          (1.65, stone(0.6, 1.8), 1.0), (1.7, dust(0.4, 1500, 400), 0.2)]), 1.1, 0.18, lpf=1800)


@se("Door_Locked", "仕掛け", MECH, "鍵がかかっている（取っ手を引いても、扉が枠に当たって「ガタッ、ガタッ」と止まる）", "開かない扉・宝箱を調べたとき")
def _():
    d = 0.6
    out = np.zeros(N(d))
    for i, at in enumerate((0, 0.13, 0.24)):
        put(out, at, wood(0.2, 1.3) * 0.7 + iron(0.2, 0.8) * 0.4, 1.0 - 0.15 * i)
    return out


@se("Key_Unlock", "仕掛け", MECH, "鍵を開ける（鍵を差し込み、回すと中で「カチ…ガチャリ」と外れる）", "鍵のかかった扉・宝箱を開けたとき")
def _():
    d = 0.8
    insert = scrape(0.15, 1500, 40) * env(0.15, [(0, 0), (0.05, 1), (0.15, 0)])
    return reverb(mix(d, [(0, insert, 0.2), (0.2, iron(0.1, 0.5), 0.4), (0.35, iron(0.3, 1.0), 1.0), (0.36, wood(0.2, 1.0), 0.3)]), 0.5, 0.12, lpf=2200)


@se("Chest_Open", "仕掛け", MECH, "宝箱を開ける（留め金が「カチャ」、ふたが「ギッ」ときしみ、後ろへ倒れて「ゴトン」）", "宝箱")
def _():
    d = 1.0
    return reverb(mix(d, [(0, iron(0.15, 0.7), 0.5), (0.08, creak(0.4, 110, 150, 700) * env(0.4, [(0, 0), (0.05, 1), (0.4, 0)]), 0.45),
                          (0.5, wood(0.4, 1.4), 1.0), (0.5, body(0.2, 300, 0.03), 0.3)]), 0.6, 0.12, lpf=2200)


@se("Treasure_Get", "仕掛け", SOFT, "宝を手に入れた（低い和音が温かく広がる。鈴の音は使わない）", "宝箱の中身・大事な物を手に入れたとき")
def _():
    d = 2.0
    parts = []
    for at, ch in [(0, (131, 165, 196)), (0.22, (147, 196, 247)), (0.44, (131, 196, 262))]:
        dd = 1.5 - at
        parts.append((at, pad(dd, ch, 1300) * env(dd, [(0, 0), (0.03, 1), (0.2, 0.6), (dd, 0)]), 0.7 if at < 0.4 else 1.0))
    parts.append((0.44, whoosh(1.0, [(0, 300), (0.3, 1000), (1.0, 300)], 0.3, 0.2, 1.5, q=0.5, body=1), 0.25))
    return reverb(mix(d, parts), 1.3, 0.3, lpf=2500)


@se("Bridge_Form", "仕掛け", BIG, "錬成の橋ができる（魔力がうなり、板と石が「コトッ、ゴトッ」と交互に組み上がって、最後にしっかり噛み合う）", "錬成の橋・足場が現れるギミック")
def _():
    d = 2.4
    hum = pad(1.8, (55, 82), 500) * env(1.8, [(0, 0), (0.3, 1), (1.8, 0)])
    parts = [(0, hum, 0.35)]
    for i in range(6):
        piece = wood(0.3, 1.1 - 0.05 * i) if i % 2 == 0 else stone(0.3, 1.0 - 0.05 * i)
        parts.append((0.25 + 0.22 * i + J(-0.02, 0.02), piece, 0.6 + 0.06 * i))
    parts.append((1.65, wood(0.5, 1.6), 0.8))
    parts.append((1.66, iron(0.4, 1.4), 0.6))
    return reverb(mix(d, parts), 1.1, 0.18, lpf=2000)


@se("Floor_Collapse", "仕掛け", BIG, "足場が崩れる（ひびが「ピシピシ」と走り、崩れ落ちて、下で砕ける）", "崩れる床・落とし穴・崩れた王都")
def _():
    d = 2.8
    crack = np.zeros(N(0.5))
    for i in range(10):
        put(crack, 0.03 * i + J(0, 0.02), norm(burst(0.03, 400, 2500, 0.004, -1) + stone(0.03, 0.5)), J(0.3, 0.8))
    crumble = grains(1.6, 80, dur=(0.01, 0.06), freq=(200, 1800), density="flat", amp=(0.2, 1.0)) * env(1.6, [(0, 0.3), (0.3, 1), (1.6, 0)])
    return reverb(mix(d, [(0, crack, 0.7), (0.45, stone(0.5, 1.6), 0.9), (0.45, rumble(1.5, 140) * env(1.5, [(0, 0), (0.05, 1), (1.5, 0)]), 0.6),
                          (0.45, crumble, 0.5), (1.45, body(0.9, 200, 0.15), 0.6), (1.45, stone(0.5, 2.0), 0.5), (1.5, dust(1.0, 1500, 300), 0.3)]), 1.4, 0.2, lpf=1800)


@se("Rock_Fall", "仕掛け", BIG, "落石（岩が斜面をはねながら落ちてきて、ゴロン、ゴトンと転がり止まる）", "落石の仕掛け・崖崩れ")
def _():
    d = 2.6
    parts = [(0, rumble(1.8, 160) * env(1.8, [(0, 0), (0.3, 1), (1.8, 0)]), 0.4)]
    for i, (at, sz) in enumerate([(0.3, 1.8), (0.62, 1.6), (0.8, 1.3), (1.05, 1.5), (1.3, 1.1), (1.45, 0.9)]):
        parts.append((at, stone(0.5, sz), 1.0 - 0.1 * i))
        parts.append((at, grains(0.3, 10, freq=(300, 1500)), 0.25))
    parts.append((0.3, dust(1.5, 1500, 300), 0.25))
    return reverb(mix(d, parts), 1.3, 0.18, lpf=1800)


@se("Barrel_Break", "仕掛け", MECH, "樽を壊す（板が「バキッ」と割れて散らばり、鉄のたがが転がって止まる）", "樽を叩く（樽の子を見分ける）")
def _():
    d = 1.1
    hoop = np.zeros(N(0.7))
    for i, at in enumerate((0.0, 0.14, 0.25, 0.33)):
        put(hoop, at, lp(iron(0.1, 1.3), 1500), 0.5 * (0.7 ** i))
    return reverb(mix(d, [(0, wood(0.3, 1.2), 1.0), (0, burst(0.2, 400, 2500, 0.02, -2), 0.7),
                          (0.01, grains(0.6, 30, dur=(0.01, 0.04), freq=(300, 1500)), 0.5), (0.2, hoop, 1.0),
                          (0.15, wood(0.2, 0.8), 0.3), (0.3, wood(0.2, 0.7), 0.2)]), 0.6, 0.12, lpf=2200)


@se("Crate_Break", "仕掛け", MECH, "木箱を壊す（薄い板が「バシャッ」と割れて、板きれが落ちる）", "木箱・箱入りの忘れ物")
def _():
    d = 0.9
    return mix(d, [(0, wood(0.2, 0.7), 0.8), (0, burst(0.2, 600, 3000, 0.015, -1), 0.8), (0.005, grains(0.5, 25, dur=(0.006, 0.03), freq=(500, 2200)), 0.5),
                   (0.18, wood(0.15, 0.6), 0.35), (0.3, wood(0.15, 0.55), 0.25), (0.42, wood(0.12, 0.5), 0.15)])


@se("Torch_Ignite", "仕掛け", MECH, "松明・灯りに火をつける（火が「ボウッ」と燃え移り、ぱちぱち燃え始める）", "燭台・坑道の灯り・墓の灯り・焚き火")
def _():
    d = 1.4
    return mix(d, [(0, whoomph(0.5, 1500), 0.9), (0.03, fire_bed(1.3, 1800) * env(1.3, [(0, 0), (0.1, 1), (0.5, 0.5), (1.3, 0)]), 0.6)])


@se("Lantern_On", "仕掛け", SOFT, "ランタンをつける（小窓を開けて、芯に「ポッ」と火が移る）", "暗闇のギミックでランタンをつける")
def _():
    d = 0.8
    return mix(d, [(0, iron(0.1, 0.6), 0.3), (0.1, whoomph(0.25, 900), 0.6), (0.12, fire_bed(0.6, 1200) * env(0.6, [(0, 0), (0.05, 1), (0.6, 0)]), 0.3)])


@se("Lantern_Off", "仕掛け", SOFT, "ランタンを消す（「フッ」と吹き消し、小窓を閉める）", "暗い区画でランタンを消す（大蛍が寄ってこなくなる）")
def _():
    d = 0.6
    puff = lp(white(0.25), 1000) * env(0.25, [(0, 0), (0.02, 1), (0.25, 0)])
    return mix(d, [(0, norm(puff), 0.8), (0.2, iron(0.1, 0.6), 0.3)])


@se("Fire_Loop", "仕掛け", LOOP, "燃え続ける火（ぱちぱち、ループ用）", "焚き火・松明・燃える菜園・溶岩の近く", loop=True)
def _():
    return make_loop(lambda d: fire_bed(d, 1500), 3.0, 0.4)


@se("LightPath_Appear", "仕掛け", SOFT, "光の道が現れる（低い和音がふくらみ、光が奥へ伸びていく）", "光の道のギミック（出現）")
def _():
    d = 2.2
    p = lp(pad(1.8, (98, 147, 196), 4000), curve(1.8, [(0, 200), (0.8, 1500), (1.8, 400)], "exp"))
    return reverb(mix(d, [(0, norm(p) * env(1.8, [(0, 0), (0.5, 1), (1.8, 0)]), 0.7), (0.1, whoosh(1.5, [(0, 300), (0.8, 1400), (1.5, 400)], 0.6, 0.25, 1.2, q=0.5, body=1), 0.5)]), 1.3, 0.3, lpf=2500)


@se("LightPath_Vanish", "仕掛け", SOFT, "光の道が消える（ふくらんだ光がしぼんで沈む）", "光の道を消す（光の番人も消える）")
def _():
    d = 1.6
    p = lp(sum(osc(f * curve(1.2, [(0, 1), (1.2, 0.7)], "exp"), 1.2, "saw") for f in (98, 147, 196)), 900)
    return reverb(mix(d, [(0, norm(p) * env(1.2, [(0, 0.8), (0.1, 1), (1.2, 0)]), 0.7), (0, whoosh(1.0, [(0, 1200), (1.0, 250)], 0.1, 0.3, 1.5, q=0.5, body=1), 0.5)]), 1.0, 0.25, lpf=2000)


@se("Seal_Break", "仕掛け", BIG, "封印・結界が解ける（うなりが高まって「バァン」とはじけ、風が吹き抜ける）", "封印の解除・結界が消える・ボス部屋が開く")
def _():
    d = 2.8
    f = curve(1.0, [(0, 45), (1.0, 110)], "exp")
    build = lp(osc(f, 1.0, "saw") + osc(f * 1.5, 1.0, "saw"), curve(1.0, [(0, 200), (1.0, 1200)], "exp")) * env(1.0, [(0, 0), (0.95, 1), (1.0, 0)])
    burst_ = mix(1.6, [(0, body(1.5, 400, 0.3, color=-4), 1.0), (0, burst(0.4, 300, 3000, 0.05, -2), 0.6),
                       (0, whoosh(1.5, [(0, 1500), (1.5, 200)], 0.05, 0.3, 2.5, q=0.5, body=1.2), 0.7)])
    return reverb(mix(d, [(0, norm(build), 0.6), (1.0, burst_, 1.0)]), 1.6, 0.25, lpf=1800)


@se("Warp_Point", "仕掛け", MECH, "転移する（低いうなりに吸い込まれ、空気が「フォン」と裏返って別の場所へ）", "転移の魔法陣・ワープ地点")
def _():
    d = 1.8
    f = curve(0.9, [(0, 60), (0.9, 180)], "exp")
    suck = lp(osc(f, 0.9, "saw") + osc(f * 1.01, 0.9, "saw"), 700) * env(0.9, [(0, 0), (0.85, 1), (0.9, 0)])
    flip = whoosh(0.8, [(0, 1800), (0.05, 1500), (0.8, 250)], 0.02, 0.2, 2.5, q=0.5, body=1)
    return reverb(mix(d, [(0, norm(suck), 0.6), (0, whoosh(0.9, [(0, 250), (0.85, 1800)], 0.8, 0.2, 0.2, q=0.5, body=1), 0.6), (0.88, flip, 0.9),
                          (0.88, body(0.5, 300, 0.08, color=-4), 0.5)]), 1.4, 0.25, lpf=1800)


@se("Save_Point", "仕掛け", SOFT, "休憩所で休む・記録する（温かい和音が「フワァン」と包む）", "休憩所・セーブ")
def _():
    d = 2.6
    parts = []
    for i, ch in enumerate([(98, 131, 165, 196), (110, 147, 175, 220)]):
        parts.append((0.45 * i, pad(2.0, ch, 1000) * env(2.0, [(0, 0), (0.5, 1), (2.0, 0)]), 0.6))
    parts.append((0, whoosh(1.5, [(0, 250), (0.8, 900), (1.5, 300)], 0.7, 0.3, 1.2, q=0.5, body=1), 0.3))
    return reverb(mix(d, parts), 1.6, 0.3, lpf=2200)


@se("Bell_Toll", "仕掛け", BIG, "低い鐘（撞木が当たり、遠くで「ゴォォン」と鳴る。高い響きは入れない）", "町の鐘・夜明け・イベントの合図")
def _():
    d = 5.0
    b = partials(4.5, [73, 146, 176, 219, 293], [2.2, 1.6, 1.2, 0.9, 0.6], [1, 0.6, 0.35, 0.3, 0.15], detune=0.002)
    b *= 1 + 0.15 * np.sin(phase_of(1.3, 4.5))
    return reverb(mix(d, [(0, lp(b, 900), 1.0), (0, wood(0.3, 2.0), 0.4)]), 2.5, 0.35, lpf=1200)


@se("Quake_Rumble", "仕掛け", BIG, "地響き（地面が大きく揺れ、小石がぱらぱら落ちる、約2.5秒）", "大きな仕掛けが動く・ボスの登場・遺跡が崩れる")
def _():
    d = 3.0
    r = rumble(2.8, 90) * env(2.8, [(0, 0), (0.4, 1), (2.0, 0.8), (2.8, 0)]) * (1 + 0.3 * slow_noise(2.8, 7))
    return mix(d, [(0, r, 1.0), (0.2, grains(2.4, 40, dur=(0.01, 0.05), freq=(250, 1500), density="flat", amp=(0.2, 0.7)), 0.3)])


# ---------------- 空鯨戦のバリスタ ----------------

@se("Ballista_Place", "バリスタ", MECH, "バリスタを据える（重い木の台を「ドスン」と下ろし、脚がきしんで落ちつく）", "アスカがバリスタを運んで設置")
def _():
    d = 1.2
    return reverb(mix(d, [(0, wood(0.5, 2.0), 1.0), (0, body(0.4, 250, 0.06), 0.6), (0.02, dust(0.4, 1500, 400), 0.2),
                          (0.18, creak(0.5, 90, 120, 600) * env(0.5, [(0, 0), (0.05, 1), (0.5, 0)]), 0.3), (0.45, wood(0.2, 1.4), 0.25)]), 0.8, 0.15, lpf=2000)


@se("Ballista_Load", "バリスタ", MECH, "銛を装填する（巻き上げが「ギリギリ」、歯止めが「カタカタ」送られ、「ガコン」と固定）", "バリスタの装填（R1）")
def _():
    d = 1.4
    return reverb(mix(d, [(0, creak(0.8, 80, 110, 500) * env(0.8, [(0, 0), (0.1, 1), (0.8, 0.5)]), 0.3), (0, ratchet(7, 0.1), 0.7),
                          (0.8, iron(0.4, 1.8), 0.9), (0.8, wood(0.4, 1.6), 0.6)]), 0.8, 0.15, lpf=2000)


@se("Ballista_Fire", "バリスタ", BIG, "銛を撃ち出す（太い弦がはじけ、木の腕が「バン」と止まり、銛がうなって飛ぶ）", "バリスタの射出（○）")
def _():
    d = 1.6
    string = karplus(55, 0.8, 0.994, 0.3) * expdec(0.8, 0.25)
    return reverb(mix(d, [(0, wood(0.5, 1.8), 1.0), (0, lp(norm(string), 700), 0.5), (0, iron(0.2, 1.5), 0.4),
                          (0.02, whoosh(1.2, [(0, 700), (0.1, 1200), (1.2, 250)], 0.08, 0.25, 2.5, q=0.8, body=1.2), 0.6)]), 1.1, 0.18, lpf=2000)


@se("Harpoon_Hit", "バリスタ", BIG, "銛が刺さる（分厚い皮を「ズブッ」と破り、深く食い込む）", "銛が空鯨に刺さったとき")
def _():
    d = 1.3
    tear = burst(0.2, 300, 2500, 0.03, -2) * (0.6 + 0.4 * slow_noise(0.2, 60))
    return reverb(mix(d, [(0, tear, 0.8), (0.01, body(0.8, 200, 0.12, color=-5), 1.0), (0.03, gurgle(0.4, 150, 400, 25) * env(0.4, [(0, 0), (0.05, 1), (0.4, 0)]), 0.4),
                          (0, wood(0.3, 1.6), 0.3)]), 1.2, 0.18, lpf=1600)


@se("Ballista_Break", "バリスタ", BIG, "バリスタが壊れる（木の台が「バキバキッ」と裂け、腕や部品が転がる）", "尾の薙ぎ払いでバリスタが壊れる")
def _():
    d = 2.0
    parts = [(0, wood(0.4, 1.8), 1.0), (0, burst(0.3, 300, 2500, 0.04, -2), 0.7), (0.01, grains(1.2, 60, dur=(0.01, 0.05), freq=(250, 1800)), 0.5)]
    for i, (at, sz) in enumerate([(0.3, 1.3), (0.5, 1.1), (0.7, 0.9), (0.85, 0.8)]):
        parts.append((at, wood(0.25, sz), 0.45 * (0.8 ** i)))
    parts.append((0.4, iron(0.2, 1.2), 0.3))
    return reverb(mix(d, parts), 1.0, 0.18, lpf=2200)


# ---------------- 環境のループ ----------------

@se("Water_Stream_Loop", "環境", LOOP, "水路の流れ（さらさら流れ、ときどきしずくが落ちる、ループ用）", "王都の地下水路・虹の水路・井戸・川", loop=True)
def _():
    def fn(d):
        flow = bp(pink(d), 900, 0.5) * (1 + 0.3 * slow_noise(d, 3))
        return norm(flow) + 0.4 * gurgle(d, 300, 900, 6) + 0.3 * droplets(d, int(d * 10), 800, 2000) + 0.25 * norm(lp(brown(d), 200))
    return make_loop(fn, 4.0, 0.5)


@se("Lava_Loop", "環境", LOOP, "溶岩が煮える（重く「ごぼ…」とうねり、ぱちぱちはぜる、ループ用）", "炎胎の火口・溶岩洞・燃えがら坑道", loop=True)
def _():
    def fn(d):
        bed = norm(lp(brown(d), 150)) * 0.8
        heave = np.zeros(N(d))
        for _ in range(int(d * 2.5)):
            gd = J(0.25, 0.45)
            put(heave, J(0, d - 0.5), gurgle(gd, 80, 220, 12) * env(gd, [(0, 0), (gd * 0.3, 1), (gd, 0)]), J(0.5, 1))
        return bed + norm(heave) * 0.8 + 0.15 * crackle(d, 15, 800, False)
    return make_loop(fn, 4.0, 0.5)


@se("Swamp_Loop", "環境", LOOP, "沼のうねり（どろっとした泥がゆっくり動き、ときどき「ぷつ」とはじける、ループ用）", "毒の湿地・蛍の沼・沈んだ村", loop=True)
def _():
    def fn(d):
        bed = gurgle(d, 150, 350, 3) * 0.5
        pops = np.zeros(N(d))
        for _ in range(int(d * 3)):
            put(pops, J(0, d - 0.1), modal(0.06, [J(250, 450)], [0.008], length=0.004, bright=1200) * J(0.3, 1))
        return bed + pops * 0.7
    return make_loop(fn, 4.0, 0.5)


@se("Wind_Loop", "環境", LOOP, "吹き抜ける風（低くうなる、ループ用）", "山嶺・雲の裏側・高台・平原", loop=True)
def _():
    def fn(d):
        fc = 380 + 200 * slow_noise(d, 0.6)
        return norm(bp(pink(d), np.clip(fc, 150, 900), 0.8) * (1 + 0.45 * slow_noise(d, 1.2))) + 0.4 * norm(lp(brown(d), 150))
    return make_loop(fn, 5.0, 0.8)


@se("Gear_Loop", "環境", LOOP, "大きな歯車の仕掛け（重く回り、木と鉄の歯が「ゴトン、ガタン」と噛み合う、ループ用）", "歯車の仕掛け・天界の工房・時計塔", loop=True)
def _():
    def fn(d):
        hum = norm(lp(brown(d), 120)) * 0.5
        teeth = np.zeros(N(d))
        for i in range(int(d / 0.5) + 1):
            put(teeth, i * 0.5, iron(0.3, 1.8) * 0.6 + wood(0.3, 1.6) * 0.5 if i % 2 else stone(0.3, 1.5) * 0.4 + iron(0.3, 2.0) * 0.5)
            put(teeth, i * 0.5 + 0.25, ratchet(1, 0.1, 0.8), 0.25)
        return hum + teeth * 0.8
    return make_loop(fn, 4.0, 0.5)


@se("Windmill_Loop", "環境", LOOP, "風車が回る（木の軸がゆっくりきしみ、羽根が風を切る、ループ用）", "風車の丘", loop=True)
def _():
    def fn(d):
        out = np.zeros(N(d))
        for i in range(int(d / 2.0) + 1):
            put(out, i * 2.0, creak(1.2, 70, 95, 500) * env(1.2, [(0, 0), (0.3, 1), (1.2, 0)]), 1.0)
            put(out, i * 2.0 + 1.0, cloth(0.8, 0.4, 0.15, 250, 600), 0.6)   # 羽根が風を切る
        wind = norm(bp(pink(d), 400, 0.7)) * 0.4
        return out * 0.5 + wind
    return make_loop(fn, 4.0, 0.5)


@se("Elevator_Loop", "環境", LOOP, "昇降機が動く（綱がきしんで巻かれ、滑車がカタカタ回る、ループ用）", "昇降機・跳ね橋を上げ下げしている間", loop=True)
def _():
    def fn(d):
        rope = creak(d, 90, 100, 450) * 0.25
        rum = norm(lp(brown(d), 150)) * 0.5
        clack = np.zeros(N(d))
        for i in range(int(d / 0.35) + 1):
            put(clack, i * 0.35, wood(0.15, 0.9) * 0.5 + iron(0.15, 0.8) * 0.3, J(0.5, 0.8))
        return rum + rope + clack * 0.5
    return make_loop(fn, 2.8, 0.35)


@se("Elevator_Stop", "環境", MECH, "昇降機が止まる（止め金が「ガチン」と掛かり、床板が「ゴトン」と沈んで、綱がきしみながら揺れが収まる）", "昇降機・跳ね橋が止まったとき")
def _():
    d = 1.6
    sway = np.zeros(N(1.2))
    for i in range(3):
        put(sway, 0.2 + 0.32 * i, creak(0.3, 85, 100, 500) * env(0.3, [(0, 0), (0.1, 1), (0.3, 0)]), 0.3 * (0.6 ** i))
        put(sway, 0.35 + 0.32 * i, wood(0.15, 1.1), 0.25 * (0.6 ** i))
    return reverb(mix(d, [(0, iron(0.3, 1.6), 0.9), (0.04, wood(0.5, 2.0), 1.0), (0.04, body(0.3, 250, 0.04), 0.4), (0.1, sway, 1.0)]), 0.8, 0.15, lpf=1800)


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
