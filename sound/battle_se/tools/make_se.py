# -*- coding: utf-8 -*-
"""
バトルの攻撃系 SE をすべて合成して out/ に書き出す。
  python make_se.py            … 全部作る
  python make_se.py Fina_Hit_A … 名前を指定して作る（部分一致）
必要なもの：Python 3 ＋ numpy ＋ scipy
"""
import os
import sys
import json
import numpy as np
from dsp import *  # noqa: F401,F403
import dsp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "Resources", "BattleSE")   # Unity の Resources から名前で読めるように

SE = []  # (名前, 群, 目標音量dB, 説明, 使う所, ループか, 関数)

# 目標音量（50ms ごとの一番大きい所の RMS）
SWING, LIGHT, HIT, HEAVY, BIG = -17, -13, -10, -8.5, -7.5
SHOT, WARN, LOOP = -12, -15, -14


def se(name, group, level, desc, use, loop=False):
    def reg(fn):
        SE.append(dict(name=name, group=group, level=level, desc=desc, use=use, loop=loop, fn=fn))
        return fn
    return reg


# =====================================================================
# フィナ（剣）
# =====================================================================

def blade_swing(d, f_lo, f_hi, peak, width, ring=0.0, ring_f=5200):
    # 金属の刃鳴りは入れない（ring は互換のために残すが使わない）。低い胴鳴りで重さを出す
    w = whoosh(d, [(0, f_lo), (peak, f_hi), (d, f_lo * 0.8)], peak, width, skew=1.6, q=1.3, body=0.5)
    low = lp(brown(d), 350) * bell_env(d, peak, width * 1.2, 1.6)
    return w + 0.45 * norm(low)


@se("Fina_Swing_A", "フィナ（剣）", SWING, "短剣の素早いひと振り（空振りでも鳴らす）", "通常攻撃1段目（振り始め 0.1秒前後）")
def _():
    return blade_swing(0.32, 900, 4200, 0.12, 0.045, ring=0.12)


@se("Fina_Swing_B", "フィナ（剣）", SWING, "切り返しのひと振り（1段目より少し低く長い）", "通常攻撃2段目")
def _():
    return blade_swing(0.36, 750, 3600, 0.14, 0.055, ring=0.1, ring_f=4600)


@se("Fina_Swing_C", "フィナ（剣）", SWING + 2, "締めの大振り（重く、刃鳴りが残る）", "通常攻撃3段目（命中 0.65秒の少し前）")
def _():
    d = 0.6
    w = blade_swing(d, 500, 3000, 0.22, 0.08, ring=0.2, ring_f=3900)
    return w + 0.35 * norm(lp(pink(d), 400)) * bell_env(d, 0.22, 0.07, 1.4)


def slash_hit(d, weight):
    cut = burst(d, 1800, 9000, 0.03 + 0.03 * weight, color=0)
    body = thump(d, 160 - 40 * weight, 60, 0.05 + 0.06 * weight, drv=2)
    flesh = burst(d, 300, 2500, 0.05 + 0.05 * weight, color=-3)
    x = mix(d, [(0, click(0.004, 2000), 0.5), (0, cut, 0.6), (0.002, body, 1.0 + 0.5 * weight),
                (0.002, flesh, 0.8), (0.002, thump(d, 80, 40, 0.06 + 0.08 * weight, 2), 0.5)])
    return reverb(x, 0.4 + 0.4 * weight, 0.12)


@se("Fina_Hit_A", "フィナ（剣）", HIT, "斬撃が当たった「ザシュッ」（軽め）", "通常攻撃1・2段目の命中／時間停止中の高速連撃の命中")
def _():
    return slash_hit(0.35, 0.0)


@se("Fina_Hit_C", "フィナ（剣）", HEAVY, "締めの斬撃が当たった重い「ズバッ」", "通常攻撃3段目の命中")
def _():
    return slash_hit(0.55, 1.0)


@se("Fina_Spin", "フィナ（剣）", SWING + 3, "回転斬り（3回転ぶんの風切り、約0.5秒）", "回転斬りの出だし")
def _():
    d = 0.75
    parts = []
    for i in range(3):
        parts.append((i * 0.17, blade_swing(0.3, 700 + 150 * i, 3800 + 300 * i, 0.09, 0.04, ring=0.1), 0.8 + 0.1 * i))
    x = mix(d, parts)
    return x + 0.25 * norm(bp(white(len(x) / SR), curve(len(x) / SR, [(0, 600), (0.5, 1400), (len(x) / SR, 500)], "exp"), 0.8)) * env(len(x) / SR, [(0, 0), (0.1, 1), (0.5, 1), (len(x) / SR, 0)])


@se("Fina_Spin_Hit", "フィナ（剣）", HIT - 2, "回転斬りの1ヒット（連続で鳴らしても耳障りでないよう短く）", "回転斬りの命中ごと")
def _():
    d = 0.22
    return mix(d, [(0, burst(d, 2000, 9000, 0.025, 0), 0.8), (0, thump(d, 140, 60, 0.05, 2), 1.0), (0, burst(d, 200, 1500, 0.04, -4), 0.6)])


@se("Fina_JumpSlash", "フィナ（剣）", SWING + 3, "跳び上がって振り下ろす（踏み切り→落下の風切り→着地）", "ジャンプ斬り（0秒から鳴らす。命中は0.28秒）")
def _():
    d = 0.8
    kick = burst(0.12, 150, 1200, 0.03, -3) + 0.5 * thump(0.12, 120, 60, 0.03)
    up = whoosh(0.3, [(0, 400), (0.15, 1400), (0.3, 700)], 0.1, 0.06, q=1.0, body=0.6)
    down = blade_swing(0.4, 600, 3500, 0.2, 0.05, ring=0.18, ring_f=4200)
    land = thump(0.3, 110, 45, 0.06) + 0.6 * burst(0.3, 100, 1500, 0.06, -6)
    return mix(d, [(0, kick, 0.6), (0.02, up, 0.5), (0.06, down, 1.0), (0.3, land, 0.7)])


@se("Fina_JumpSlash_Hit", "フィナ（剣）", BIG, "ジャンプ斬りの命中（地面ごと叩き斬る重い一撃）", "ジャンプ斬りの命中（0.28秒）")
def _():
    d = 0.9
    x = mix(d, [(0, slash_hit(0.5, 1.0), 1.0), (0, thump(0.6, 90, 35, 0.15, 2.5), 0.9),
                (0.01, grains(0.6, 40, freq=(300, 3000)), 0.3)])
    return reverb(x, 0.9, 0.15)


@se("Fina_Rush_Swing", "フィナ（剣）", SWING, "時間停止中の高速連撃（鋭く短い剣閃）", "時間停止中の□（A・B の振りごと）")
def _():
    d = 0.25
    return blade_swing(d, 1100, 5000, 0.07, 0.025)


@se("Fina_Warp", "フィナ（剣）", LIGHT, "時間停止中のワープ（低くうなって吸い込まれ、目の前にドンと現れる）", "時間停止中、最初の□のワープ")
def _():
    d = 0.45
    f = curve(d, [(0, 60), (0.28, 200), (d, 200)], "exp")
    hum = lp(osc(f, d, "saw") + osc(f * 1.01, d, "saw"), 600) * env(d, [(0, 0), (0.05, 0.4), (0.28, 1), (0.3, 0), (d, 0)])
    air = whoosh(d, [(0, 400), (0.28, 3000), (d, 1200)], 0.26, 0.06, skew=0.6)
    pop = mix(d, [(0.29, burst(0.12, 200, 3000, 0.025, -3), 1.0), (0.29, thump(0.2, 160, 50, 0.05, 2), 0.9)])
    x = mix(d, [(0, norm(hum), 0.5), (0, air, 0.7), (0, pop, 1.0)])
    return reverb(x, 0.5, 0.2)


@se("JustDodge_TimeStop", "フィナ（剣）", HEAVY, "ジャスト回避→時間停止（空気を吸い込み、太い「ブゥン」が沈みながら世界が止まる）", "ジャスト回避の成功")
def _():
    d = 2.2
    # 空気を吸い込む → 「ブゥン」と太い音が沈みながら伸びる（テープが止まるように）
    swell = rev(norm(lp(white(0.45), 1500)) * expdec(0.45, 0.15))
    f = curve(d, [(0, 150), (0.45, 150), (1.4, 38), (d, 32)], "exp")
    wob = 1 + 0.12 * np.sin(phase_of(curve(d, [(0, 9), (d, 3)]), d))   # 「ブゥン」のうなり
    tone = osc(f, d, "saw") + osc(f * 1.007, d, "saw") + 0.8 * osc(f * 0.5, d, "sine")
    tone = lp(tone, curve(d, [(0, 900), (0.45, 900), (1.6, 180), (d, 120)], "exp"), stages=2)
    dive = tone * wob * env(d, [(0, 0), (0.42, 0), (0.47, 1), (1.3, 0.7), (d, 0)])
    boom = thump(1.4, 70, 28, 0.4, 2.5)
    air = whoosh(1.2, [(0, 700), (0.1, 900), (1.2, 150)], 0.05, 0.25, skew=2.5, q=0.6, body=1.0)
    x = mix(d, [(0, swell, 0.6), (0, norm(dive), 0.9), (0.45, boom, 1.0), (0.45, air, 0.5)])
    return reverb(x, 1.6, 0.3, lpf=1800)


@se("TimeStop_End", "フィナ（剣）", LIGHT, "時間停止が解ける（止まった空気がゆっくり流れ出す、柔らかい「フゥゥン」）", "時間停止の終わり（5秒）")
def _():
    d = 1.2
    d = 1.6
    # 止まっていた空気がゆっくり流れ出す「フゥゥン」：柔らかい風がふくらんで抜け、低いうなりが持ち上がって消える
    air = whoosh(d, [(0, 250), (0.55, 1100), (d, 400)], 0.55, 0.22, skew=1.6, q=0.5, body=1.2)
    f = curve(d, [(0, 40), (0.6, 110), (d, 95)], "exp")
    hum = lp(osc(f, d, "saw") + osc(f * 1.006, d, "saw"), 500) * env(d, [(0, 0), (0.5, 1), (1.3, 0.3), (d, 0)])
    return reverb(mix(d, [(0, air, 1.0), (0, norm(hum), 0.45)]), 1.2, 0.25, lpf=2000)


# =====================================================================
# アスカ（格闘）
# =====================================================================

def punch_hit(d, weight):
    slap = burst(d, 600, 5000, 0.015 + 0.01 * weight, color=-1)
    body = thump(d, 130 - 30 * weight, 45, 0.06 + 0.06 * weight, drv=2.5)
    mid = burst(d, 150, 1200, 0.04 + 0.04 * weight, color=-4)
    x = mix(d, [(0, click(0.003, 1500), 0.6), (0, slap, 0.7), (0, body, 1.0), (0.001, mid, 0.7)])
    return reverb(x, 0.35 + 0.3 * weight, 0.1)


@se("Asuka_Jab", "アスカ（格闘）", SWING, "拳が空を切る「シュッ」（短く低め）", "ジャブ（振りごと）")
def _():
    return whoosh(0.22, [(0, 500), (0.08, 2200), (0.22, 700)], 0.08, 0.03, skew=1.4, q=1.0, body=0.6)


@se("Asuka_Jab_Hit", "アスカ（格闘）", HIT, "拳が当たった「バシッ」", "ジャブの命中（0.27秒）")
def _():
    return punch_hit(0.3, 0.0)


@se("Asuka_Kick", "アスカ（格闘）", SWING + 1, "ハイキックの風切り（大きく重め）", "キック（振り）")
def _():
    return whoosh(0.35, [(0, 350), (0.14, 1600), (0.35, 500)], 0.14, 0.05, skew=1.5, q=0.9, body=0.8)


@se("Asuka_Kick_Hit", "アスカ（格闘）", HEAVY, "蹴りが当たった重い「ドカッ」", "キックの命中（0.38秒）")
def _():
    return punch_hit(0.45, 1.0)


@se("Asuka_Mach_Charge", "アスカ（格闘）", LIGHT, "マッハ突進の溜め（踏みしめて力を込める、0.25秒）", "スキル1：マッハ突進の出だし")
def _():
    d = 0.3
    f = curve(d, [(0, 80), (0.24, 220), (d, 220)], "exp")
    hum = drive(osc(f, d, "saw"), 2) * env(d, [(0, 0), (0.2, 1), (0.25, 0.3), (d, 0)])
    return mix(d, [(0, lp(hum, 1200), 0.6), (0, burst(0.15, 80, 900, 0.04, -5), 0.8), (0.05, whoosh(0.25, [(0, 300), (0.24, 2500)], 0.22, 0.05, skew=0.3), 0.6)])


@se("Asuka_Mach_Dash", "アスカ（格闘）", SHOT, "マッハ突進（ジェットのように空気を裂いて走る）", "マッハ突進の突進中（溜めの後）")
def _():
    d = 0.9
    roar = lp(brown(d), curve(d, [(0, 400), (0.1, 3000), (d, 900)], "exp")) * env(d, [(0, 0), (0.04, 1), (0.6, 0.8), (d, 0)])
    hiss = bp(white(d), curve(d, [(0, 2000), (0.1, 6000), (d, 2500)], "exp"), 1.0) * env(d, [(0, 0), (0.05, 1), (d, 0)])
    boom = thump(0.3, 90, 40, 0.06)
    return mix(d, [(0, norm(roar), 0.8), (0, norm(hiss), 0.35), (0, boom, 0.6)])


def explosion(d, size=1.0, bright=3500):
    fc = curve(d, [(0, bright), (0.05, bright), (d, 120)], "exp")
    body = lp(brown(d), fc, stages=2) * expdec(d, 0.18 * size + 0.1, attack=0.003)
    sub = thump(d, 70, 28, 0.2 * size + 0.1, drv=2)
    x = mix(d, [(0, norm(body), 1.0), (0, sub, 0.9), (0, crackle(d * 0.7, 250, 1200) * expdec(d * 0.7, 0.2), 0.25),
                (0, click(0.005, 800), 0.5)])
    return reverb(drive(x, 1.6), 1.0 * size + 0.4, 0.2, lpf=2500)


@se("Asuka_Mach_Blast", "アスカ（格闘）", BIG, "突進の着弾と爆風（拳の衝撃がはじけ飛ぶ）", "マッハ突進の命中（直撃＋爆風）")
def _():
    d = 1.2
    return mix(d, [(0, punch_hit(0.3, 1.0), 0.7), (0.01, explosion(1.0, 0.8, 3000), 1.0)])


@se("Asuka_GroundSplit", "アスカ（格闘）", BIG, "地面割り（拳を叩きつけ、地面が割れて岩が跳ねる）", "スキル2：地面割り（命中0.62秒）")
def _():
    d = 1.6
    impact = thump(1.0, 100, 30, 0.3, 3)
    crack = mix(0.5, [(0.002 + 0.03 * i + RNG.uniform(0, 0.01), click(0.006, 1200), RNG.uniform(0.4, 1)) for i in range(10)])
    crack = bp(crack, 2200, 0.8)
    rumble = lp(brown(d), 250) * env(d, [(0, 0), (0.02, 1), (0.5, 0.6), (d, 0)])
    debris = grains(1.2, 80, dur=(0.006, 0.04), freq=(400, 4000))
    x = mix(d, [(0, punch_hit(0.3, 1.0), 0.6), (0, impact, 1.0), (0, crack, 0.6), (0, norm(rumble), 0.6), (0.05, debris, 0.35)])
    return reverb(x, 1.3, 0.2, lpf=3000)


# =====================================================================
# 合体攻撃「踏み台」
# =====================================================================

@se("Combo_Launch", "合体攻撃", SHOT, "踏み台：アスカの手を蹴って高く跳ぶ（受け止め→打ち上げ→上昇の風）", "合体攻撃の跳び上がり")
def _():
    d = 1.0
    catch = punch_hit(0.2, 0.3)
    up = whoosh(0.9, [(0, 300), (0.35, 2200), (0.9, 900)], 0.3, 0.12, skew=2, q=0.8, body=0.7)
    return mix(d, [(0, catch, 0.7), (0.05, thump(0.2, 180, 80, 0.04), 0.5), (0.08, up, 0.8)])


@se("Combo_Stab", "合体攻撃", BIG, "突き刺し（落下の勢いで剣を深く突き立てる）", "合体攻撃の突き刺し（1.70秒）")
def _():
    d = 0.9
    fall = whoosh(0.45, [(0, 800), (0.4, 4500)], 0.38, 0.1, skew=0.4, q=1.4, body=0.4)
    pierce = mix(0.6, [(0, burst(0.6, 1500, 9000, 0.04, 0), 0.8), (0, burst(0.6, 100, 1500, 0.12, -4), 0.9),
                       (0, thump(0.6, 120, 40, 0.15, 3), 1.0), (0, thump(0.6, 60, 30, 0.2, 2), 0.6)])
    return reverb(mix(d, [(0, fall, 0.5), (0.4, pierce, 1.0)]), 0.9, 0.15)


@se("Combo_Shockwave", "合体攻撃", BIG, "衝撃波（地面から大きく広がる爆風と地鳴り）", "合体攻撃の衝撃波（1.75秒）")
def _():
    d = 2.0
    wave = whoosh(1.5, [(0, 1500), (0.1, 3000), (1.5, 200)], 0.08, 0.25, skew=3, q=0.6, body=1.2)
    return mix(d, [(0, explosion(1.8, 1.4, 4000), 1.0), (0, wave, 0.6), (0.02, grains(1.4, 60, freq=(300, 3000)), 0.25)])


# =====================================================================
# 被弾・撃破
# =====================================================================

@se("Hit_Player", "被弾・撃破", HIT, "フィナが攻撃を受けた（鈍い衝撃と、少しざらつく音）", "フィナの被弾（ダメージ12前後）")
def _():
    d = 0.4
    x = mix(d, [(0, thump(d, 200, 70, 0.07, 3), 1.0), (0, burst(d, 400, 3500, 0.05, -2), 0.7),
                (0, drive(bp(white(0.12), 900, 2), 3) * expdec(0.12, 0.03), 0.3)])
    return reverb(x, 0.4, 0.1)


@se("Hit_Player_Heavy", "被弾・撃破", HEAVY, "フィナが大きな攻撃を受けた（はじき飛ばされる重い衝撃）", "肩からの突進（30）、尾の薙ぎ払いなど")
def _():
    d = 0.8
    x = mix(d, [(0, thump(d, 160, 40, 0.14, 3.5), 1.0), (0, burst(d, 300, 4000, 0.09, -2), 0.8),
                (0.03, whoosh(0.45, [(0, 1500), (0.45, 400)], 0.05, 0.12, 2.5, body=0.5), 0.4)])
    return reverb(x, 0.7, 0.15)


@se("Enemy_Down", "被弾・撃破", HIT, "敵を倒した（とどめの手応えと、ふっと消える余韻）", "敵のHPが0になったとき")
def _():
    d = 1.0
    x = mix(d, [(0, slash_hit(0.35, 0.6), 0.8), (0.05, thump(0.4, 90, 40, 0.12), 0.6),
                (0.08, norm(bp(white(0.6), curve(0.6, [(0, 1500), (0.6, 400)], "exp"), 1.2)) * expdec(0.6, 0.2), 0.3)])
    return reverb(x, 0.9, 0.2)


# =====================================================================
# 敵の攻撃
# =====================================================================

@se("Enemy_Telegraph", "敵の攻撃", WARN, "攻撃の予告（赤い輪郭と同時に鳴る、低く短い「ヴォン」）", "敵の攻撃の0.3秒前（無音の影 EN-38 だけは鳴らさない）")
def _():
    d = 0.5
    f = curve(d, [(0, 90), (0.08, 140), (d, 120)], "exp")
    tone = lp(osc(f, d, "saw") + osc(f * 1.5, d, "saw") * 0.6 + osc(f * 0.5, d, "sine"), 1100)
    tone = tone * env(d, [(0, 0), (0.03, 1), (0.12, 0.8), (0.35, 0), (d, 0)])
    return reverb(mix(d, [(0, norm(tone), 0.9), (0, whoosh(0.3, [(0, 500), (0.08, 1500), (0.3, 400)], 0.07, 0.04), 0.4)]), 0.5, 0.15, lpf=2000)


@se("Enemy_Lunge", "敵の攻撃", SWING, "飛びかかり（体ごとぶつかってくる低い風切り）", "キノコ・ビー・植物のランジ、跳びかかり全般")
def _():
    return whoosh(0.35, [(0, 250), (0.12, 1100), (0.35, 350)], 0.12, 0.05, skew=1.5, q=0.8, body=1.0)


@se("Enemy_Bite", "敵の攻撃", HIT, "噛みつき（歯が噛み合う「ガチッ」と湿った音）", "沼の魔物・幼虫・骨の小竜・箱入りの忘れ物など")
def _():
    d = 0.35
    clack = mix(d, [(0, bp(click(0.01, 500), 1800, 3), 1.0), (0.05, bp(click(0.01, 500), 1500, 3), 0.8)])
    wet = lp(pink(0.25), 1500) * expdec(0.25, 0.06) * (1 + 0.6 * np.sin(phase_of(35, 0.25)))
    return mix(d, [(0, clack * 3, 1.0), (0.04, norm(wet), 0.5), (0.04, thump(0.2, 150, 70, 0.04), 0.5)])


@se("Enemy_Claw", "敵の攻撃", HIT - 1, "爪でひっかく（3本の爪が走る「ザザッ」）", "翼の悪魔（小）の急降下の爪など")
def _():
    d = 0.35
    parts = []
    for i in range(3):
        s = bp(white(0.06), 1600 - 250 * i, 0.8) * env(0.06, [(0, 0), (0.004, 1), (0.06, 0)]) * (1 + 0.5 * np.sin(phase_of(180 + 40 * i, 0.06)))
        parts.append((0.055 * i, norm(s), 0.8 - 0.1 * i))
    parts.append((0, whoosh(0.2, [(0, 800), (0.06, 3000), (0.2, 900)], 0.06, 0.03), 0.4))
    parts.append((0.02, thump(0.15, 180, 80, 0.03), 0.3))
    return mix(d, parts)


@se("Enemy_Sting", "敵の攻撃", HIT - 1, "蜂の針（羽音の高まり→鋭く刺す「プスッ」）", "装甲バチ・毒羽のバチ・酔いバチ・受粉の蜂")
def _():
    d = 0.45
    f = curve(0.3, [(0, 180), (0.3, 260)], "exp")
    buzz = lp(osc(f, 0.3, "saw") * (1 + 0.3 * np.sin(phase_of(30, 0.3))), 2500) * env(0.3, [(0, 0), (0.25, 1), (0.3, 0.2)])
    prick = mix(0.2, [(0, click(0.004, 3000), 1.0), (0, burst(0.2, 1500, 7000, 0.02, 0), 0.7), (0, thump(0.2, 220, 110, 0.03), 0.4)])
    return mix(d, [(0, buzz, 0.35), (0.25, prick, 1.0)])


@se("Enemy_Punch", "敵の攻撃", HIT, "人型の敵のパンチ・キックの命中（フィナより低くこもった音）", "魔族・ベリット・狼の獣人・亡者のパンチ／キック")
def _():
    return lp(punch_hit(0.4, 0.6), 3500)


@se("Enemy_Tackle", "敵の攻撃", HEAVY, "体当たりの衝突（重い「ドスッ」）", "大蛍・炎の魔物・清掃機・歯車の子などの体当たり")
def _():
    d = 0.5
    return reverb(mix(d, [(0, thump(d, 120, 45, 0.1, 3), 1.0), (0, burst(d, 150, 2000, 0.07, -4), 0.8), (0, click(0.004, 1000), 0.4)]), 0.5, 0.12)


@se("Enemy_Stomp", "敵の攻撃", BIG, "踏みつけ（地面が揺れて砂ぼこりが舞う）", "輪の茸番の踏みつけ（半径1.6m）")
def _():
    d = 1.0
    dust = lp(white(0.8), curve(0.8, [(0, 3000), (0.8, 600)], "exp")) * env(0.8, [(0, 0), (0.02, 1), (0.8, 0)])
    x = mix(d, [(0, thump(d, 90, 30, 0.2, 3), 1.0), (0, burst(0.4, 80, 900, 0.08, -6), 0.7), (0.01, norm(dust), 0.25), (0.03, grains(0.6, 30, freq=(300, 2500)), 0.2)])
    return reverb(x, 0.9, 0.15, lpf=2500)


@se("Enemy_HeavySmash", "敵の攻撃", BIG, "大振りの振り下ろし（重い風切り→石や鉄が叩きつけられる）", "石くれ人形・動く鎧の大振り（予備動作0.8秒の後）")
def _():
    d = 1.3
    swing = whoosh(0.5, [(0, 200), (0.35, 900), (0.5, 250)], 0.35, 0.1, skew=0.7, q=0.7, body=1.2)
    hit = mix(0.9, [(0, thump(0.9, 80, 28, 0.22, 3.5), 1.0), (0, burst(0.5, 200, 4000, 0.06, -2), 0.8),
                    (0, thump(0.9, 55, 25, 0.3, 2), 0.7), (0.01, grains(0.6, 40, freq=(400, 4000)), 0.3)])
    return reverb(mix(d, [(0, swing, 0.5), (0.4, hit, 1.0)]), 1.0, 0.18, lpf=3000)


@se("Enemy_SwordSlash", "敵の攻撃", HIT, "敵の剣の斬撃（長剣の重い風切りと「ズバッ」）", "聖堂騎士の剣の2連撃（1撃ごと）")
def _():
    d = 0.6
    sw = blade_swing(0.4, 450, 2400, 0.15, 0.06)
    return mix(d, [(0, sw, 0.8), (0.15, slash_hit(0.4, 0.7), 0.8)])


@se("Enemy_Whip", "敵の攻撃", HIT, "鞭の横なぎ（しなる風切り→鋭い「パァン」）", "監督の魔物の鞭（前方120°）")
def _():
    d = 0.6
    swish = whoosh(0.35, [(0, 400), (0.28, 5000)], 0.26, 0.08, skew=0.3, q=1.2, body=0.3)
    crack = mix(0.3, [(0, click(0.003, 2000), 1.0), (0, burst(0.3, 1500, 12000, 0.012, 1), 1.0), (0.002, thump(0.1, 600, 200, 0.01), 0.3)])
    return reverb(mix(d, [(0, swish, 0.5), (0.28, crack, 1.0)]), 0.8, 0.2)


@se("Enemy_Baton", "敵の攻撃", HIT, "警棒で打つ（短い風切り→木のような「ゴッ」）", "天の番兵の警棒")
def _():
    d = 0.4
    sw = whoosh(0.2, [(0, 500), (0.12, 2000)], 0.1, 0.04)
    knock = mix(0.3, [(0, partials(0.3, [230, 610, 1020], [0.05, 0.03, 0.02]), 1.0), (0, thump(0.3, 180, 90, 0.04), 0.8), (0, burst(0.3, 500, 3000, 0.02), 0.5)])
    return mix(d, [(0, sw, 0.4), (0.12, knock, 1.0)])


@se("Enemy_Scissors", "敵の攻撃", HIT, "大きな鋏がはさみ込む（刃がすれ合い「ガシュッ」と重く閉じる）", "刈り込み鋏のはさみ込み（正面2連、1回ごと）")
def _():
    d = 0.5
    scrape = bp(white(0.18), 1500, 0.8) * env(0.18, [(0, 0), (0.1, 0.6), (0.18, 1)]) * (1 + 0.4 * np.sin(phase_of(60, 0.18)))
    snap = mix(0.4, [(0, burst(0.3, 600, 4000, 0.025, -2), 1.0), (0, thump(0.3, 200, 70, 0.05, 2.5), 1.0), (0, burst(0.3, 150, 900, 0.05, -4), 0.6)])
    return mix(d, [(0, norm(scrape), 0.4), (0.17, snap, 1.0)])


@se("Enemy_Chain", "敵の攻撃", HIT - 1, "太い鎖を伸ばして打つ（鈍い「ゴロゴロ」→ 重く「ドガッ」）", "鎖の魂の鎖")
def _():
    d = 0.8
    # 太い鉄の鎖：輪がぶつかり合う鈍い「ゴロゴロ」→ 重く打ちつける「ドガッ」（金属の響きは入れない）
    rattle = grains(0.45, 26, dur=(0.015, 0.05), freq=(250, 1100), density="flat", amp=(0.4, 1.0))
    rattle = rattle * env(0.45, [(0, 0.3), (0.35, 1), (0.45, 1)])
    hit = mix(0.7, [(0, thump(0.7, 110, 35, 0.14, 3.5), 1.0), (0, burst(0.4, 250, 2500, 0.05, -3), 0.8),
                    (0.005, grains(0.4, 18, dur=(0.015, 0.05), freq=(250, 1000)), 0.6)])
    return reverb(mix(d, [(0, rattle, 0.6), (0, whoosh(0.4, [(0, 300), (0.35, 1200)], 0.33, 0.08, 0.4, body=1.0), 0.4), (0.38, hit, 1.0)]), 0.8, 0.15, lpf=2500)


@se("Enemy_Grab", "敵の攻撃", HIT - 2, "掴みかかる（ぐっと掴まれる衣ずれと締め付け）", "溺れた村人・仕分けの手・笑う死者の掴み")
def _():
    d = 0.6
    rustle = bp(white(0.3), 1800, 0.8) * env(0.3, [(0, 0), (0.05, 1), (0.3, 0)]) * (1 + 0.5 * np.sin(phase_of(25, 0.3)))
    squeeze = lp(pink(0.4), 700) * env(0.4, [(0, 0), (0.05, 1), (0.4, 0)])
    return mix(d, [(0, norm(rustle), 0.5), (0.05, thump(0.3, 140, 70, 0.05), 0.8), (0.08, norm(squeeze), 0.5)])


@se("Enemy_Throw", "敵の攻撃", HIT - 1, "放り投げる（機械の腕がうなって振り抜く）", "仕分けの手が後ろの区画へ放り投げる")
def _():
    d = 0.9
    f = curve(0.5, [(0, 120), (0.4, 380), (0.5, 380)], "exp")
    motor = lp(osc(f, 0.5, "square") * 0.5 + osc(f * 2.02, 0.5, "saw") * 0.3, 1500) * env(0.5, [(0, 0), (0.1, 0.6), (0.4, 1), (0.5, 0)])
    fling = whoosh(0.6, [(0, 300), (0.15, 1800), (0.6, 400)], 0.15, 0.08, skew=2.5, q=0.8, body=0.9)
    return mix(d, [(0, motor, 0.4), (0.05, click(0.01, 500), 0.4), (0.3, fling, 0.8)])


@se("Enemy_Roll_Loop", "敵の攻撃", LOOP, "岩が転がってくる（ごろごろ、ループ用）", "岩の魔物・岩ダンゴ・冷えた溶岩の殻・樽の子の転がり", loop=True)
def _():
    def fn(d):
        rumble = lp(brown(d), 180) * (1 + 0.4 * np.sin(phase_of(3.2, d)))
        knocks = grains(d, int(d * 22), dur=(0.01, 0.04), freq=(120, 600), density="flat", amp=(0.3, 1.0))
        grit = grains(d, int(d * 60), dur=(0.003, 0.01), freq=(1500, 5000), density="flat", amp=(0.1, 0.4))
        return norm(rumble) * 0.8 + norm(knocks) * 0.7 + norm(grit) * 0.2
    return make_loop(fn, 2.0, 0.3)


@se("Enemy_Burst_Lava", "敵の攻撃", BIG, "殻が割れて溶岩が飛び散る（割れる音→ジュッと焼ける）", "冷えた溶岩の殻が割れたとき（半径2m）")
def _():
    d = 1.5
    crack = mix(0.2, [(0.012 * i, click(0.006, 800), RNG.uniform(0.5, 1)) for i in range(8)])
    sizzle = hp(white(1.2), 3000) * env(1.2, [(0, 0), (0.05, 1), (1.2, 0)]) * (0.6 + 0.4 * crackle(1.2, 300, 2000, False))
    x = mix(d, [(0, bp(crack, 1500, 0.7) * 3, 0.8), (0.05, explosion(1.0, 0.6, 2500), 0.9), (0.08, norm(sizzle), 0.3), (0.08, grains(0.8, 30, freq=(200, 1500)), 0.3)])
    return x


@se("Enemy_Vine_Erupt", "敵の攻撃", BIG, "地面を割って蔦が突き上がる（地鳴り→土が割れる→木がきしむ）", "侵食の蔦の突き上げ（花が咲いてから1秒）")
def _():
    d = 1.2
    rumble = lp(brown(0.4), 150) * env(0.4, [(0, 0), (0.35, 1), (0.4, 1)])
    burst_ = mix(0.8, [(0, thump(0.8, 110, 40, 0.15, 3), 1.0), (0, grains(0.7, 60, freq=(250, 3000)), 0.5), (0, burst(0.5, 150, 2500, 0.08, -3), 0.7)])
    f = curve(0.6, [(0, 180), (0.6, 120)])
    creak = bp(osc(f, 0.6, "saw") * (1 + 0.8 * np.sin(phase_of(12, 0.6))), 700, 2) * env(0.6, [(0, 0), (0.05, 1), (0.6, 0)])
    return reverb(mix(d, [(0, norm(rumble), 0.5), (0.35, burst_, 1.0), (0.45, norm(creak), 0.25)]), 0.8, 0.15, lpf=3000)


# ---------------- 飛び道具 ----------------

@se("Arrow_Shoot", "敵の攻撃", SHOT, "弓を射る（弦の「ビン」と矢が飛ぶ風切り）", "狼の獣人（弓）の矢（2秒に1本）")
def _():
    d = 0.6
    string = karplus(98, 0.45, 0.992, 0.7) * expdec(0.45, 0.15)
    fly = whoosh(0.5, [(0, 2500), (0.1, 4000), (0.5, 1500)], 0.08, 0.1, skew=2.5, q=2, body=0.1)
    return mix(d, [(0, click(0.004, 1000), 0.5), (0, norm(string), 1.0), (0.02, fly, 0.4)])


@se("Arrow_Hit", "敵の攻撃", HIT - 1, "矢が刺さる（「トスッ」と軸がふるえる）", "矢・光の矢・本などの命中")
def _():
    d = 0.4
    wobble = partials(0.35, [190, 410], [0.08, 0.05]) * (1 + 0.5 * np.sin(phase_of(28, 0.35)))
    return mix(d, [(0, click(0.004, 1500), 0.8), (0, burst(0.3, 400, 4000, 0.02, -2), 0.8), (0, thump(0.3, 200, 90, 0.03), 0.6), (0.01, wobble, 0.3)])


@se("LightArrow_Shoot", "敵の攻撃", SHOT, "光の矢を放つ（「フォン」と太い光が飛んでいく）", "光の番人の光の矢")
def _():
    d = 0.8
    f = curve(d, [(0, 110), (0.5, 160), (d, 160)], "exp")
    hum = lp(osc(f, d, "saw") + osc(f * 1.5, d, "saw") * 0.7 + osc(f * 2.005, d, "saw") * 0.5, 900) * env(d, [(0, 0), (0.02, 1), (0.6, 0.3), (d, 0)])
    return reverb(mix(d, [(0, norm(hum), 0.6), (0, whoosh(0.6, [(0, 1500), (0.08, 2500), (0.6, 600)], 0.07, 0.12, 2.5, q=1, body=0.6), 0.8),
                          (0, thump(0.3, 150, 70, 0.05), 0.5)]), 0.8, 0.2, lpf=3000)


@se("Book_Throw", "敵の攻撃", SWING + 2, "本が飛んでくる（ページがばたばたはためく）", "書架の魔物の本（3冊・扇形）")
def _():
    d = 0.5
    flap = bp(white(d), 1500, 0.8) * np.clip(np.sin(phase_of(22, d)), 0, 1) ** 2 * env(d, [(0, 0), (0.05, 1), (d, 0)])
    return mix(d, [(0, norm(flap), 0.8), (0, whoosh(d, [(0, 600), (0.2, 1800), (d, 600)], 0.2, 0.1), 0.4)])


@se("Spit_Poison", "敵の攻撃", SHOT, "毒の玉を吐く（ためて「ペッ」と飛ばす、ぬめった音）", "毒吐き草の毒の玉")
def _():
    d = 0.5
    f = curve(0.2, [(0, 300), (0.2, 900)], "exp")
    gurgle = lp(pink(0.2), 900) * (1 + 0.8 * np.sin(phase_of(40, 0.2))) * env(0.2, [(0, 0), (0.18, 1), (0.2, 0)])
    pt = bp(white(0.12), 1200, 1.5) * expdec(0.12, 0.03) + 0.5 * np.sin(phase_of(curve(0.12, [(0, 500), (0.12, 200)], "exp"), 0.12)) * expdec(0.12, 0.03)
    return mix(d, [(0, norm(gurgle), 0.4), (0.18, norm(pt), 1.0), (0.2, bubbles(0.25, 6, 500, 1500), 0.3)])


@se("Poison_Splash", "敵の攻撃", HIT - 1, "毒の玉がはじける（べちゃっと広がり、しゅわしゅわ泡立つ）", "毒の玉の命中・毒の大蛙など")
def _():
    d = 0.8
    splat = mix(0.3, [(0, burst(0.3, 300, 3000, 0.04, -2), 1.0), (0, thump(0.2, 180, 80, 0.03), 0.5)])
    fizz = hp(white(0.7), 4000) * env(0.7, [(0, 0), (0.05, 1), (0.7, 0)]) * (0.5 + 0.5 * crackle(0.7, 600, 3000, False))
    return mix(d, [(0, splat, 1.0), (0.03, bubbles(0.6, 20, 600, 2500), 0.4), (0.05, norm(fizz), 0.15)])


@se("Web_Shoot", "敵の攻撃", SHOT, "糸を吐く（「シュルッ」と伸びて、ぺたっと絡みつく）", "洞の小蜘蛛の糸（当たると1.5秒動けない）")
def _():
    d = 0.5
    zipf = curve(0.25, [(0, 1500), (0.25, 5000)], "exp")
    thwip = bp(white(0.25), zipf, 2) * env(0.25, [(0, 0), (0.02, 1), (0.25, 0)])
    stick = lp(pink(0.2), 1200) * expdec(0.2, 0.04) * (1 + np.sin(phase_of(60, 0.2)))
    return mix(d, [(0, norm(thwip), 0.8), (0.25, norm(stick), 0.6)])


@se("Sleep_Powder", "敵の攻撃", LIGHT, "眠り粉を撒く（「ボフッ」と撒かれて、ふわっと漂う）", "妖精の灯の眠り粉（移動が2秒半分）")
def _():
    d = 1.2
    puff = lp(white(0.4), 1800) * env(0.4, [(0, 0), (0.08, 1), (0.4, 0)])
    drift = lp(white(1.1), curve(1.1, [(0, 1500), (1.1, 400)], "exp")) * env(1.1, [(0, 0), (0.1, 1), (1.1, 0)]) * (1 + 0.4 * np.sin(phase_of(3, 1.1)))
    return reverb(mix(d, [(0, norm(puff), 0.7), (0.05, norm(drift), 0.5), (0, thump(0.3, 120, 60, 0.06, 1.2), 0.3)]), 1.0, 0.3, lpf=2000)


@se("Spore_Burst", "敵の攻撃", HIT - 2, "胞子がはじける（「ボフッ」と舞い散る）", "胞子キノコが倒れて1秒後の胞子（半径1.5m）")
def _():
    d = 0.9
    pop = mix(0.3, [(0, thump(0.3, 150, 60, 0.05, 2), 1.0), (0, burst(0.3, 200, 1500, 0.05, -4), 0.8)])
    drift = lp(white(0.8), curve(0.8, [(0, 2500), (0.8, 700)], "exp")) * env(0.8, [(0, 0), (0.03, 1), (0.8, 0)])
    return mix(d, [(0, pop, 1.0), (0.02, norm(drift), 0.3)])


@se("Steam_Blast", "敵の攻撃", LOOP - 1, "熱い湯気を吹きかける（「シュウゥ」と長く噴き出す、約1.5秒）", "湯煙の精の湯気（3秒で計12）")
def _():
    d = 1.6
    hiss = bp(white(d), curve(d, [(0, 1200), (0.2, 2200), (d, 1500)], "exp"), 0.6) * env(d, [(0, 0), (0.08, 1), (1.3, 0.8), (d, 0)])
    rum = lp(pink(d), 400) * env(d, [(0, 0), (0.1, 1), (d, 0)])
    return mix(d, [(0, norm(hiss), 0.8), (0, norm(rum), 0.6), (0.05, bubbles(0.6, 10, 300, 900), 0.15)])


@se("Water_Splash", "敵の攻撃", HIT - 1, "湯・水が跳ねる（着地の「バシャッ」としぶき）", "湯あたりガエルの着地（半径1.5m）・水路の清掃機")
def _():
    d = 1.0
    body = mix(0.4, [(0, burst(0.4, 250, 4000, 0.08, -2), 1.0), (0, thump(0.3, 120, 60, 0.05), 0.6)])
    drops = bubbles(0.8, 25, 700, 3000)
    spray = hp(white(0.6), 3000) * expdec(0.6, 0.15)
    return mix(d, [(0, body, 1.0), (0.02, drops, 0.4), (0, norm(spray), 0.3)])


# ---------------- 炎 ----------------

def fire_noise(d, bright=2500):
    roar = lp(brown(d), bright) + 0.3 * bp(white(d), bright * 1.3, 0.5)
    roar *= 1 + 0.25 * lp(white(d), 8)  # ゆらぎ
    return norm(roar) + 0.35 * crackle(d, 90, 1800, False)


@se("Flame_Breath", "敵の攻撃", SHOT, "短い火炎を吐く（「ボウッ」と1秒）", "火蜥蜴の火炎（1秒）・炎の魔物")
def _():
    d = 1.3
    ign = mix(0.3, [(0, thump(0.3, 120, 60, 0.06), 0.6), (0, burst(0.3, 200, 2500, 0.05, -3), 0.7)])
    f = fire_noise(d, 2200) * env(d, [(0, 0), (0.06, 1), (1.0, 0.8), (d, 0)])
    return mix(d, [(0, ign, 0.8), (0, f, 1.0)])


@se("Flamethrower_Start", "敵の攻撃", SHOT, "火炎放射の吹き始め（点火して一気に噴き出す）", "ベリットの火炎放射の出だし（この後 Flamethrower_Loop をつなぐ）")
def _():
    d = 0.7
    ign = mix(0.3, [(0, click(0.005, 600), 0.6), (0, thump(0.3, 100, 45, 0.08, 2), 0.8), (0, burst(0.3, 150, 3000, 0.06, -3), 0.8)])
    f = fire_noise(d, curve(d, [(0, 800), (0.3, 2800), (d, 2800)], "exp")) * env(d, [(0, 0), (0.1, 1), (d, 1)])
    return mix(d, [(0, ign, 0.9), (0.02, f, 0.9)])


@se("Flamethrower_Loop", "敵の攻撃", LOOP, "火炎放射の噴き続け（ループ用）", "ベリットの火炎放射（1.8秒）の間くり返す", loop=True)
def _():
    return make_loop(lambda d: fire_noise(d, 2800), 2.0, 0.3)


@se("Shoulder_Charge_Loop", "敵の攻撃", LOOP, "肩からの突進（地響きの足音と空気を裂く音、ループ用）", "ベリットの突進・巣守りのバチ・看守の犬などの突進中", loop=True)
def _():
    def fn(d):
        wind = bp(white(d), 1200, 0.5) * (1 + 0.2 * np.sin(phase_of(1.5, d)))
        steps = np.zeros(N(d))
        for i in range(int(d / 0.16) + 1):
            s = thump(0.15, 90, 45, 0.04, 2.5)
            at = N(i * 0.16)
            e = min(len(steps), at + len(s))
            steps[at:e] += s[: e - at]
        return norm(wind) * 0.5 + norm(lp(pink(d), 300)) * 0.4 + steps * 0.8
    return make_loop(fn, 1.6, 0.16)


@se("Shoulder_Charge_Hit", "敵の攻撃", BIG, "突進がぶつかる（全身でぶち当たる重い衝突）", "突進の命中・壁に止まったとき")
def _():
    d = 1.0
    return reverb(mix(d, [(0, thump(0.8, 130, 35, 0.18, 4), 1.0), (0, burst(0.5, 150, 3000, 0.08, -3), 0.9),
                          (0, click(0.006, 800), 0.6), (0.02, grains(0.5, 20, freq=(300, 2000)), 0.2)]), 0.8, 0.15)


# ---------------- 空鯨 ----------------

@se("Whale_Inhale", "空鯨", SHOT, "大きく息を吸う（空気が渦を巻いて吸い込まれる、0.9秒）", "光のブレスの予備動作（0.9秒）")
def _():
    d = 1.1
    air = bp(white(d), curve(d, [(0, 300), (0.9, 1800), (d, 1800)], "exp"), 0.6) * env(d, [(0, 0), (0.8, 1), (1.05, 0), (d, 0)])
    low = lp(brown(d), curve(d, [(0, 80), (0.9, 300), (d, 300)], "exp")) * env(d, [(0, 0), (0.75, 1), (1.0, 0), (d, 0)])
    return mix(d, [(0, norm(air), 0.7), (0, norm(low), 0.8)])


@se("Whale_Breath", "空鯨", BIG, "光のブレス（巨大な光の奔流、1.2秒）", "光のブレス（幅4m×長さ40m）")
def _():
    d = 1.8
    f0 = 55
    chord = sum(osc(f0 * k * (1 + 0.003 * RNG.uniform(-1, 1)), d, "saw") / k for k in (1, 1.5, 2, 3, 4, 6))
    chord = lp(chord, curve(d, [(0, 400), (0.15, 3500), (1.2, 3000), (d, 500)], "exp"))
    roar = lp(brown(d), 2000) + 0.4 * bp(white(d), 5000, 0.5)
    e = env(d, [(0, 0), (0.08, 1), (1.2, 0.9), (d, 0)])
    x = mix(d, [(0, norm(chord) * e, 0.6), (0, norm(roar) * e, 0.8), (0, explosion(0.8, 0.7), 0.6)])
    return reverb(x, 1.5, 0.25, lpf=3500)


@se("Whale_TailSwipe", "空鯨", BIG, "尾の薙ぎ払い（巨大な尾が空気を押しのける重い風）", "尾の薙ぎ払い（背後270°・半径14m）")
def _():
    d = 1.6
    w = whoosh(1.2, [(0, 120), (0.5, 600), (1.2, 150)], 0.5, 0.18, skew=1.5, q=0.5, body=2.0)
    sub = thump(1.0, 60, 30, 0.3, 1.5)
    return reverb(mix(d, [(0, w, 1.0), (0.45, sub, 0.6)]), 1.4, 0.2, lpf=2000)


@se("Whale_SoulSuck_Loop", "空鯨", LOOP, "魂の吸い込み（不気味な声のような響きと吸い込む風、ループ用）", "魂の吸い込み（4秒）の間くり返す", loop=True)
def _():
    def fn(d):
        voices = np.zeros(N(d))
        for f in (196, 233, 294, 392, 466):
            vib = f * (1 + 0.006 * np.sin(phase_of(RNG.uniform(4, 6), d)))
            voices += osc(vib, d, "saw") * (0.6 + 0.4 * np.sin(phase_of(RNG.uniform(0.2, 0.5), d) + RNG.uniform(0, TAU)))
        voices = bp(voices, 700, 1.5) + 0.6 * bp(voices, 1150, 2)  # 「あー」という母音っぽく
        wind = bp(white(d), 500 + 300 * np.sin(phase_of(0.5, d)), 0.7)
        return norm(voices) * 0.6 + norm(wind) * 0.6 + norm(lp(brown(d), 120)) * 0.4
    return make_loop(fn, 4.0, 0.5)


@se("Whale_Shake", "空鯨", HEAVY, "身震い（背中がぶるっと震えて、はじき飛ばされる）", "身震い（背のフィナを落とす）")
def _():
    d = 0.8
    rum = lp(brown(0.5), 200) * (0.5 + 0.5 * np.sign(np.sin(phase_of(14, 0.5)))) * env(0.5, [(0, 0), (0.03, 1), (0.5, 0.3)])
    return reverb(mix(d, [(0, norm(lp(rum, 400)), 0.8), (0.35, whoosh(0.4, [(0, 400), (0.1, 1500), (0.4, 500)], 0.1, 0.06, 2), 0.6), (0.3, thump(0.3, 100, 45, 0.06), 0.6)]), 1.0, 0.2)


# =====================================================================
# 魔法（魔法陣の8属性）
# =====================================================================

ELEMS = ["Fire", "Ice", "Thunder", "Wind", "Water", "Earth", "Light", "Dark"]
ELEM_JP = dict(Fire="炎", Ice="氷", Thunder="雷", Wind="風", Water="水", Earth="土", Light="光", Dark="闇")


@se("Magic_Circle_Appear", "魔法", LIGHT, "魔法陣が現れる（低い和音が「フゥン」とふくらんで輪が広がる）", "魔法陣クリップの Appear")
def _():
    d = 1.3
    # 低い和音が「フゥン」とふくらんで輪が広がる
    pad = sum(osc(f * (1 + 0.004 * RNG.uniform(-1, 1)), d, "saw") for f in (65.4, 98, 131, 196))
    pad = lp(pad, curve(d, [(0, 200), (0.4, 1200), (d, 300)], "exp")) * env(d, [(0, 0), (0.35, 1), (d, 0)])
    return reverb(mix(d, [(0, norm(pad), 0.7), (0, whoosh(0.8, [(0, 300), (0.35, 1500), (0.8, 400)], 0.35, 0.15, 1.3, q=0.6, body=1.0), 0.6)]), 1.2, 0.3, lpf=2500)


@se("Magic_Charge", "魔法", LIGHT, "魔力を溜める（うなりが高まっていく、約0.6秒）", "魔法陣クリップの Charge")
def _():
    d = 0.8
    f = curve(d, [(0, 70), (0.6, 240), (d, 250)], "exp")
    tone = (osc(f, d, "saw") * 0.4 + osc(f * 1.5, d) + osc(f * 2.01, d) * 0.5)
    tone = lp(tone, f * 6) * env(d, [(0, 0), (0.55, 1), (0.65, 0.6), (d, 0)]) * (1 + 0.4 * np.sin(phase_of(curve(d, [(0, 6), (0.6, 24)]), d)))
    return reverb(mix(d, [(0, norm(tone), 0.8),
                          (0, whoosh(0.6, [(0, 300), (0.6, 2500)], 0.55, 0.15, 0.3, body=0.5), 0.35)]), 0.8, 0.25)


def shot_whoosh(d, lo, hi):
    return whoosh(d, [(0, lo), (0.05, hi), (d, lo)], 0.05, 0.08, skew=3, q=0.9, body=0.6)


def magic_shot(e):
    d = 0.7
    if e == "Fire":
        ign = mix(0.3, [(0, thump(0.3, 140, 60, 0.05), 0.7), (0, burst(0.3, 200, 3000, 0.05, -3), 0.8)])
        return mix(d, [(0, ign, 1.0), (0, fire_noise(0.6, 2500) * expdec(0.6, 0.18, 0.01), 0.7), (0, shot_whoosh(0.6, 400, 1600), 0.5)])
    if e == "Ice":
        glass = partials(0.6, [2900, 4400, 6100, 7900], [0.25, 0.2, 0.15, 0.1], detune=0.01)
        return reverb(mix(d, [(0, glass, 0.5), (0, sparkle(0.5, 20, 5000, 11000), 0.3), (0, shot_whoosh(0.6, 1500, 5000), 0.7), (0, click(0.004, 3000), 0.5)]), 0.7, 0.25)
    if e == "Thunder":
        buzz = drive(osc(np.maximum(30, 80 + 800 * lp(white(0.7), 30)), 0.7, "saw"), 3) * expdec(0.7, 0.12, 0.002)
        return mix(d, [(0, hp(buzz, 300), 0.6), (0, crackle(0.7, 1500, 1000) * expdec(0.7, 0.15), 0.6), (0, burst(0.1, 1000, 12000, 0.01, 1), 1.0), (0, shot_whoosh(0.5, 1000, 4000), 0.4)])
    if e == "Wind":
        swirl = bp(white(d), 1200 + 900 * np.sin(phase_of(curve(d, [(0, 10), (d, 4)]), d)), 2) * env(d, [(0, 0), (0.04, 1), (d, 0)])
        return mix(d, [(0, norm(swirl), 0.7), (0, shot_whoosh(d, 600, 3000), 0.8)])
    if e == "Water":
        return mix(d, [(0, bubbles(0.5, 18, 500, 2000), 0.6), (0, burst(0.2, 300, 3000, 0.04, -2), 0.6), (0, shot_whoosh(0.6, 500, 2000), 0.6),
                       (0, lp(pink(0.5), 1500) * expdec(0.5, 0.12) * (1 + 0.5 * np.sin(phase_of(18, 0.5))), 0.3)])
    if e == "Earth":
        return mix(d, [(0, thump(0.5, 110, 45, 0.1, 3), 1.0), (0, grains(0.5, 30, freq=(250, 2500)), 0.4), (0, burst(0.3, 100, 1500, 0.06, -5), 0.7), (0.03, shot_whoosh(0.6, 250, 900), 0.6)])
    if e == "Light":
        pad = lp(sum(osc(f, 0.7, "saw") for f in (131, 196, 262)), 1500) * expdec(0.7, 0.2, 0.01)
        return reverb(mix(d, [(0, norm(pad), 0.6), (0, burst(0.3, 300, 5000, 0.05, -2), 0.6), (0, thump(0.3, 160, 70, 0.05), 0.6), (0, shot_whoosh(0.6, 1200, 3500), 0.8)]), 0.9, 0.25, lpf=3500)
    if e == "Dark":
        f = curve(0.7, [(0, 200), (0.7, 70)], "exp")
        growl = drive(osc(f, 0.7, "saw") + osc(f * 1.01, 0.7, "saw") + osc(f * 0.5, 0.7, "square") * 0.5, 2.5)
        growl = lp(growl, 1500) * env(0.7, [(0, 0), (0.03, 1), (0.7, 0)])
        return reverb(mix(d, [(0, norm(growl), 0.6), (0, rev(norm(hp(white(0.25), 1500)) * expdec(0.25, 0.08)), 0.3), (0.2, shot_whoosh(0.5, 300, 1200), 0.6)]), 1.0, 0.3, lpf=2500)


def magic_impact(e):
    d = 1.6
    if e == "Fire":
        return mix(d, [(0, explosion(1.0, 0.6, 3000), 1.0), (0.05, crackle(0.9, 120, 1500), 0.3)])
    if e == "Ice":
        shards = np.zeros(N(0.9))
        for _ in range(40):
            at = N(min(0.8, RNG.exponential(0.08)))
            s = partials(0.2, [RNG.uniform(3000, 9000), RNG.uniform(4000, 11000)], [0.04, 0.03]) * RNG.uniform(0.3, 1)
            e_ = min(len(shards), at + len(s))
            shards[at:e_] += s[: e_ - at]
        return reverb(mix(d, [(0, burst(0.4, 2000, 12000, 0.05, 0), 0.8), (0, shards, 0.6), (0, thump(0.3, 200, 90, 0.04), 0.5)]), 0.9, 0.2)
    if e == "Thunder":
        crack = burst(0.15, 800, 14000, 0.015, 1)
        rumble = lp(brown(1.1), curve(1.1, [(0, 2000), (1.1, 150)], "exp")) * env(1.1, [(0, 0), (0.02, 1), (0.3, 0.7), (1.1, 0)]) * (1 + 0.5 * lp(white(1.1), 12) * 8)
        return reverb(mix(d, [(0, crack, 1.0), (0, crackle(0.3, 3000, 2000), 0.5), (0.01, norm(rumble), 0.8), (0, thump(0.5, 100, 40, 0.1), 0.5)]), 1.2, 0.2)
    if e == "Wind":
        gust = whoosh(1.5, [(0, 2500), (0.05, 3500), (1.5, 300)], 0.04, 0.15, skew=3, q=0.6, body=1.0)
        return mix(d, [(0, gust, 1.0), (0, thump(0.3, 150, 70, 0.05), 0.4), (0, burst(0.2, 500, 6000, 0.03, 0), 0.5)])
    if e == "Water":
        return mix(d, [(0, burst(0.5, 250, 5000, 0.1, -2), 1.0), (0, thump(0.3, 130, 60, 0.05), 0.5), (0.02, bubbles(1.0, 40, 600, 3000), 0.5), (0, hp(white(0.8), 3000) * expdec(0.8, 0.2), 0.25)])
    if e == "Earth":
        return reverb(mix(d, [(0, thump(1.0, 90, 30, 0.2, 3.5), 1.0), (0, burst(0.5, 150, 3000, 0.08, -3), 0.8), (0.01, grains(1.0, 90, dur=(0.006, 0.05), freq=(250, 3500)), 0.5)]), 0.9, 0.15, lpf=3000)
    if e == "Light":
        pad = lp(sum(osc(f, 1.2, "saw") for f in (65.4, 131, 196, 262)), curve(1.2, [(0, 3000), (1.2, 300)], "exp")) * expdec(1.2, 0.35, 0.005)
        flash = burst(0.6, 300, 6000, 0.12, -2)
        return reverb(mix(d, [(0, flash, 0.8), (0, norm(pad), 0.6), (0, thump(0.6, 110, 40, 0.12, 2.5), 0.9)]), 1.3, 0.25, lpf=3000)
    if e == "Dark":
        suck = rev(norm(lp(white(0.35), 2500)) * expdec(0.35, 0.12))
        boom = drive(thump(0.9, 70, 25, 0.25, 4) + 0.5 * lp(brown(0.9), 300) * expdec(0.9, 0.2), 1.5)
        f = curve(0.8, [(0, 300), (0.8, 60)], "exp")
        moan = lp(osc(f, 0.8, "saw") + osc(f * 1.02, 0.8, "saw"), 1000) * expdec(0.8, 0.3)
        return reverb(mix(d, [(0, suck, 0.6), (0.33, boom, 1.0), (0.33, norm(moan), 0.4)]), 1.3, 0.3, lpf=2000)


for _e in ELEMS:
    se(f"Magic_Shot_{_e}", "魔法", SHOT, f"{ELEM_JP[_e]}の玉を撃ち出す", "魔法陣クリップの Fire:番号（玉を撃つ瞬間）")((lambda e: lambda: magic_shot(e))(_e))
for _e in ELEMS:
    se(f"Magic_Impact_{_e}", "魔法", HEAVY, f"{ELEM_JP[_e]}の玉の着弾", "魔法陣クリップの Impact:番号")((lambda e: lambda: magic_impact(e))(_e))

SHOT_DESC = dict(Fire="「ボッ」と火がついて燃えながら飛ぶ", Ice="澄んだガラスのような響きと冷たいきらめき", Thunder="「バチッ」とはじける電気のうなり",
                 Wind="渦を巻いて飛ぶ風", Water="泡立ちながら水の玉が飛ぶ", Earth="岩が「ドン」と撃ち出される",
                 Light="まぶしい光が太い和音とともに飛ぶ", Dark="低くうなる不気味な音")
IMPACT_DESC = dict(Fire="爆発してパチパチ燃え残る", Ice="氷が砕け散る", Thunder="落雷の「バリッ」と遠雷", Wind="突風が吹き抜ける",
                   Water="水しぶきがはじけて泡立つ", Earth="岩が砕けて破片が散らばる", Light="まぶしくはじけて「ドォン」と光が広がる",
                   Dark="吸い込まれてから低く「ドゥン」と沈む")
for s in SE:
    for _e in ELEMS:
        if s["name"] == f"Magic_Shot_{_e}":
            s["desc"] = f"{ELEM_JP[_e]}の玉を撃ち出す（{SHOT_DESC[_e]}）"
        if s["name"] == f"Magic_Impact_{_e}":
            s["desc"] = f"{ELEM_JP[_e]}の玉の着弾（{IMPACT_DESC[_e]}）"


@se("Magic_Beam", "魔法", SHOT + 1, "ビームを撃つ（溜めがはじけて光線が伸び続ける、約1.6秒）", "魔法陣クリップの BeamStart（Beam は 1.4秒、Beam_Sweep は 1.8秒）")
def _():
    d = 2.0
    f0 = 110
    tone = sum(osc(f0 * k * (1 + 0.002 * RNG.uniform(-1, 1)), d, "saw") / k for k in (1, 2, 3, 4, 5))
    tone = lp(tone, 2500) * (1 + 0.15 * np.sin(phase_of(9, d)))
    hiss = bp(white(d), 4000, 0.5)
    e = env(d, [(0, 0), (0.05, 1), (1.5, 0.9), (d, 0)])
    x = mix(d, [(0, burst(0.2, 400, 8000, 0.03, -1), 0.8), (0, thump(0.3, 150, 60, 0.05), 0.6), (0, norm(tone) * e, 0.6), (0, norm(hiss) * e, 0.3)])
    return reverb(x, 0.9, 0.2)


@se("Magic_Pillar", "魔法", BIG, "光の柱が噴き上がる（地面から轟音とともに立ちのぼる）", "魔法陣クリップの PillarStart")
def _():
    d = 1.6
    up = whoosh(1.2, [(0, 200), (0.3, 2500), (1.2, 1200)], 0.2, 0.1, skew=6, q=0.6, body=1.2)
    x = mix(d, [(0, thump(0.8, 90, 35, 0.2, 3), 1.0), (0, up, 0.8), (0.05, lp(sum(osc(f, 1.2, "saw") for f in (65.4, 98, 131)), 700) * env(1.2, [(0, 0), (0.1, 1), (1.2, 0)]), 0.12)])
    return reverb(x, 1.2, 0.25)


# =====================================================================

def build(filters=None):
    os.makedirs(OUT, exist_ok=True)
    meta = []
    for s in SE:
        if filters and not any(f in s["name"] for f in filters):
            continue
        dsp.seed(s["name"])
        x = s["fn"]()
        bright = "Ice" in s["name"] or "Thunder" in s["name"]
        x = weight_eq(x, 5.0, 0.0 if bright else -5.0, loop=s["loop"])
        x = finish(x, s["level"], loop=s["loop"])
        path = os.path.join(OUT, s["name"] + ".wav")
        write_wav(path, x)
        peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
        meta.append(dict(name=s["name"], group=s["group"], desc=s["desc"], use=s["use"], loop=s["loop"], sec=round(len(x) / SR, 3), peak_db=round(peak, 2)))
        print(f"{s['name']:24s} {len(x) / SR:5.2f}秒 ピーク {peak:6.2f}dB")
    if not filters:
        with open(os.path.join(HERE, "se_list.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"{len(meta)} 音 → {os.path.normpath(OUT)}")


if __name__ == "__main__":
    build(sys.argv[1:] or None)
