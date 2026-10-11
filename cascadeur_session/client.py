"""Cascadeur のスクリプトサーバー (Scripts > MCP > Start script server) を呼ぶクライアント。

標準ライブラリだけで動く。サーバーの仕様は docs/Cascadeur_引継ぎ.md を参照:
  GET  /health
  POST /run   本文 {"code": "..."}  (app / scene / csc が使える。print の出力が返る)
"""

import json
import os
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("CASCADEUR_URL", "http://127.0.0.1:8765")

# 引継ぎ資料の注意: run の scene は最初のタブを指したままになることがあるので、
# 送るコードの先頭で現在のタブに差し替える。
PRELUDE = "scene = app.current_scene()\n"


class ServerError(RuntimeError):
    pass


def _open(req, timeout):
    # localhost へのアクセスがプロキシ設定に吸われないよう、プロキシを使わない
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout) as res:
            return res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise ServerError("HTTP %d: %s" % (e.code, e.read().decode("utf-8", "replace")))
    except (urllib.error.URLError, OSError) as e:
        raise ServerError(
            "Cascadeur のスクリプトサーバーに接続できません (%s)。\n"
            "Cascadeur で Scripts > MCP > Start script server を実行してください。" % e
        )


def health(url=DEFAULT_URL, timeout=5):
    return _open(urllib.request.Request(url.rstrip("/") + "/health"), timeout)


def run(code, url=DEFAULT_URL, timeout=120, use_current_scene=True):
    """code を Cascadeur 内で実行し、サーバーの返答（文字列）を返す。"""
    if use_current_scene:
        code = PRELUDE + code
    req = urllib.request.Request(
        url.rstrip("/") + "/run",
        data=json.dumps({"code": code}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return _open(req, timeout)


def format_reply(body):
    """返答が JSON なら中身を読みやすく並べる。形式が分からないのでそのままも許す。"""
    try:
        data = json.loads(body)
    except ValueError:
        return body
    if not isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False, indent=2)
    parts = []
    for key, value in data.items():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
        parts.append("[%s]\n%s" % (key, text.rstrip()) if "\n" in text else "[%s] %s" % (key, text))
    return "\n".join(parts)


def log_path(env=None):
    env = os.environ if env is None else env
    base = env.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.join(base, "Nekki Limited", "Cascadeur", "logs", "cascadeur_log.log")


def tail(path, lines=50):
    with open(path, encoding="utf-8", errors="replace") as f:
        return "".join(f.readlines()[-lines:])
