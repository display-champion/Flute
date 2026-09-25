# 獣走りモーション（Unity 用）

`../beast_run.html` と同じ「獣系の両腕を左右に構えて走ってくる棒人間」を Unity で再生するためのファイルです。

| ファイル | 内容 |
|---|---|
| `BeastRun.anim` | ループする AnimationClip（Generic、1周期 0.69 秒、49関節の位置と回転） |
| `BeastRigBones.cs` | クリップに対応する関節階層（自動生成） |
| `BeastRig.cs` | 関節階層と棒人間の見た目を組み立てて、クリップを再生するコンポーネント |

## 使い方

1. この3ファイルを Unity プロジェクトの `Assets/` 以下（例: `Assets/BeastRun/`）にコピーする。
2. シーンに空の GameObject を作り、`BeastRig` コンポーネントを追加する（Animator も自動で付きます）。
3. `BeastRig` の **Clip** に `BeastRun.anim` をドラッグして再生する。

AnimatorController は不要です（Playables API で直接再生します）。

### BeastRig の設定

- **Speed**: 再生速度（0.1〜2）
- **Approach**: オンで前方（GameObject の +Z）へ走って迫ってくる。オフならその場で走る
- **Approach Distance**: この距離を走るとスタート地点に戻る
- **Body Color / Accent Color / Line Width**: 見た目。爪の先と目がアクセント色

カメラは GameObject の正面（+Z 側）に置いて、こちら向きにすると「走ってくる」構図になります。

## 関節階層

```
Hips
├─ Spine ─ Chest
│          ├─ Neck ─ Head ─ Eye_L / Eye_R
│          ├─ Shoulder_L ─ Elbow_L ─ Wrist_L ─ ClawL1〜4 (_a/_b/_c), ThumbL (_a/_b)
│          └─ Shoulder_R ─ （同上）
├─ Hip_L ─ Knee_L ─ Ankle_L ─ Toe_L
└─ Hip_R ─ （同上）
```

各関節の +Y 軸が次の関節を向いているので、骨の向きに沿って自前のモデルを子に付けることもできます。
Humanoid ではなく Generic なので、別の人型モデルへそのままリターゲットはできません。

## 作り直し方

モーションは `../beast_run.html` 内の `==POSE-BEGIN==` 〜 `==POSE-END==` の計算から作っています。
そこを編集したら、リポジトリのルートで次を実行すると `BeastRun.anim` と `BeastRigBones.cs` が作り直されます（Node.js のみ必要）。

```
node motion/beast_run/tools/export_unity.mjs
```

## 注意

- ビルドでシェーダーが削られて表示されない場合は、**Body/Accent Material Override** に任意のマテリアルを指定してください。
