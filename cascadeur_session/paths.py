"""出力先パスとファイル名の組み立て（csc に依存しない純粋な処理）。"""

import datetime
import os
import re

ENV_OUTPUT_DIR = "CASCADEUR_SESSION_OUTPUT"
_INVALID = re.compile(r'[\\/:*?"<>|\x00-\x1f]+')


def output_dir(env=None, home=None):
    """出力フォルダ。環境変数 CASCADEUR_SESSION_OUTPUT があればそれを使う。"""
    env = os.environ if env is None else env
    if env.get(ENV_OUTPUT_DIR):
        return env[ENV_OUTPUT_DIR]
    home = os.path.expanduser("~") if home is None else home
    return os.path.join(home, "Documents", "CASCADEUR_SESSION", "output")


def safe_filename(name, default="untitled"):
    """Windows でも使えるファイル名に変換する。"""
    cleaned = _INVALID.sub("_", name).strip(" .")
    return cleaned or default


def timestamped_path(directory, stem, ext, now=None):
    """<directory>/<stem>_YYYYmmdd_HHMMSS.<ext> を返す（フォルダは作らない）。"""
    now = now or datetime.datetime.now()
    ext = ext.lstrip(".")
    return os.path.join(directory, "%s_%s.%s" % (safe_filename(stem), now.strftime("%Y%m%d_%H%M%S"), ext))
