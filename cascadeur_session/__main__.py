"""コマンドライン:  python -m cascadeur_session <サブコマンド>

  health                 スクリプトサーバーが動いているか確認
  run "<code>"           Python コードを Cascadeur 内で実行
  run-file <path.py>     ファイルの中身を Cascadeur 内で実行
  log [-n 50]            Cascadeur のログの末尾を表示（run でエラーが返らないとき用）
  check-names <path>...  書き出した FBX の名前から Unity での扱いを表示
"""

import argparse
import glob
import os
import sys

from . import client, motion_names


def _print(text):
    # Windows のコンソールで文字化け・例外にならないようにする
    enc = sys.stdout.encoding or "utf-8"
    print(text.encode(enc, "replace").decode(enc))


def cmd_check_names(paths):
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, "*.fbx"))) if os.path.isdir(p) else [p]
    if not files:
        _print("FBX が見つかりません")
        return 1
    bad = 0
    for f in files:
        kind = motion_names.classify(f)
        _print("%-40s %s" % (motion_names.clip_name(f), motion_names.DESCRIPTIONS[kind]))
        for w in motion_names.warnings(f):
            bad += 1
            _print("    ! " + w)
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m cascadeur_session", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=client.DEFAULT_URL, help="スクリプトサーバーの URL")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    p = sub.add_parser("run")
    p.add_argument("code")
    p = sub.add_parser("run-file")
    p.add_argument("path")
    p = sub.add_parser("log")
    p.add_argument("-n", type=int, default=50)
    p = sub.add_parser("check-names")
    p.add_argument("paths", nargs="+")
    a = ap.parse_args(argv)

    try:
        if a.cmd == "health":
            _print(client.health(a.url))
        elif a.cmd == "run":
            _print(client.format_reply(client.run(a.code, a.url)))
        elif a.cmd == "run-file":
            with open(a.path, encoding="utf-8") as f:
                _print(client.format_reply(client.run(f.read(), a.url)))
        elif a.cmd == "log":
            _print(client.tail(client.log_path(), a.n))
        elif a.cmd == "check-names":
            return cmd_check_names(a.paths)
    except client.ServerError as e:
        _print(str(e))
        return 2
    except OSError as e:
        _print("エラー: %s" % e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
