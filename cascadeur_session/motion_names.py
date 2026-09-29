"""書き出す FBX のファイル名から、Unity 取り込み時の扱いを判定する。

docs/Cascadeur.md「4. 書き出して Unity へ」の命名ルールを写したもの。
Unity 側 (HELLEDEN > Player > Import Cascadeur Motions) の実装とずれたら、こちらを合わせること。

未確認の前提:
- 大文字小文字は区別しない
- jump 系と loop 系の両方を含む名前は jump 系を優先する
- loop 系の「など」に当たる語は不明なので idle/walk/run/wait のみ
"""

import os

KEEP_HEIGHT_WORDS = ("jump", "leap", "dive", "flip", "vault")
LOOP_WORDS = ("idle", "walk", "run", "wait")

KEEP_HEIGHT = "keep_height"  # 高さ (Y) の動きを残す
LOOP = "loop"                # ループ再生
ONE_SHOT = "one_shot"        # 1 回再生、前後の移動は体に焼き込む

DESCRIPTIONS = {
    KEEP_HEIGHT: "高さ (Y) の動きを残す",
    LOOP: "ループ再生",
    ONE_SHOT: "1 回再生・前後の移動は体に焼き込む",
}


def clip_name(filename):
    """ファイル名（パス可）からクリップ名（拡張子なし）を返す。"""
    return os.path.splitext(os.path.basename(filename))[0]


def classify(filename):
    """KEEP_HEIGHT / LOOP / ONE_SHOT のいずれかを返す。"""
    name = clip_name(filename).lower()
    if any(w in name for w in KEEP_HEIGHT_WORDS):
        return KEEP_HEIGHT
    if any(w in name for w in LOOP_WORDS):
        return LOOP
    return ONE_SHOT


def warnings(filename):
    """意図しない扱いになりそうな名前への注意を返す。"""
    name = clip_name(filename)
    lower = name.lower()
    out = []
    if not filename.lower().endswith(".fbx"):
        out.append("拡張子が .fbx ではありません")
    hits = [w for w in KEEP_HEIGHT_WORDS + LOOP_WORDS if w in lower]
    for w in hits:
        # 単語の一部として含まれている (例: "brunt" の run) と誤判定になる
        for token in lower.replace("-", "_").split("_"):
            if w in token and token != w and not token.startswith(w) and not token.endswith(w):
                out.append("「%s」の中に %s が含まれ、%s として扱われます" % (token, w, DESCRIPTIONS[classify(filename)]))
                break
    return out
