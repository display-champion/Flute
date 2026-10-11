# ガレスのテストモーション（Cascadeur）

Cascadeur で動きを滑らかにする流れを、ガレスで 1 本ずつ試すためのもの。
キーポーズだけを Blender で作り、間の動きは Cascadeur（Inbetweening・AutoPhysics）に作らせる。
手順の正本は HELLEDEN の [Cascadeur.md](../../docs/Cascadeur.md)。ここではガレス用の差分だけを書く。

| クリップ | 内容 | Unity での扱い（名前で決まる） |
|---|---|---|
| `gareth_test_jump` | その場ジャンプ（溜め → 踏み切り → 頂点 → 着地 → 沈み込み → 立ち直り）。0〜44F | 高さ (Y) の動きを残す |
| `gareth_test_punch` | 右ストレート（構え → 引き → 打ち抜き 3F → 止め → 構え）。0〜26F | 1 回再生・前後の移動は体に焼き込む |

キーポーズの確認図：[jump](preview/gareth_test_jump_keys.svg) / [punch](preview/gareth_test_punch_keys.svg)
（図はダミーの骨格で作ったもの。体格が違っても動きは同じになる）

## 1. キーポーズの FBX を作る（Blender）

入力は Cascadeur 用に整えたガレスの FBX（骨の名前が Mixamo 式、T ポーズ、実寸）。
フィナの `fina_cascadeur.fbx` と同じ形式。まだ無ければ、先に `Docs/tools/export_cascadeur_rig.py` と同じ要領でガレス版を作る。

```bat
blender -b -P cascadeur\gareth_test\make_test_motion.py -- ^
  --input  D:\HELLEDEN\Cascadeur\rigs\gareth_cascadeur.fbx ^
  --outdir D:\HELLEDEN\Cascadeur\export\gareth_test
```

できるもの（クリップごと）：

| ファイル | 中身 |
|---|---|
| `<clip>_keys.fbx` | キーポーズだけのアニメーション（メッシュなし）。キーの間は直前のポーズのまま止まっている |
| `<clip>_keys.svg` | キーポーズの横・正面の棒人間図。Cascadeur に入れる前にブラウザで確認する |
| `<clip>_keys.txt` | キーのフレーム番号とポーズ名 |

骨が Mixamo 式でないと、足りない骨の名前と骨の一覧を出して止まる。

## 2. Cascadeur で仕上げる

1. リグ付きのガレスのシーン（`Cascadeur/scenes/gareth_base.casc`）を複製して開く。
   まだ無ければ、Cascadeur.md の「2. 読み込んでリグを付ける」をガレスの FBX で行う（Rig mode を先に ON、テンプレートは `Mixamo_Namespace_Template_New`、Character mirror plane は X、Create autoposing を ON）
2. File > Import > FBX Animation で `<clip>_keys.fbx` を読み込む。fps は 30
3. キーを `_keys.txt` のフレームだけにする。ステップ状のアニメーションなので、Animation Unbaking を使うと、ポーズが切り替わるフレームがそのままキーになる。手で行う場合は、`_keys.txt` 以外のフレームのキーを消す
4. 補間を作る：
   - **jump**：踏み切り（12F）〜着地（28F）の区間は AutoPhysics に任せる（放物線と空中の回転が物理的に正しくなる）。0〜12F と 28〜44F は Inbetweening で埋める
   - **punch**：区間をすべて Inbetweening で埋め、AutoPhysics で重心のぶれを直す。打ち抜き（6→9F）は 3 フレームのまま縮めない
5. 足が滑る・浮く所は、接地（Fulcrum）を確認する。Secondary Motion で着地の沈みや、打ち終わりの揺れ戻しを足す
6. File > Export > FBX Animation で書き出す。ファイル名は `_keys` を外して **`gareth_test_jump.fbx` / `gareth_test_punch.fbx`**、置き場は `Assets/Motions/Cascadeur/`
7. 名前の確認と取り込み：

```bat
python -m cascadeur_session check-names D:\HELLEDEN\Assets\Motions\Cascadeur
```

Unity でメニュー **HELLEDEN > Player > Import Cascadeur Motions** を実行し、ゲーム内で再生する。

比較のために、Cascadeur で手を入れる前（`_keys.fbx` をそのまま Unity に入れたもの）と後を並べて撮っておくと、Cascadeur の効果が分かる。

## 確認済みのこと・まだのこと

確認済み（Blender 5.1、ダミーの Mixamo 骨格。身長 1.282m と 1.9m）：`test/verify_export.py` で以下をすべて確認した。

- 書き出した FBX を読み直しても、骨の名前・本数・T ポーズが元と同じ
- 各キーで、腰の高さと足首の位置がポーズ定義どおり（ずれ 0.1% 以内）
- キーの間は直前のポーズのまま止まっている

```bat
blender -b -P cascadeur\gareth_test\test\make_dummy_rig.py -- dummy.fbx 1.282
blender -b -P cascadeur\gareth_test\make_test_motion.py -- --input dummy.fbx --outdir out
blender -b -P cascadeur\gareth_test\test\verify_export.py -- dummy.fbx out
```

まだ：

- ガレス本体の FBX では試していない（このリポジトリにモデルが無いため）
- Cascadeur での読み込み〜書き出し（手順 2）は試していない。File > Import > FBX Animation や Animation Unbaking の正確なメニュー名は、Cascadeur のバージョンで違うことがある
- Cascadeur 内のアニメーション読み込みはスクリプトサーバーから自動化できていない。`python -m cascadeur_session run-file snippets\probe_api.py` の結果に、アニメーション読み込みに使えそうな呼び出しがあれば、手順 2 の 2〜3 を自動化できる

## ポーズを変えるには

`make_test_motion.py` の `CLIPS` を編集する。向きは骨の軸ではなく、キャラクターの「前・上・左」で書く。

- 長さの単位は「腰の高さ」（1.0 = 立った時の腰の高さ）
- 角度は度
- 足は足首の位置を指定すると、膝は自動で正面側に曲がる
- 腕は上腕と前腕の向きで指定する。基準は胸の向き。`"space": "world"` を付けると、体のひねりに関係なく地面に対する向きになる（パンチの打ち抜きで使用）
