# 蜂の針攻撃モーション（Unity 用）

`../bee_sting.html` と同じ「蜂が飛びながらしっぽの針で攻撃してくる」動きを Unity で再生するためのファイルです。

| ファイル | 内容 |
|---|---|
| `BeeSting.anim` | ループする AnimationClip（Generic、1サイクル 3 秒、39関節） |
| `BeeRigBones.cs` | クリップに対応する関節階層・初期姿勢・見た目の指定（自動生成） |
| `BeeRig.cs` | 蜂を組み立ててクリップを再生するコンポーネント |

1サイクルの流れ（秒は速度1のとき）:

| 時刻 | 動き |
|---|---|
| 0〜1.2 秒 | ホバリング（ゆらゆら浮かぶ） |
| 1.2〜1.74 秒 | 構え：後ろへ引いて上昇し、腹を体の下から前へ丸める |
| 1.74〜1.98 秒 | 突き刺し：前へ突進して針を突き出す（1.98 秒で最大） |
| 1.98〜2.2 秒 | 刺したまま小刻みに震える |
| 2.2〜3.0 秒 | 離れてホバリングに戻る |

羽ばたきは 12 回/秒です。

## 使い方

1. この3ファイルを Unity プロジェクトの `Assets/` 以下（例: `Assets/BeeSting/`）にコピーする。
2. シーンに空の GameObject を作り、`BeeRig` コンポーネントを追加する（Animator も自動で付きます）。
3. `BeeRig` の **Clip** に `BeeSting.anim` をドラッグして再生する。

AnimatorController は不要です（Playables API で直接再生します）。
蜂は GameObject の位置から高さ 1.35 m のところに浮かび、+Z 方向へ攻撃します。
カメラを GameObject の正面（+Z 側、高さ 1.3 m くらい）に置いてこちらに向けると、正面から刺しにくる構図になります。

### BeeRig の設定

- **Speed**: 再生速度（0.05〜2）。遅くすると羽ばたきまでよく見えます
- **Approach**: オンで前方（+Z）へ飛んで迫ってくる。オフならその場で攻撃を繰り返す
- **Approach Speed / Approach Distance**: 迫ってくる速さと、スタート地点に戻るまでの距離
- **On Sting**: 針が最も突き出た瞬間に呼ばれるイベント（ダメージ判定などに）
- **Black / Yellow / Amber / Accent / Wing**: 色

## 関節階層

```
Body（胸）
├─ Head ─ Eye_L / Eye_R, Antenna_L_a ─ _b ─ _c, Antenna_R_a ─ _b ─ _c
├─ Abdomen_1 ─ Abdomen_2 ─ Abdomen_3 ─ Abdomen_4 ─ Abdomen_5 ─ Stinger ─ StingerTip
├─ Wing_FL / Wing_FR / Wing_HL / Wing_HR（前羽・後羽）
└─ Leg_L1〜L3 / Leg_R1〜R3（各 _a ─ _b ─ _c）
```

各関節の +Y 軸が次の関節（羽は先端方向）を向いているので、自前のモデルを子に付けて差し替えることもできます。
Humanoid ではなく Generic です。

## 作り直し方

動きは `../bee_sting.html` 内の `==POSE-BEGIN==` 〜 `==POSE-END==` の計算から作っています。
そこを編集したら、リポジトリのルートで次を実行すると `BeeSting.anim` と `BeeRigBones.cs` が作り直されます（Node.js のみ必要）。

```
node motion/bee_sting/tools/export_unity.mjs
```

## 注意

- ビルドでシェーダーが削られて表示されない場合は、Project Settings > Graphics の Always Included Shaders に使っているシェーダーを追加してください。
