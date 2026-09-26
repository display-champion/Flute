# -*- coding: utf-8 -*-
"""SE を合成するための小さな道具箱（numpy / scipy だけで動く）。"""
import numpy as np
from scipy.signal import lfilter, fftconvolve, butter, sosfilt

SR = 44100
TAU = 2 * np.pi
RNG = np.random.default_rng(1)


def seed(name):
    """音ごとに乱数を固定する（作り直しても同じ音になる）"""
    global RNG
    RNG = np.random.default_rng(abs(hash_str(name)) % (2 ** 32))


def hash_str(s):
    h = 2166136261
    for ch in s.encode("utf-8"):
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


def N(d):
    return max(1, int(round(d * SR)))


def T(d):
    return np.arange(N(d)) / SR


def silence(d):
    return np.zeros(N(d))


# ---------------- 雑音 ----------------

def white(d):
    return RNG.standard_normal(N(d))


def colored(d, slope_db_oct):
    """傾きつきの雑音（-3 = ピンク、-6 = ブラウン）"""
    n = N(d)
    X = np.fft.rfft(RNG.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1] if n > 2 else 1
    X *= (f / 1000.0) ** (slope_db_oct / 6.02)
    X[f < 30] = 0   # 聞こえない低さ（30Hz 未満）は消す（波形がふらつき、音量の余裕を食うため）
    x = np.fft.irfft(X, n)
    return x / (np.std(x) + 1e-12)


def pink(d):
    return colored(d, -3)


def brown(d):
    return colored(d, -6)


# ---------------- 時間で変わる値 ----------------

def curve(d, pts, mode="lin"):
    """[(時刻, 値), ...] を折れ線でつなぐ。mode="exp" は対数でつなぐ（周波数向け）"""
    t = T(d)
    ts = np.array([p[0] for p in pts], float)
    vs = np.array([p[1] for p in pts], float)
    if mode == "exp":
        return np.exp(np.interp(t, ts, np.log(np.maximum(vs, 1e-6))))
    return np.interp(t, ts, vs)


def env(d, pts):
    return curve(d, pts, "lin")


def expdec(d, tau, attack=0.002, hold=0.0):
    t = T(d)
    a = np.clip(t / max(attack, 1e-5), 0, 1)
    dec = np.exp(-np.maximum(t - attack - hold, 0) / tau)
    return a * dec


def bell_env(d, peak, width, skew=1.0):
    """山なりの包絡（peak の時刻で 1。skew > 1 で後ろが長い）"""
    t = T(d)
    w = np.where(t < peak, width, width * skew)
    return np.exp(-0.5 * ((t - peak) / w) ** 2)


# ---------------- フィルター ----------------

def _rbj(kind, f, q):
    f = np.clip(f, 20, SR * 0.45)
    w = TAU * f / SR
    cw, sw = np.cos(w), np.sin(w)
    al = sw / (2 * q)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
    elif kind == "bp":
        b = [al, 0, -al]
    else:
        raise ValueError(kind)
    a = [1 + al, -2 * cw, 1 - al]
    return np.array(b) / a[0], np.array(a) / a[0]


def _shelf(kind, f, gain_db):
    A = 10 ** (gain_db / 40)
    w = TAU * f / SR
    cw, sw = np.cos(w), np.sin(w)
    al = sw / 2 * np.sqrt(2)
    sA = 2 * np.sqrt(A) * al
    if kind == "low":
        b = [A * ((A + 1) - (A - 1) * cw + sA), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sA)]
        a = [(A + 1) + (A - 1) * cw + sA, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sA]
    else:
        b = [A * ((A + 1) + (A - 1) * cw + sA), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sA)]
        a = [(A + 1) - (A - 1) * cw + sA, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sA]
    return np.array(b) / a[0], np.array(a) / a[0]


def weight_eq(x, low_db=5.0, high_db=-5.0, low_f=160, high_f=4500, loop=False):
    """重厚感：低い所を持ち上げ、高い所を抑える。ループは前後をつないで処理し、つなぎ目を保つ"""
    y = np.concatenate([x, x, x]) if loop else np.asarray(x, float)
    b, a = _shelf("low", low_f, low_db)
    y = lfilter(b, a, y)
    if high_db:
        b, a = _shelf("high", high_f, high_db)
        y = lfilter(b, a, y)
    return y[len(x):2 * len(x)] if loop else y


def filt(x, kind, fc, q=0.707, stages=1, block=64):
    """カットオフ（または中心）周波数が時間で変わってよいフィルター。fc は数値か x と同じ長さの配列"""
    y = np.asarray(x, float)
    fcs = np.broadcast_to(np.asarray(fc, float), y.shape)
    const = np.ndim(fc) == 0
    for _ in range(stages):
        out = np.empty_like(y)
        zi = np.zeros(2)
        if const:
            b, a = _rbj(kind, float(fc), q)
            out, _ = lfilter(b, a, y, zi=zi)
        else:
            for s in range(0, len(y), block):
                e = min(len(y), s + block)
                b, a = _rbj(kind, float(np.mean(fcs[s:e])), q)
                out[s:e], zi = lfilter(b, a, y[s:e], zi=zi)
        y = out
    return y


def lp(x, fc, q=0.707, stages=1):
    return filt(x, "lp", fc, q, stages)


def hp(x, fc, q=0.707, stages=1):
    return filt(x, "hp", fc, q, stages)


def bp(x, fc, q=1.0, stages=1):
    return filt(x, "bp", fc, q, stages)


def band(x, lo, hi, order=4):
    sos = butter(order, [lo, min(hi, SR * 0.45)], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def dc_block(x):
    return lfilter([1, -1], [1, -0.995], x)


# ---------------- 発振器 ----------------

def phase_of(freq, d):
    f = np.broadcast_to(np.asarray(freq, float), (N(d),))
    return np.cumsum(TAU * f / SR)


def osc(freq, d, wave="sine", phase0=0.0):
    ph = phase_of(freq, d) + phase0
    if wave == "sine":
        return np.sin(ph)
    if wave == "saw":
        return 2 * ((ph / TAU) % 1.0) - 1
    if wave == "square":
        return np.sign(np.sin(ph))
    if wave == "tri":
        return 2 * np.abs(2 * ((ph / TAU) % 1.0) - 1) - 1
    raise ValueError(wave)


def partials(d, freqs, decays, amps=None, detune=0.0):
    """減衰する正弦波を重ねる（金属・鐘・ガラス）"""
    out = np.zeros(N(d))
    amps = amps or [1.0] * len(freqs)
    for f, tau, a in zip(freqs, decays, amps):
        f = f * (1 + detune * RNG.uniform(-1, 1))
        out += a * np.sin(phase_of(f, d) + RNG.uniform(0, TAU)) * expdec(d, tau, attack=0.0008)
    return out


def karplus(freq, d, damp=0.996, bright=0.5):
    """弦をはじいた音（弓の弦など）"""
    n = N(d)
    p = max(2, int(SR / freq))
    buf = RNG.uniform(-1, 1, p)
    buf = lp(buf, 800 + 8000 * bright)
    out = np.zeros(n)
    for i in range(n):
        j = i % p
        out[i] = buf[j]
        buf[j] = damp * 0.5 * (buf[j] + buf[(j + 1) % p])
    return out


# ---------------- 加工 ----------------

def drive(x, amt):
    return np.tanh(amt * x) / np.tanh(amt)


def reverb(x, t60=0.8, mix=0.2, lpf=5000, pre=0.012):
    """減衰する雑音をたたみ込む簡単な残響（音の後ろに残響ぶん長くなる）"""
    d = t60 * 1.1
    ir = RNG.standard_normal(N(d)) * np.exp(-6.9 * T(d) / t60)
    ir = lp(ir, lpf)
    ir[: N(pre)] = 0
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-12
    wet = fftconvolve(x, ir)
    y = np.zeros(len(wet))
    y[: len(x)] += x
    return y + mix * wet


def pad_to(x, n):
    return np.concatenate([x, np.zeros(max(0, n - len(x)))])[:n] if len(x) < n else x


def mix(d, parts):
    """[(開始秒, 信号, 音量)] を重ねる。d は最短の長さ（はみ出たら伸ばす）"""
    n = N(d)
    for at, sig, g in parts:
        n = max(n, N(at) + len(sig))
    out = np.zeros(n)
    for at, sig, g in parts:
        s = N(at) if at > 0 else 0
        sig = np.array(sig, float)
        k = min(len(sig), N(0.006))
        sig[-k:] *= np.linspace(1, 0, k)   # 途中で切れた音の「プツッ」を防ぐ
        out[s:s + len(sig)] += g * sig
    return out


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-12)


def rev(x):
    return x[::-1].copy()


# ---------------- よく使う部品 ----------------

WHOOSH_SCALE = 0.72   # 風切りの高さ（1 = 元のまま。低いほど重い）
WHOOSH_BODY = 0.35    # 風切りの「胴」の厚み（足す量）
THUMP_TAU = 1.3       # 「ドン」の余韻の長さの倍率


def whoosh(d, f_pts, amp_peak, width, skew=1.3, q=1.2, body=0.4, flutter=0.0):
    """空気を切る音。f_pts は中心周波数の折れ線 [(秒, Hz)]"""
    fc = curve(d, f_pts, "exp") * WHOOSH_SCALE
    body = body + WHOOSH_BODY
    x = bp(white(d), fc, q, stages=2) + body * lp(pink(d), fc * 0.5)
    e = bell_env(d, amp_peak, width, skew)
    if flutter:
        e *= 1 + 0.35 * np.sin(phase_of(flutter, d))
    return norm(x * e)


def thump(d, f0, f1, tau, drv=1.5):
    """低い「ドン」。周波数が f0 から f1 へ下がる"""
    tau = tau * THUMP_TAU
    f = curve(d, [(0, f0), (min(d, tau * 1.5), f1), (d, f1)], "exp")
    return drive(np.sin(phase_of(f, d)) * expdec(d, tau, attack=0.001), drv)


def click(d=0.006, lo=2000):
    return hp(white(d), lo) * expdec(d, d / 4, attack=0.0002)


def burst(d, lo, hi, tau, color=-3):
    """雑音のかたまり（打撃の「バシッ」）"""
    x = band(colored(d, color), lo, hi)
    return norm(x) * expdec(d, tau, attack=0.0008)


def grains(d, count, dur=(0.004, 0.03), freq=(800, 5000), density="decay", amp=(0.3, 1.0)):
    """細かい粒（破片・砂利・パチパチ）"""
    out = np.zeros(N(d))
    for _ in range(count):
        if density == "decay":
            at = min(d * 0.95, RNG.exponential(d / 4))
        else:
            at = RNG.uniform(0, d * 0.95)
        gd = RNG.uniform(*dur)
        f = np.exp(RNG.uniform(np.log(freq[0]), np.log(freq[1])))
        g = bp(white(gd), f, 3) * expdec(gd, gd / 3, attack=0.0003)
        g = norm(g) * RNG.uniform(*amp)
        s = N(at)
        e = min(len(out), s + len(g))
        out[s:e] += g[: e - s]
    return out


def crackle(d, rate, lo=1500, decay_env=True):
    """炎・電気のパチパチ"""
    n = N(d)
    imp = (RNG.uniform(0, 1, n) < rate / SR) * RNG.uniform(-1, 1, n)
    x = hp(lfilter([1], [1, -0.6], imp), lo)
    if decay_env:
        x *= np.linspace(1, 0.2, n)
    return norm(x)


def sparkle(d, count, fmin=2500, fmax=9000, tau=(0.03, 0.12)):
    """きらきら（高い短い鈴）"""
    out = np.zeros(N(d))
    for _ in range(count):
        at = RNG.uniform(0, d * 0.9)
        tt = RNG.uniform(*tau)
        gd = tt * 5
        f = np.exp(RNG.uniform(np.log(fmin), np.log(fmax)))
        g = np.sin(phase_of(f, gd)) * expdec(gd, tt, attack=0.001) * RNG.uniform(0.3, 1)
        s = N(at)
        e = min(len(out), s + len(g))
        out[s:e] += g[: e - s]
    return out


def bubbles(d, count, fmin=400, fmax=1600):
    """泡（周波数が上がる短い正弦波）"""
    out = np.zeros(N(d))
    for _ in range(count):
        at = RNG.uniform(0, d * 0.85)
        gd = RNG.uniform(0.02, 0.06)
        f0 = np.exp(RNG.uniform(np.log(fmin), np.log(fmax)))
        f = f0 * (1 + 2.5 * T(gd) / gd)
        g = np.sin(phase_of(f, gd)) * expdec(gd, gd / 3, attack=0.002) * RNG.uniform(0.3, 1)
        s = N(at)
        e = min(len(out), s + len(g))
        out[s:e] += g[: e - s]
    return out


def metal_ring(d, base, tau=0.25, inharm=(1, 1.47, 2.09, 2.56, 3.14, 4.2)):
    decs = [tau / (1 + 0.35 * i) for i in range(len(inharm))]
    amps = [1 / (1 + 0.5 * i) for i in range(len(inharm))]
    return partials(d, [base * k for k in inharm], decs, amps, detune=0.004)


def make_loop(fn, d, xfade=0.25):
    """つなぎ目で途切れないループ。fn(長さ) で作った音の頭とおしりを重ねる"""
    x = fn(d + xfade)
    n, m = N(d), N(xfade)
    y = x[:n].copy()
    w = np.linspace(0, 1, m)
    y[:m] = x[:m] * np.sin(w * np.pi / 2) + x[n:n + m] * np.cos(w * np.pi / 2)
    return y


# ---------------- 仕上げ ----------------

def finish(x, target_db, loop=False, tail_db=-60):
    """音量をそろえて（50ms ごとの一番大きい所を target_db に）、はみ出しをやわらかく抑える"""
    x = dc_block(np.asarray(x, float)) if not loop else np.asarray(x, float) - np.mean(x)
    w = N(0.05)
    p = np.convolve(x ** 2, np.ones(w) / w, mode="same")
    rms = np.sqrt(np.max(p)) + 1e-12
    x = x * (10 ** (target_db / 20) / rms)
    # やわらかい頭打ち（-3dB から丸め始め、-1dB を超えない）
    th, ceil = 10 ** (-3 / 20), 10 ** (-1 / 20)
    # 鋭い音（鞭・針など）は頭打ちでつぶれないよう、丸める量が 3dB を超えるぶんは全体を下げる
    peak = np.max(np.abs(x))
    if peak > ceil * 10 ** (3 / 20):
        x = x * (ceil * 10 ** (3 / 20) / peak)
    a = np.abs(x)
    over = a > th
    x[over] = np.sign(x[over]) * (th + (ceil - th) * np.tanh((a[over] - th) / (ceil - th)))
    if not loop:
        # 後ろの無音を切り、頭と終わりをなめらかに
        thr = 10 ** (tail_db / 20)
        idx = np.nonzero(np.abs(x) > thr)[0]
        end = min(len(x), (idx[-1] if len(idx) else len(x)) + N(0.01))
        x = x[:end]
        fi = min(len(x), N(0.0015))
        x[:fi] *= np.linspace(0, 1, fi)
        fo = min(len(x), N(0.02))
        x[-fo:] *= np.linspace(1, 0, fo)
    return x


def write_wav(path, x):
    import wave
    data = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def slow_noise(d, rate):
    """ゆっくり揺れる乱数（rate 回/秒くらいの速さ。平均 0・振れ幅およそ ±1）"""
    n = N(d)
    k = max(2, int(d * rate) + 3)
    pts = RNG.uniform(-1, 1, k)
    xs = np.linspace(0, d, k)
    t = T(d)
    # なめらかにつなぐ（余弦補間）
    i = np.clip(np.searchsorted(xs, t) - 1, 0, k - 2)
    u = (t - xs[i]) / (xs[i + 1] - xs[i])
    w = (1 - np.cos(np.pi * u)) / 2
    return pts[i] * (1 - w) + pts[i + 1] * w
