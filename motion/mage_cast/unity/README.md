# 魔術師の術発動モーション（Unity 用）

`../mage_cast.html` と同じ「両腕を掲げてゆらゆらさせた後、胸の前へ振り下ろして術を発動する」動きを Unity で再生するためのファイルです。

| ファイル | 内容 |
|---|---|
| `MageCast.anim` | AnimationClip（Generic、1回 5 秒、30関節＋魔力の玉） |
| `MageRigBones.cs` | クリップに対応する関節階層・初期姿勢・見た目の指定（自動生成） |
| `MageRig.cs` | 魔術師を組み立ててクリップを再生するコンポーネント |

動きの流れ（秒は速度1のとき）:

| 時刻 | 動き |
|---|---|
| 0〜0.5 秒 | 待機 |
| 0.5〜1.2 秒 | 両腕を頭上へ掲げる（V字） |
| 1.2〜3.2 秒 | 頭上でゆらゆら（両手が左右に揺れ、手首が波打つ）。両手の間に魔力の玉が育つ |
| 3.2〜3.55 秒 | さらに振りかぶる（上体を反らし、左足を踏み出し始める） |
| 3.55〜3.8 秒 | 左足を踏み込みつつ、腕を胸の前へ加速して振り下ろす |
| 3.8 秒 | 術発動：手のひらを前へ向けて押し出し、玉が前方へ飛んでいく |
| 3.8〜4.3 秒 | 押し出したまま |
| 4.3〜5.0 秒 | 待機へ戻る |

## 使い方

1. この3ファイルを Unity プロジェクトの `Assets/` 以下（例: `Assets/MageCast/`）にコピーする。
2. シーンに空の GameObject を作り、`MageRig` コンポーネントを追加する（Animator も自動で付きます）。
3. `MageRig` の **Clip** に `MageCast.anim` をドラッグして再生する。

AnimatorController は不要です（Playables API で直接再生します）。魔術師は GameObject の +Z 方向へ術を放ちます。

### MageRig の設定

- **Speed**: 再生速度（0.1〜2）
- **Loop**: オフにすると1回で止まる。`Cast()` を呼ぶと最初からもう一度再生します
- **Orb Light**: 魔力の玉に点光源を付ける（玉の大きさに合わせて明るさが変わる）
- **On Gather Start**: 両腕を掲げて魔力を溜め始めた瞬間に呼ばれるイベント
- **On Cast**: 胸の前へ振り下ろして術が発動した瞬間に呼ばれるイベント（ここで魔法のエフェクトや弾を出す）
- **Body / Hat / Accent / Magic Color**: 色

## 関節階層

関節名は Unity の Humanoid のボーン名に合わせています。

```
Hips
├─ Spine ─ Chest
│          ├─ Neck ─ Head（帽子付き）─ LeftEye / RightEye
│          ├─ LeftUpperArm ─ LeftLowerArm ─ LeftHand ─ LeftHandTip ─ LeftFinger1〜3
│          └─ RightUpperArm ─（同上）
├─ LeftUpperLeg ─ LeftLowerLeg ─ LeftFoot ─ LeftToes
└─ RightUpperLeg ─（同上）
Orb（魔力の玉。スケールで大きさが変わり、0 のときは見えない）
```

各関節の +Y 軸が次の関節を向いています（Head は +Y が頭頂、+Z が顔の向き）。
クリップ自体は Generic なので、別の人型モデルにそのまま使うことはできません。

## 作り直し方

動きは `../mage_cast.html` 内の `==POSE-BEGIN==` 〜 `==POSE-END==` の計算から作っています。
そこを編集したら、リポジトリのルートで次を実行すると `MageCast.anim` と `MageRigBones.cs` が作り直されます（Node.js のみ必要）。

```
node motion/mage_cast/tools/export_unity.mjs
```

## 注意

- ビルドでシェーダーが削られて表示されない場合は、Project Settings > Graphics の Always Included Shaders に使っているシェーダーを追加してください。
