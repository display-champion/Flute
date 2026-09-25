# ダンジョン雑魚モーション 作業経過

`バトル一覧.xlsx` の「ダンジョン雑魚」シート（EN-01〜EN-56）の「行動・攻撃」欄から、必要なモーションを作る作業の記録。
途中で止まっても、このファイルを読めば続きから再開できるようにしておく。

## 決まっていること（ユーザー回答）

1. 名前に「人」を含む敵は人型、それ以外は人型以外として作る
2. 人型以外は「体全体を動かす」方式でよい（位置・回転・伸び縮みだけ。骨は使わない）
3. 既存スクリプト（MonsterController / EnemyShoulderCharge / DemonFlameCaster）との連携は一旦考えない
4. 作る順番は **案A：序章・第1章から**
5. 未作成モデルの敵は、見た目を予想して作る
6. 納品は今まで通り：確認用 HTML ＋ Unity 用（.anim ＋ C#）を zip で渡し、git には残さない
   （作業中は中断に備えて git にコミットしておき、納品時に作業ファイルを消して、この PROGRESS.md だけ残す）

## 作り方（全モーション共通の約束）

- Unity の構成：`敵の本体（Animator ＋ EnemyMotion）` → `Motion`（クリップが動かす） → `モデル`
  - クリップは `Motion` の localPosition / localRotation / localScale だけを動かすので、どのモデルにも付けられる
  - モデルは `Motion` の子に、足元が原点、+Z が正面になるよう置く（浮く敵は下の「軸の高さ」に体の中心を合わせる）
- 回転や伸び縮みの中心（軸）は体の種類ごとに決める。例：キノコは足元、岩ダンゴは球の中心、ナメクジはしっぽ
- 攻撃のうち短い飛びかかり（射程 1m 前後）は、クリップ内で前に出て戻る（その場で完結）
- 長い突進・転がり（6m 以上）は、クリップはその場で「構え → 突進中の姿勢 → 止まる」だけを持ち、実際の移動はゲーム側が行う
- 攻撃が当たる瞬間などは AnimationEvent（関数名 `OnMotionEvent`、文字列でイベント名）を入れ、EnemyMotion から UnityEvent で受け取れるようにする
- 実装：`dungeon_minor.html` の `==POSE-BEGIN==`〜`==POSE-END==` にクリップ定義を書き、`tools/export_unity.mjs` で .anim を生成する（これまでの3モーションと同じ仕組み）

## 人型／人型以外の振り分け（名前に「人」を含むか）

- 人型：EN-09 溺れた村人、EN-12 狼の獣人、EN-13 狼の獣人（弓）、EN-33 罪人の影、EN-54 光の番人
- それ以外はすべて人型以外（体全体を動かす）

## 進み具合

### 案A：序章・第1章（今回の対象）

| ID | 名前 | 体の種類 | 作るクリップ | 状態 |
|---|---|---|---|---|
| EN-01 | 胞子キノコ | キノコ | 待機・移動・飛びかかり・被弾・死亡（胞子が弾ける） | 完了（納品済み） |
| EN-02 | 巣守りのバチ | ハチ | 待機・移動・刺す・突進・被弾・死亡 | 完了（納品済み） |
| EN-03 | 妖精の灯 | 光の妖精（未作成モデル） | 待機・逃げる・眠り粉を撒く・被弾・死亡 | 完了（納品済み） |
| EN-04 | 輪の茸番 | キノコ | キノコ共通＋踏みつけ（硬直0.9秒） | 完了（納品済み） |
| EN-16 | 洞窟茸 | キノコ | キノコ共通 | 完了（納品済み） |
| EN-17 | 岩ダンゴ | 岩の子 | 待機・移動・転がり・被弾・死亡 | 完了（納品済み） |
| EN-42 | 水路ナメクジ | ナメクジ（未作成モデル） | 待機・這う・噛みつき・被弾・死亡 | 完了（納品済み） |
| EN-43 | 苔キノコ | キノコ | キノコ共通 | 完了（納品済み） |

### 残り全部（ユーザー指示：途中で止めずに全モンスター分を作る）

体の種類（Body）ごとに共通の待機・移動・被弾・死亡を作り、攻撃などの特別な動きを足す。
人型（名前に「人」）の5体は、別の仕組み（下の「人型」）で作る。

| ID | 名前 | 体の種類 | 作るクリップ | 状態 |
|---|---|---|---|---|
| EN-05 | 沼の魔物 | Creature | Idle / Move / Burrow（泥に潜る）/ Emerge_Bite（飛び出して噛む）/ Hit / Death | 未着手 |
| EN-06 | 毒吐き草 | Plant | Idle / Attack_Spit / Hit / Death（動かない） | 未着手 |
| EN-07 | 毒羽のバチ | Bee | Idle / Move / Attack_Sting / Hit / Death | 未着手 |
| EN-08 | 大蛍 | Bee | Idle / Move / Attack_Ram（体当たり）/ Hit / Death | 未着手 |
| EN-10 | 根喰い虫の幼虫 | Creature | Idle / Move / Emerge_Bite / Attack_Bite / Hit / Death | 未着手 |
| EN-11 | 世界樹の瘤 | Plant | Dormant（擬態）/ WakeUp / Idle / Attack_Slam / Hit / Death | 未着手 |
| EN-14 | 翼の悪魔（小） | Flyer | Idle / Move / Attack_Dive（急降下→着地1秒→飛び立つ）/ Hit / Death | 未着手 |
| EN-15 | 岩の魔物 | RockBall（1.67倍） | Idle / Move / Attack_Roll_Long（起き上がり2秒）/ Hit / Death | 未着手 |
| EN-18 | 石くれ人形 | Upright | Idle / Move / Attack_HeavySlam（予備動作0.8秒）/ Hit / Death | 未着手 |
| EN-19 | 洞の小蜘蛛 | Spider | Idle / Move / Descend（天井から降りる）/ Attack_Web / Hit / Death | 未着手 |
| EN-20 | 骨の小竜 | Flyer | Idle / Move / Attack_GlideBite / Hit / Death_Collapse / Reassemble | 未着手 |
| EN-21 | 炎の魔物 | Creature | Idle / Move / Attack_Tackle / Hit / Death | 未着手 |
| EN-22 | 火蜥蜴 | Creature | Idle / Move / Attack_Breath（1秒）/ Hit / Death | 未着手 |
| EN-23 | 鉄殻虫 | Creature | Idle / Move / Attack_Bite / Flipped（ひっくり返る）/ Hit / Death | 未着手 |
| EN-24 | 湯煙の精 | Phantom | Idle / Move / Appear / Attack_Blow / Vanish / Hit / Death | 未着手 |
| EN-25 | 湯あたりガエル | Creature | Idle / Move / Attack_Pounce（大跳躍）/ Hit / Death | 未着手 |
| EN-26 | 巡回の検品機 | Clockwork | Idle / Move / Alert（見つけた） | 未着手 |
| EN-27 | 天の番兵 | Upright | Idle / Move / Attack_Swing（警棒）/ Hit / Death | 未着手 |
| EN-28 | 仕分けの手 | Upright | Idle / Move / Attack_GrabThrow（予備動作0.8秒）/ Hit / Death | 未着手 |
| EN-29 | 水路の清掃機 | Whale | Idle / Move / Attack_LeapTackle / Hit / Death | 未着手 |
| EN-30 | 歯車の子 | Clockwork | Idle / Move / Attack_SpinJump / Hit / Death | 未着手 |
| EN-31 | 迷い羽根 | Bee | Idle / Move_Flutter / Attack_Slash / Hit / Death | 未着手 |
| EN-32 | 監督の魔物 | Creature | Idle / Move / Attack_Whip（前方120°の横なぎ）/ Hit / Death | 未着手 |
| EN-34 | 炎喰いの子 | Creature | Idle / Move / Attack_Bite / Grow（大きくなる）/ Hit / Death | 未着手 |
| EN-35 | 冷えた溶岩の殻 | RockBall（1.67倍） | Idle / Move / Attack_Roll_Long / Hit / Death_Shatter（割れる） | 未着手 |
| EN-36 | 看守の犬 | Hound | Idle / Move / Sniff / Bark / Attack_Bite / Hit / Death | 未着手 |
| EN-37 | 鎖の魂 | Phantom | Dormant / WakeUp / Idle / Move / Attack_ChainLash / Hit / Death | 未着手 |
| EN-38 | 無音の影 | Phantom | Idle / Move / Attack_Strike / Hit / Death | 未着手 |
| EN-39 | 聖堂騎士 | Upright | Idle / Move / Attack_Combo2（剣の2連撃）/ Hit / Death | 未着手 |
| EN-40 | 動く鎧 | Upright | Idle / Move / Attack_HeavySlam / Hit / Death | 未着手 |
| EN-41 | 書架の魔物 | Clockwork | Idle / Move / Attack_Throw（本を3冊扇形）/ Hit / Death | 未着手 |
| EN-44 | 酔いバチ | Bee | Idle / Move_Drunk / Attack_DoubleSting / Hit / Death | 未着手 |
| EN-45 | 樽の子 | Barrel | Disguise / Reveal / Idle / Move / Attack_Roll / Hit / Death | 未着手 |
| EN-46 | 箱入りの忘れ物 | Box | Disguise / Attack_Bite / Idle / Move / Hit / Death | 未着手 |
| EN-47 | 名を失くした亡者 | Upright | Idle / Move / Attack_Punch / Hit / Death | 未着手 |
| EN-48 | 苔の石像 | Upright | Disguise / Ambush_Punch / Idle / Move / Hit / Death | 未着手 |
| EN-49 | 墓守の鬼火 | Fairy | Idle / Move / Attack_Touch / Hit / Death | 未着手 |
| EN-50 | 墓荒らしの魔物 | Creature | Idle / Move / Attack_Bite / Dig_Escape（穴を掘って逃げる）/ Hit / Death | 未着手 |
| EN-51 | 笑う死者 | Upright | Idle_Laugh / Move / Attack_Grab / Hit / Death_Crumble（花になって崩れる） | 未着手 |
| EN-52 | 侵食の蔦 | Plant | Submerged（地中）/ Attack_Erupt（突き上げ）/ Idle / Hit / Death | 未着手 |
| EN-53 | 庭の番 | Plant | Idle / Move / Attack_Lunge / Hit / Death | 未着手 |
| EN-55 | 刈り込み鋏 | Shears | Idle / Move / Attack_Snip2（はさみ込み2連）/ Hit / Death | 未着手 |
| EN-56 | 受粉の蜂 | Bee | Idle / Move / Attack_Sting / Hit / Death | 未着手 |

名前に「人」を含まないので、聖堂騎士・動く鎧・亡者・死者なども「体全体を動かす」方式（Upright）で作る（ユーザーの決めた振り分けどおり）。

### 人型（名前に「人」を含む5体）

骨を持つ人型（Humanoid）モデルを動かすため、次の仕組みにする：
- 見えない「代理の骨組み（Proxy）」を Generic クリップで動かし、`HumanoidRetarget.cs` が毎フレーム、モデルの Humanoid ボーン（Animator.GetBoneTransform）を代理の骨と同じ向きに回す
- 骨の向きだけを写すので、モデルの骨の軸の向きや体格が違っても使える（ねじれは元のまま）
- 作業ファイル：`dungeon_humanoid.html`（確認用・定義）＋ `tools/export_humanoid.mjs`

| ID | 名前 | 作るクリップ | 状態 |
|---|---|---|---|
| EN-09 | 溺れた村人 | Idle / Move（ゆっくり歩く）/ Attack_Grab（掴んで1.5秒離さない）/ Hit / Death | 未着手 |
| EN-12 | 狼の獣人 | Idle / Move（走る）/ Attack_Punch / Attack_Kick / Howl（吠える）/ Hit / Death | 未着手 |
| EN-13 | 狼の獣人（弓） | Idle / Move_Back（下がる）/ Attack_Bow（矢を撃つ）/ Hit / Death | 未着手 |
| EN-33 | 罪人の影 | Idle / Move / Sink（影に潜る）/ Rise（出てくる）/ Attack_Claw / Hit / Death | 未着手 |
| EN-54 | 光の番人 | Idle / Appear（現れる）/ Attack_Shoot（光の矢）/ Hit / Death | 未着手 |

## 作業ログ

- 作業開始。方針を決めてこのファイルを作成
- `dungeon_minor.html` を作成：案A の 8 体・5 種類の体（Mushroom / Bee / Fairy / RockBall / Slug）・28 クリップを定義し、ブラウザで確認できるようにした
- `tools/export_unity.mjs` を作成し、28 本の .anim を `unity/<体>/` に書き出した（合計約 8.5 MB）
  - 検証：全クリップを YAML として読み直し、キーの間の補間まで含めて元の動きと比べて、ずれは最大 0.33 mm。ループ設定・長さ・イベントも一致
  - 震え（毎秒14〜25回）を含む4本はキーを細かくしている（RATE_OVERRIDE）
- `unity/EnemyMotion.cs`（クリップの切り替え・フェード・自動で待機へ戻る・イベント受け取り）と `unity/README.md`（自動生成）を作成
- **案A 完了・納品**：`HELLEDEN_DungeonMinor_A.zip` を渡した（展開先 `D:\HELLEDEN\Assets\HELLEDEN\Animation`）
  - 作業ファイル一式はコミット `4592ecf` にある（git からは削除済み。続きはここから取り出すか、展開先のフォルダを使う）
  - 取り出し方：`git checkout 4592ecf -- motion/dungeon_minor`

## 次に再開するとき

1. 作業ファイルを戻す：`git checkout 4592ecf -- motion/dungeon_minor`（または展開先の `dungeon_minor` フォルダを持ってくる）
2. `dungeon_minor.html` の `==POSE-BEGIN==`〜`==POSE-END==` に、新しい体の種類（BODIES）・クリップ（clip(...)）・敵の割り当て（ENEMIES）を追加
3. `node motion/dungeon_minor/tools/export_unity.mjs` で .anim と README を作り直す
4. 確認用の形は `SHAPES`（POSE-END より後ろ）に追加
5. このファイルの表を更新してコミット
- ユーザー指示「途中で止めずに全てのモンスターの必要モーションを作成」。コミット `4592ecf` から作業ファイルを戻し、残り 48 体の割り当て計画を上の表に書いた
  - 進め方：①人型以外の新しい体の種類とクリップを追加 → ②書き出し・検証 → ③人型の仕組みと5体 → ④まとめて zip 納品
