# 魔法陣の玉とビーム（Unity 用）

`../magic_circle.html` をブラウザで開くと、撃ち方 × 属性の組み合わせを確認できます。
このファイルは `../tools/export_unity.mjs` が自動生成します。

## 仕組み

- `MagicCircleRig` が、魔法陣（外の輪・内の輪・六芒星・ルーン・中心の光）・玉 8 個（尾つき）・ビームを組み立てます。
- クリップはそれらの位置・回転・大きさだけを動かします（大きさ 0 のときは見えません）。属性は同じクリップのまま、色と味付けで出し分けます。
- 原点は術者の足元、+Z が正面です。術者の子に置くか、撃つ位置・向きに合わせて置いてください。
- 撃つ瞬間などに **On Motion Event** がイベント名付きで呼ばれます。玉が複数ある撃ち方は `Fire:2`・`Impact:5` のように玉の番号が付きます。
  `GetOrb(番号)` でその玉の Transform が取れるので、当たり判定や着弾エフェクトの位置に使えます。ビームは `BeamTransform`（付け根。+Z 方向へ伸びる）。

## 使い方

1. `MagicCircleRig.cs` と `Clips` フォルダを Assets に置く。
2. 空の GameObject に `MagicCircleRig` を付ける（Animator も自動で付きます）。
3. **Clips** に使う撃ち方のクリップを入れ、**Element** で属性を選ぶ。
4. `Cast("Beam")` や `Cast("Orb_Triple", MagicCircleRig.Element.Ice)` のように呼ぶと、その撃ち方を最初から再生します。
   **Play On Start** をオンにすると、始まったときに最初のクリップを再生します（確認用）。

## 撃ち方

| クリップ | 長さ | 内容 | イベント |
|---|---|---|---|
| MagicCircle_Orb_Single | 2秒 | 前に立つ魔法陣の中心に玉が生まれ、正面へ1発（約13m・0.55秒） | Appear（0秒）、Charge（0.4秒）、Fire:0（0.9秒）、Impact:0（1.45秒）、Vanish（1.9秒） |
| MagicCircle_Orb_Triple | 2.6秒 | 輪の上に3つの玉が並び、順に扇形（左右12°）へ撃つ | Appear（0秒）、Charge（0.4秒）、Fire:0（1秒）、Fire:1（1.15秒）、Fire:2（1.3秒）、Impact:0（1.55秒）、Impact:1（1.7秒）、Impact:2（1.85秒）、Vanish（2.5秒） |
| MagicCircle_Orb_Barrage | 3.2秒 | 輪の周り8か所から0.2秒おきに連射（少し中心へ寄りながら約12m） | Appear（0秒）、Charge（0.4秒）、Fire:0（0.9秒）、Fire:1（1.1秒）、Fire:2（1.3秒）、Fire:3（1.5秒）、Fire:4（1.7秒）、Fire:5（1.9秒）、Fire:6（2.1秒）、Fire:7（2.3秒）、Impact:0（1.4秒）、Impact:1（1.6秒）、Impact:2（1.8秒）、Impact:3（2秒）、Impact:4（2.2秒）、Impact:5（2.4秒）、Impact:6（2.6秒）、Impact:7（2.8秒）、Vanish（3.15秒） |
| MagicCircle_Orb_Homing | 3.2秒 | 6つの玉が魔法陣の周りを回り、いっせいに外へふくらんでから前方12m の一点へ曲がって集まる | Appear（0秒）、Charge（0.4秒）、Fire（1.4秒）、Impact:0（2.2秒）、Impact:1（2.25秒）、Impact:2（2.3秒）、Impact:3（2.35秒）、Impact:4（2.4秒）、Impact:5（2.45秒）、Vanish（3秒） |
| MagicCircle_Beam | 3秒 | 溜めてから、太さ0.55m・長さ20m のビームを1.4秒撃ち続ける | Appear（0秒）、Charge（0.4秒）、BeamStart（1秒）、BeamEnd（2.4秒）、Vanish（2.9秒） |
| MagicCircle_Beam_Sweep | 3.6秒 | ビームを左40°から右40°へなぎ払う（魔法陣も少し向きを変える） | Appear（0秒）、Charge（0.4秒）、BeamStart（1秒）、BeamEnd（2.8秒）、Vanish（3.5秒） |
| MagicCircle_Pillar | 2.6秒 | 前方3m の地面に魔法陣が広がり、光の柱（高さ7m・太さ1.1m）が噴き上がる | Appear（0秒）、Charge（0.35秒）、PillarStart（1秒）、PillarEnd（1.8秒）、Vanish（2.5秒） |
| MagicCircle_Rain | 3.6秒 | 前方6m・高さ6m に魔法陣が現れ、玉が0.22秒おきに8発降り注ぐ | Appear（0秒）、Charge（0.4秒）、Fire:0（1秒）、Fire:1（1.22秒）、Fire:2（1.44秒）、Fire:3（1.66秒）、Fire:4（1.88秒）、Fire:5（2.1秒）、Fire:6（2.32秒）、Fire:7（2.54秒）、Impact:0（1.35秒）、Impact:1（1.57秒）、Impact:2（1.79秒）、Impact:3（2.01秒）、Impact:4（2.23秒）、Impact:5（2.45秒）、Impact:6（2.67秒）、Impact:7（2.89秒）、Vanish（3.5秒） |

## 属性

| 属性（Element） | 色 | 味付け |
|---|---|---|
| Fire（炎） | #f97316 | 玉がゆらめき、尾が赤く伸びる |
| Ice（氷） | #38bdf8 | 玉がとげのある結晶で回転する |
| Thunder（雷） | #facc15 | ビームと玉がちらつき、稲妻のように揺れる |
| Wind（風） | #4ade80 | 玉が渦を巻いて速く回る |
| Water（水） | #3b82f6 | 玉がぷるぷると伸び縮みする |
| Earth（土） | #a16207 | 玉が岩のように転がる（光は控えめ） |
| Light（光） | #fde047 | まぶしく、輪がきらめく |
| Dark（闇） | #7c3aed | 中心が暗く、紫のふちが揺らぐ |

## 作り直し方

`../magic_circle.html` の `==POSE-BEGIN==`〜`==POSE-END==` に撃ち方の定義があります。編集したら次を実行します（Node.js のみ必要）。

```
node <magic_circle フォルダ>/tools/export_unity.mjs
```

## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面や見た目を教えてください。
- 色の加算表示には、パーティクル用のシェーダー（URP の Particles/Unlit、ビルトインの Legacy Shaders/Particles/Additive）を順に探して使います。ビルドで削られる場合は Always Included Shaders に追加してください。
