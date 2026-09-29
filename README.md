# CASCADEUR_SESSION

HELLEDEN の人型モーション（斬り・ジャンプ・パンチなど）を Cascadeur で作る作業を、Python から補助するツール。

- 手順書: [docs/Cascadeur.md](docs/Cascadeur.md)
- 進み具合と次にやること: [docs/Cascadeur_引継ぎ.md](docs/Cascadeur_引継ぎ.md)

Python 3 の標準ライブラリだけで動く（追加インストール不要）。Windows のコマンドプロンプトでこのフォルダに移動して使う。

## 準備

Cascadeur を起動し、メニュー **Scripts > MCP > Start script server** を実行する（起動のたびに必要）。

## 使い方

```bat
python -m cascadeur_session health
python -m cascadeur_session run "print(app.current_scene())"
python -m cascadeur_session run-file snippets\probe_api.py
python -m cascadeur_session log -n 100
python -m cascadeur_session check-names D:\HELLEDEN\Assets\Motions\Cascadeur
```

| サブコマンド | 内容 |
|---|---|
| `health` | スクリプトサーバーが動いているか確認 |
| `run "<code>"` | コードを Cascadeur 内で実行。`app`・`scene`・`csc` が使える。`scene` は自動で現在のタブに差し替える |
| `run-file <path>` | ファイルの中身を Cascadeur 内で実行 |
| `log [-n N]` | `%LOCALAPPDATA%\Nekki Limited\Cascadeur\logs\cascadeur_log.log` の末尾を表示（`run` でエラーが返らないとき用） |
| `check-names <フォルダ or ファイル>` | 書き出した FBX の名前から、Unity での扱い（高さを残す / ループ / 1 回再生）を表示し、誤判定しそうな名前に注意を出す |

サーバーの URL は `--url` か環境変数 `CASCADEUR_URL` で変えられる（既定 `http://127.0.0.1:8765`）。

## スニペット

| ファイル | 内容 |
|---|---|
| `snippets/probe_api.py` | シーン保存・FBX アニメ書き出し・AutoPhysics などに使えそうな API 名を一覧表示する（まだ使える呼び出しが分かっていない所を調べる用） |

## 開発

```sh
python -m unittest discover -s tests -t .
```

`cascadeur_session/motion_names.py` の命名ルールは Unity 側（`Assets/HELLEDEN/Editor/CascadeurImport.cs` 経由の取り込み）を写したもの。実装とずれたらこちらを合わせる。
