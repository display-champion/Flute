# Cascadeur でモーションを作る

> HELLEDEN プロジェクトの `D:\HELLEDEN\Docs\Cascadeur.md` の写し（2026-09-29 時点）。
> 文中の相対パス（`Cascadeur/rigs/...`、`Assets/...` など）は HELLEDEN プロジェクト基準。

斬り・ジャンプ・パンチなどを、物理的に自然な動き（重心・慣性・接地）で作るための手順。

## 用意済みのもの

| もの | 場所 |
|---|---|
| フィナの体（Cascadeur 用） | `Cascadeur/rigs/fina_cascadeur.fbx` |
| その作り直し | `blender -b -P Docs/tools/export_cascadeur_rig.py`（元は `sena2_fixed.fbx`） |
| シーン保存先 | `Cascadeur/scenes/` |
| 完成 FBX の置き場 | `Assets/Motions/Cascadeur/` |
| Unity への取り込み | メニュー **HELLEDEN > Player > Import Cascadeur Motions** |

`fina_cascadeur.fbx` の中身：
- 骨の名前は Mixamo 式（`mixamorig:Hips` など）。Cascadeur が自動で認識する
- 身長はゲーム内と同じ 1.282m（物理計算を実寸で行うため）
- T ポーズ、テクスチャ入り、テイクは無し

## 1. インストール（ご自身で）

1. https://cascadeur.com でアカウントを作り、Windows 版をダウンロードしてインストールする
2. 無料版（Free）でも作れる。書き出しの制限（FBX 1回あたりのフレーム数など）はバージョンで変わるので、起動時の案内で確認する。商用で売るなら Indie ライセンス（年収の条件あり）が必要

## 2. フィナを読み込んでリグを付ける（初回だけ）

1. File > Import > FBX Model で `Cascadeur/rigs/fina_cascadeur.fbx` を開く（T ポーズで出ること）
2. ツールバーの **Rig mode** を ON にする（先に入らないと Quick Rigging Tool がエラーになる）
3. 左パネルの Quick rigging tool を開き、テンプレート `Mixamo_Namespace_Template_New` を読み込む → 「fully recognized」と出る → Add rig elements
4. Character mirror plane を **X** に、Create autoposing を ON にして Generate rig
5. `Cascadeur/scenes/fina_base.casc` として保存しておき、以後はこれを複製して使う

進み具合とつまずいた所は [Cascadeur_引継ぎ.md](Cascadeur_引継ぎ.md)。

## 3. 動きを作る

キーは少なく置き、あとは Cascadeur に補ってもらう。

- **キーポーズだけ置く**：たとえば斬りなら、構え → 振りかぶり → 振り抜き → 止め → 戻り の 5 枚
- **AutoPhysics** を ON：重心の軌道・足の接地を物理的に正しく直してくれる。ジャンプの放物線はこれに任せる
- **AutoPosing**：手先・足先を動かすと、体の残りを自然な姿勢に合わせてくれる
- **Secondary Motion**：振り抜いたあとの揺れ戻しや、着地の沈みを追加する
- 目安は 30fps。攻撃の振り抜きは 2〜4 フレームで一気に、溜めと止めは長めに取る

## 4. 書き出して Unity へ

1. File > Export > FBX Animation（メッシュなし）で書き出す
2. ファイル名がそのままクリップ名になる。名前で扱いが変わる：
   - `jump` `leap` `dive` `flip` `vault` を含む → 高さ（Y）の動きを残す
   - `idle` `walk` `run` `wait` などを含む → ループ再生
   - それ以外（攻撃など）→ 1 回再生、前後の移動は体に焼き込む
   - 例：`fina_slash_A.fbx`、`fina_jump_start.fbx`、`fina_punch_straight.fbx`
3. `Assets/Motions/Cascadeur/` に置き、**HELLEDEN > Player > Import Cascadeur Motions** を実行する
4. Humanoid として取り込まれるので、フィナ以外の人型（アスカなど）にもそのまま載る
5. 使い始めたら、モーション一覧.xlsx の OWN に説明を追加する
