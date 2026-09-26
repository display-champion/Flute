# 魔法陣から属性の玉・ビームを撃ち出すモーション 作業経過

ユーザー指示：「魔法陣から各属性の玉やビームを打ち出すモーションを何個か作成してください」

## 方針

- 魔法陣・玉・ビームそのものの動き（エフェクトのモーション）として作る。術者の体の動きは含めない（術者は魔術師の術発動モーションなどと組み合わせる）
- 撃ち方 8 種類 × 属性 8 種類（炎・氷・雷・風・水・土・光・闇）。クリップは撃ち方ごとに作り、属性は色と味付け（ちらつき・回転・稲妻の揺れ）で出し分ける
- Unity：`MagicCircleRig.cs` が魔法陣（輪・ルーン・六芒星・中心の光）・玉（8個、尾つき）・ビームを組み立て、Generic クリップで動かす。撃つ・着弾などは AnimationEvent（OnMotionEvent）→ UnityEvent
- 作業ファイル：`magic_circle.html`（確認用・定義）＋ `tools/export_unity.mjs`。納品は zip（展開先 `D:\HELLEDEN\Assets\HELLEDEN\Animation`）、git からは作業ファイルを消してこのファイルだけ残す

## 撃ち方（クリップ）

| クリップ | 内容 | 状態 |
|---|---|---|
| Orb_Single | 前に立つ魔法陣から玉を1発 | 納品済み |
| Orb_Triple | 3発を扇形に順に撃つ | 納品済み |
| Orb_Barrage | 輪の周りから8発を連射 | 納品済み |
| Orb_Homing | 玉が魔法陣の周りを回ってから、曲がりながら一点へ集まる | 納品済み |
| Beam | 溜めてからビームを撃ち続ける | 納品済み |
| Beam_Sweep | ビームで横になぎ払う | 納品済み |
| Pillar | 足元（前方）の魔法陣から光の柱が噴き上がる | 納品済み |
| Rain | 頭上の魔法陣から玉が降り注ぐ | 納品済み |

## 作業ログ

- 開始
- 8 種類の撃ち方を `magic_circle.html` に定義。確認用の画面で 8 属性すべて表示を確認
- Unity 出力：クリップ 8 本（計約 5MB）。HTML の動きとのずれは最大 1.98mm（別途 Python で .anim を読み直して検算：最大 1.63mm、イベント・長さ・終わりに全部消えることも確認）
  - 玉が撃たれる瞬間に大きさが跳ねていた（撃つ前の脈打ちが急に消える）のを、撃つ 0.15 秒前から脈打ちを弱めてつなげて解消（キーの細かさ 240/秒 → 20/秒、約 20MB → 5MB）
- `MagicCircleRig.cs`：魔法陣・玉 8 個（尾つき）・ビームをメッシュから組み立て、Playables で再生。`Cast("Beam", Element.Ice)`、イベントは OnMotionEvent → UnityEvent。Unity での動作は未確認
- 納品：`HELLEDEN_MagicCircle.zip`（`D:\HELLEDEN\Assets\HELLEDEN\Animation` に展開 → `magic_circle/` ができる）
- 作業ファイル（`magic_circle.html`・`tools/`・`unity/`）は git から削除。全部そろった状態はコミット `6f5f277` で取り出せる
  （例：`git checkout 6f5f277 -- motion/magic_circle`）
