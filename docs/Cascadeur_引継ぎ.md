# Cascadeur 導入 引継ぎ（2026-09-29 時点）

> HELLEDEN プロジェクトの `D:\HELLEDEN\Docs\Cascadeur_引継ぎ.md` の写し。
> 文中の相対パスは HELLEDEN プロジェクト基準。

目的：斬り・ジャンプ・パンチなど人型モーションを、Cascadeur の物理補助（AutoPhysics / AutoPosing）で自然にする。
手順の正本は [Cascadeur.md](Cascadeur.md)。この資料は「どこまで進んだか」と「次に何をするか」。

## 進み具合

| 手順 | 状態 |
|---|---|
| フィナの体を Cascadeur 用に書き出し | 済 |
| Unity への取り込みメニュー | 済（未コンパイル） |
| Cascadeur のインストール・ログイン | 済（ユーザー。Free 版） |
| フィナを Cascadeur に読み込み | 済 |
| Quick Rigging Tool（Mixamo テンプレート）→ Add rig elements | 済 |
| Generate rig | 済（エラーなし）。見た目の確認はまだ |
| `Cascadeur/scenes/fina_base.casc` として保存 | **未** |
| 最初の1本（斬りなど）を作る → 書き出し → Unity で再生 | **未** |

いま Cascadeur は開いたまま。タブ `*untitled (1)` にリグ付きのフィナがあり、Outliner に `mixamorig:Rig(0)`、`auto_posing(0)` がある。
タブ `untitled` は最初の失敗分（T ポーズではない姿勢で読み込んだもの）なので、保存せずに閉じてよい。

## 作ったファイル

| ファイル | 内容 |
|---|---|
| `Docs/tools/export_cascadeur_rig.py` | sena2_fixed.fbx → `Cascadeur/rigs/fina_cascadeur.fbx`。骨名を Mixamo 式（`mixamorig:`）に変換、身長 1.282m、テイクを外して T ポーズに戻す |
| `Cascadeur/rigs/fina_cascadeur.fbx` | 上の出力（67 骨、テクスチャ入り） |
| `Cascadeur/README.txt` | 作業フォルダの説明（rigs / scenes / export） |
| `Assets/HELLEDEN/Editor/CascadeurImport.cs` | メニュー HELLEDEN > Player > Import Cascadeur Motions。`Assets/Motions/Cascadeur/*.fbx` を MotionLibraryBuilder.ImportFiles で Humanoid 取り込み |
| `Assets/Motions/Cascadeur/` | 完成 FBX の置き場（空） |
| `Docs/Cascadeur.md` | 手順書 |

## 途中で分かったこと（つまずいた所）

1. **テイクを消しても姿勢が残る**：Blender でアクションを削除しても、最後に評価された姿勢がポーズボーンに残る。書き出し前に `pb.matrix_basis.identity()` で T ポーズへ戻す必要があった（スクリプトは修正済み）。
2. **Quick Rigging Tool はリグモードに入ってから使う**：リグモードの外で Add rig elements を押すと、`Rig mode several animationInfo` のエラーが出て、腕（arm_l / arm_r）が見つからないと言われる。ツールバーの **Rig mode**（V 字アイコン）を ON にしてから、左パネルの Quick rigging tool を開く。
3. **左右の対称面は X にする**：既定は Z（前後で対称）だった。フィナは左右が X 軸なので、Character mirror plane を **X** にする（スクリプトでは `set_character_mirror_plane(2)`、2 が YZ 面）。
4. **Create autoposing を ON** にしてから Generate rig を押す。
5. テンプレートは `C:/Program Files/Cascadeur/resources/autorig_templates/Mixamo_Namespace_Template_New.qrigcasc`。骨名が完全一致するので、読み込むと「fully recognized」と出る。
6. fps の警告（Scene 30 / fbx 24）が出るが、読み込むのはリグだけなので影響なし。

## Cascadeur を Python で動かす方法

Cascadeur には、動いているアプリの中で Python を実行するローカルサーバーが付いている。

- 起動：メニュー **Scripts > MCP > Start script server**（Cascadeur を起動するたびに必要）
- 確認：`curl http://127.0.0.1:8765/health`
- 実行：`POST http://127.0.0.1:8765/run`、本文は `{"code": "..."}`。`app`・`scene`・`csc` が使える。print の出力が返ってくる
- `scene` は最初のタブを指したままになることがあるので、`app.current_scene()` を使う
- エラーが返りに出ないことがある。ログは `%LOCALAPPDATA%\Nekki Limited\Cascadeur\logs\cascadeur_log.log`
- 使えた呼び出し：
  - FBX 読み込み：`app.get_tools_manager().get_tool('FbxSceneLoader').get_fbx_loader(app.current_scene()).add_model(path)`
  - リグツール：`app.get_tools_manager().get_tool('RiggingToolWindowTool').editor(app.current_scene())` の `open_quick_rigging_tool()`、`load_template_by_fileName(path)`、`set_character_mirror_plane(n)`、`set_is_create_autoposing(True)`
- 関連スクリプト：`C:/Program Files/Cascadeur/resources/scripts/python/`（`prototypes/qrt_prototypes/create.py`、`rig_mode/`、`test/test_cases/`）
- ボタン操作（Add rig elements、Generate rig、Rig mode）は画面操作で行った。

## 次にやること

1. リグの確認：コントロールポイントをつかんで、手足・腰が自然に動くか、左右が逆になっていないかを見る。生成後は T ポーズから腕が下がった姿勢に見えたので、これが AutoPosing の標準姿勢なのかも確かめる。
2. `Cascadeur/scenes/fina_base.casc` として保存する（以後はこれを複製して使う）。
3. 最初の1本を作る。候補はフィナの通常攻撃の斬り（`fina_slash_A`）。キーポーズは 構え → 振りかぶり → 振り抜き（2〜4F）→ 止め → 戻り。AutoPhysics を ON にする。
4. File > Export > FBX Animation で書き出し、`Assets/Motions/Cascadeur/` に置く。Unity でメニューを実行し（CascadeurImport.cs の初コンパイルもここで確認）、ゲーム内で再生する。
5. 書き出す前後を撮影して見比べる。その後、モーション一覧.xlsx の OWN に追加する。

## 注意

- Free 版は書き出しに制限がある場合がある。書き出しで止められたら、そこでユーザーに確認する。
- 他のセッションが Unity を同時に使っていることがある。Unity のバッチは `Docs/tools/unity_batch.sh` から実行し、起動前に Unity.exe が動いていないか確かめる。
