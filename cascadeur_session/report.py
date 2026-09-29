"""シーン情報のレポート出力（csc に依存しない純粋な処理）。"""

import csv
import fnmatch
import os


def filter_names(objects, pattern=None):
    """(id, name) の列から、名前がワイルドカード pattern に一致するものだけ返す。名前順。"""
    rows = [(oid, name) for oid, name in objects if not pattern or fnmatch.fnmatchcase(name, pattern)]
    return sorted(rows, key=lambda r: r[1])


def write_objects_csv(path, objects):
    """(id, name) の列を UTF-8 (BOM 付き、Excel で文字化けしない) の CSV に書き出す。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "name"])
        for oid, name in objects:
            w.writerow([oid, name])
    return path
