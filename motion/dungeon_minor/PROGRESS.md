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
| EN-05 | 沼の魔物 | Creature | Idle / Move / Burrow（泥に潜る）/ Emerge_Bite（飛び出して噛む）/ Hit / Death | 完了（納品済み） |
| EN-06 | 毒吐き草 | Plant | Idle / Attack_Spit / Hit / Death（動かない） | 完了（納品済み） |
| EN-07 | 毒羽のバチ | Bee | Idle / Move / Attack_Sting / Hit / Death | 完了（納品済み） |
| EN-08 | 大蛍 | Bee | Idle / Move / Attack_Ram（体当たり）/ Hit / Death | 完了（納品済み） |
| EN-10 | 根喰い虫の幼虫 | Creature | Idle / Move / Emerge_Bite / Attack_Bite / Hit / Death | 完了（納品済み） |
| EN-11 | 世界樹の瘤 | Plant | Dormant（擬態）/ WakeUp / Idle / Attack_Slam / Hit / Death | 完了（納品済み） |
| EN-14 | 翼の悪魔（小） | Flyer | Idle / Move / Attack_Dive（急降下→着地1秒→飛び立つ）/ Hit / Death | 完了（納品済み） |
| EN-15 | 岩の魔物 | RockBall（1.67倍） | Idle / Move / Attack_Roll_Long（起き上がり2秒）/ Hit / Death | 完了（納品済み） |
| EN-18 | 石くれ人形 | Upright | Idle / Move / Attack_HeavySlam（予備動作0.8秒）/ Hit / Death | 完了（納品済み） |
| EN-19 | 洞の小蜘蛛 | Spider | Idle / Move / Descend（天井から降りる）/ Attack_Web / Hit / Death | 完了（納品済み） |
| EN-20 | 骨の小竜 | Flyer | Idle / Move / Attack_GlideBite / Hit / Death_Collapse / Reassemble | 完了（納品済み） |
| EN-21 | 炎の魔物 | Creature | Idle / Move / Attack_Tackle / Hit / Death | 完了（納品済み） |
| EN-22 | 火蜥蜴 | Creature | Idle / Move / Attack_Breath（1秒）/ Hit / Death | 完了（納品済み） |
| EN-23 | 鉄殻虫 | Creature | Idle / Move / Attack_Bite / Flipped（ひっくり返る）/ Hit / Death | 完了（納品済み） |
| EN-24 | 湯煙の精 | Phantom | Idle / Move / Appear / Attack_Blow / Vanish / Hit / Death | 完了（納品済み） |
| EN-25 | 湯あたりガエル | Creature | Idle / Move / Attack_Pounce（大跳躍）/ Hit / Death | 完了（納品済み） |
| EN-26 | 巡回の検品機 | Clockwork | Idle / Move / Alert（見つけた） | 完了（納品済み） |
| EN-27 | 天の番兵 | Upright | Idle / Move / Attack_Swing（警棒）/ Hit / Death | 完了（納品済み） |
| EN-28 | 仕分けの手 | Upright | Idle / Move / Attack_GrabThrow（予備動作0.8秒）/ Hit / Death | 完了（納品済み） |
| EN-29 | 水路の清掃機 | Whale | Idle / Move / Attack_LeapTackle / Hit / Death | 完了（納品済み） |
| EN-30 | 歯車の子 | Clockwork | Idle / Move / Attack_SpinJump / Hit / Death | 完了（納品済み） |
| EN-31 | 迷い羽根 | Bee | Idle / Move_Flutter / Attack_Slash / Hit / Death | 完了（納品済み） |
| EN-32 | 監督の魔物 | Creature | Idle / Move / Attack_Whip（前方120°の横なぎ）/ Hit / Death | 完了（納品済み） |
| EN-34 | 炎喰いの子 | Creature | Idle / Move / Attack_Bite / Grow（大きくなる）/ Hit / Death | 完了（納品済み） |
| EN-35 | 冷えた溶岩の殻 | RockBall（1.67倍） | Idle / Move / Attack_Roll_Long / Hit / Death_Shatter（割れる） | 完了（納品済み） |
| EN-36 | 看守の犬 | Hound | Idle / Move / Sniff / Bark / Attack_Bite / Hit / Death | 完了（納品済み） |
| EN-37 | 鎖の魂 | Phantom | Dormant / WakeUp / Idle / Move / Attack_ChainLash / Hit / Death | 完了（納品済み） |
| EN-38 | 無音の影 | Phantom | Idle / Move / Attack_Strike / Hit / Death | 完了（納品済み） |
| EN-39 | 聖堂騎士 | Upright | Idle / Move / Attack_Combo2（剣の2連撃）/ Hit / Death | 完了（納品済み） |
| EN-40 | 動く鎧 | Upright | Idle / Move / Attack_HeavySlam / Hit / Death | 完了（納品済み） |
| EN-41 | 書架の魔物 | Clockwork | Idle / Move / Attack_Throw（本を3冊扇形）/ Hit / Death | 完了（納品済み） |
| EN-44 | 酔いバチ | Bee | Idle / Move_Drunk / Attack_DoubleSting / Hit / Death | 完了（納品済み） |
| EN-45 | 樽の子 | Barrel | Disguise / Reveal / Idle / Move / Attack_Roll / Hit / Death | 完了（納品済み） |
| EN-46 | 箱入りの忘れ物 | Box | Disguise / Attack_Bite / Idle / Move / Hit / Death | 完了（納品済み） |
| EN-47 | 名を失くした亡者 | Upright | Idle / Move / Attack_Punch / Hit / Death | 完了（納品済み） |
| EN-48 | 苔の石像 | Upright | Disguise / Ambush_Punch / Idle / Move / Hit / Death | 完了（納品済み） |
| EN-49 | 墓守の鬼火 | Fairy | Idle / Move / Attack_Touch / Hit / Death | 完了（納品済み） |
| EN-50 | 墓荒らしの魔物 | Creature | Idle / Move / Attack_Bite / Dig_Escape（穴を掘って逃げる）/ Hit / Death | 完了（納品済み） |
| EN-51 | 笑う死者 | Upright | Idle_Laugh / Move / Attack_Grab / Hit / Death_Crumble（花になって崩れる） | 完了（納品済み） |
| EN-52 | 侵食の蔦 | Plant | Submerged（地中）/ Attack_Erupt（突き上げ）/ Idle / Hit / Death | 完了（納品済み） |
| EN-53 | 庭の番 | Plant | Idle / Move / Attack_Lunge / Hit / Death | 完了（納品済み） |
| EN-55 | 刈り込み鋏 | Shears | Idle / Move / Attack_Snip2（はさみ込み2連）/ Hit / Death | 完了（納品済み） |
| EN-56 | 受粉の蜂 | Bee | Idle / Move / Attack_Sting / Hit / Death | 完了（納品済み） |

名前に「人」を含まないので、聖堂騎士・動く鎧・亡者・死者なども「体全体を動かす」方式（Upright）で作る（ユーザーの決めた振り分けどおり）。

### 人型（名前に「人」を含む5体）

骨を持つ人型（Humanoid）モデルを動かすため、次の仕組みにする：
- 見えない「代理の骨組み（Proxy）」を Generic クリップで動かし、`HumanoidRetarget.cs` が毎フレーム、モデルの Humanoid ボーン（Animator.GetBoneTransform）を代理の骨と同じ向きに回す
- 骨の向きだけを写すので、モデルの骨の軸の向きや体格が違っても使える（ねじれは元のまま）
- 作業ファイル：`dungeon_humanoid.html`（確認用・定義）＋ `tools/export_humanoid.mjs`

| ID | 名前 | 作るクリップ | 状態 |
|---|---|---|---|
| EN-09 | 溺れた村人 | Idle / Move（ゆっくり歩く）/ Attack_Grab（掴んで1.5秒離さない）/ Hit / Death | 完了（納品済み） |
| EN-12 | 狼の獣人 | Idle / Move（走る）/ Attack_Punch / Attack_Kick / Howl（吠える）/ Hit / Death | 完了（納品済み） |
| EN-13 | 狼の獣人（弓） | Idle / Move_Back（下がる）/ Attack_Bow（矢を撃つ）/ Hit / Death | 完了（納品済み） |
| EN-33 | 罪人の影 | Idle / Move / Sink（影に潜る）/ Rise（出てくる）/ Attack_Claw / Hit / Death | 完了（納品済み） |
| EN-54 | 光の番人 | Idle / Appear（現れる）/ Attack_Shoot（光の矢）/ Hit / Death | 完了（納品済み） |

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

1. 作業ファイルを戻す：`git checkout 80330b7 -- motion/dungeon_minor`（または展開先の `dungeon_minor` フォルダを持ってくる）
2. `dungeon_minor.html` の `==POSE-BEGIN==`〜`==POSE-END==` に、新しい体の種類（BODIES）・クリップ（clip(...)）・敵の割り当て（ENEMIES）を追加
3. `node motion/dungeon_minor/tools/export_unity.mjs`（人型は `export_humanoid.mjs`）で .anim と README を作り直す
4. 確認用の形は `SHAPES`（POSE-END より後ろ）に追加
5. このファイルの表を更新してコミット
- ユーザー指示「途中で止めずに全てのモンスターの必要モーションを作成」。コミット `4592ecf` から作業ファイルを戻し、残り 48 体の割り当て計画を上の表に書いた
  - 進め方：①人型以外の新しい体の種類とクリップを追加 → ②書き出し・検証 → ③人型の仕組みと5体 → ④まとめて zip 納品
- 人型以外の残り 43 体を追加（新しい体の種類 12：Creature / Plant / Flyer / Upright / Spider / Phantom / Clockwork / Whale / Hound / Barrel / Box / Shears、既存の Bee / RockBall / Fairy にもクリップ追加）。合計 51 体・138 クリップ
  - 書き出しを改良：キー数/秒は 30 から始め、補間のずれが 1mm を超えるクリップだけ自動で細かくする。動かない項目も2キーで必ず書く（クリップ切り替え時に前の値が残らないように）
  - 検証：別スクリプトで全 138 本を読み直し、ずれ最大 1.05mm。長さ・ループ・イベント・編集用カーブも一致
  - 次：人型5体（`dungeon_humanoid.html`・`tools/export_humanoid.mjs`・`unity/HumanoidRetarget.cs`）
- 人型5体を作成：`dungeon_humanoid.html`（確認用・定義）、`tools/export_humanoid.mjs`、`unity/Humanoid/`（29 クリップ・`HumanoidRetarget.cs`・`HumanoidProxyBones.cs`・README）
  - 代理の骨組み（Proxy）は関節の位置だけを動かす（回転なし）。`HumanoidRetarget` が位置から骨の向きを求め、モデルの Humanoid ボーンを同じ向きに回す
  - 肘・膝の IK は伸び切る手前でなめらかに頭打ち、弓を引く腕は肘を後ろへ張る向きを指定（肘の反転を防ぐ）
  - 検証：全 29 本を読み直して関節位置のずれ最大 1.9mm（許容 2mm）。関節・ループ・イベントも一致
  - `EnemyMotion` は子の Proxy を Motion の下へ移さないよう修正
- **全 56 体 完了・納品**：`HELLEDEN_DungeonMinor_All.zip`（展開先 `D:\\HELLEDEN\\Assets\\HELLEDEN\\Animation`、案A の内容も含む完全版）
  - 人型以外 51 体・138 クリップ ＋ 人型 5 体・29 クリップ ＝ 167 クリップ
  - 作業ファイル一式はコミット `80330b7` にある（git からは削除済み）。取り出し方：`git checkout 80330b7 -- motion/dungeon_minor`

## 第2段階：手足も動かす（ユーザー指示「人の形をしていないものでも手足を動かせる場合は、動かすモーションに変えて」）

方針：
- 人の形の骨で動かせる敵は、人型の仕組み（Proxy ＋ HumanoidRetarget）へ移す
  - Upright の8体（EN-18 / 27 / 28 / 39 / 40 / 47 / 48 / 51）、EN-36 看守の犬（狼の獣人 CHR-025 を四つ足の姿勢で）、Phantom の3体（EN-24 / 37 / 38：人影）
- それ以外は、体全体の動き（Motion）に加えて、手足・羽・しっぽ・刃・ふたの「代理の関節」（Motion/Limbs/...）もクリップで動かす
  - 新しい `LimbRetarget.cs` が、Inspector で割り当てたモデルの骨を、代理の関節の「初期からの向きの変化」と同じだけ回す（モデルの骨の軸や初期の曲がり方が違っても使える）
  - 体の種類ごとの手足：Creature/RockBall 四つ足＋しっぽ＋首、Bee 羽＋脚、Flyer 翼＋脚＋しっぽ、Plant 葉の腕、Spider 8本脚、Clockwork 腕＋脚、Whale しっぽ＋ひれ、Mushroom 腕＋足、Fairy 羽、Slug 目の触角、Barrel 足、Box ふた、Shears 刃

| 段階 | 内容 | 状態 |
|---|---|---|
| 2-1 | 人型へ移す 12 体のクリップを dungeon_humanoid.html に追加 | 完了（91 クリップ・17 体。dungeon_minor.html からは Upright/Phantom/Hound を削除し 39 体・106 クリップ） |
| 2-2 | 手足の代理関節と動きを dungeon_minor.html に追加（体の種類ごと） | 完了（14 種類・106 クリップすべてに手足の指示） |
| 2-3 | 書き出し（export_unity.mjs に手足のカーブ、LimbRigs.cs 生成）と LimbRetarget.cs | 完了 |
| 2-4 | 検証・zip 納品・git から作業ファイル削除 | 完了 |

- 作業ファイルをコミット `80330b7` から戻して開始
- 2-1 完了：人型の骨組みに Knight / Heavy / Sentry / Grabber / Ghoul / Statue / Laugher / Hound / Steam / Chained / Silent を追加。四つ足用に roll（横倒し）と handWL/handWR（手を地面の位置で指定）を追加。確認画面は Idle が無い敵（笑う死者）でも動くよう修正
- 2-2 / 2-3：手足の代理関節（Motion/Limbs/<鎖>_0/<鎖>_1/...、位置のみ）を追加。`LimbRetarget.cs`（Inspector で骨を割り当て、向きの変化を写す）と自動生成の `LimbRigs.cs`
  - 書き出しを作り直し：キーの細かさを体全体（1mm）と関節ごと（0.5mm）で別々に自動決定、キーは time/value/傾きだけ書く（重みは省く）、有効数字6桁
  - 人型の書き出しも関節ごとに細かさを決める方式に（関節ごと 1.2mm）
  - 不連続だった式を修正（樽の足をしまう量、時計仕掛けの待機のカチカチ）
  - `EnemyMotion.EnsureMotionRoot` を static にして LimbRetarget からも使う
  - 人型へ移した Hound / Phantom / Upright の古いクリップのフォルダは削除
- 検証：人型以外 106 本（体全体のずれ最大 1.1mm、手足の鎖の先まで最大 0.6mm）、人型 91 本（関節位置のずれ最大 2.5mm）。長さ・ループ・イベント・編集用カーブ・手足の鎖のそろいも一致
- **第2段階 完了・納品**：`HELLEDEN_DungeonMinor_Limbs.zip`（展開先 `D:\\HELLEDEN\\Assets\\HELLEDEN\\Animation`）
  - 人型以外 39 体・106 クリップ（体全体＋手足）、人型 17 体・91 クリップ ＝ 56 体・197 クリップ
  - 前回の納品から Hound / Phantom / Upright のフォルダが無くなったので、展開前に古い dungeon_minor フォルダを消してもらう
  - 作業ファイル一式はコミット `564aabd` にある（git からは削除済み）。取り出し方：`git checkout 564aabd -- motion/dungeon_minor`

## 次に再開するとき（第2段階以降）

1. 作業ファイルを戻す：`git checkout 564aabd -- motion/dungeon_minor`（または展開先の `dungeon_minor` フォルダを持ってくる）
2. 人型以外：`dungeon_minor.html` の POSE 部分（BODIES・clip(...)・LIMBS・ENEMIES）を編集 → `node motion/dungeon_minor/tools/export_unity.mjs`
3. 人型：`dungeon_humanoid.html` の POSE 部分（姿勢の基本形・clip(...)・RIGS・ENEMIES）を編集 → `node motion/dungeon_minor/tools/export_humanoid.mjs`
4. このファイルを更新してコミット。納品したら作業ファイルを git から消し、このファイルだけ残す

## 第3段階：更新された「モンスター一覧」シートの I列（行動・攻撃）から追加

- 001〜060 のうち、ダンジョン雑魚で作っていなかった 4 体と、I列に内容のあるボス 3 体を追加する
- ボスのうち「未設計（ボスの行動・攻撃はまだ決めていない）」の 40 体は、行動が決まってから作る（今回は作らない）
- 時間はモンスター表・モンスタースキル表の数値どおりにし、区切りにイベント（Telegraph / Strike / Recover など）を入れる。0.7m・0.3m の踏み込みはゲーム側（MonsterController）が動かすので、クリップはその場

| No. | 名前 | 仕組み | 作るクリップ | 状態 |
|---|---|---|---|---|
| 001 | キノコ | Mushroom（体全体＋手足） | Run（追跡 3.2m/秒）/ Attack_Lunge_Std（予告0.3＋のけぞり0.55→攻撃0.18→硬直0.9） ＋ 既存の Idle / Move / Hit / Death | 完了 |
| 006 | 装甲バチ | Bee | Run / Attack_Lunge_Std ＋ 既存 | 完了 |
| 007 | 植物クリーチャー | Plant（2倍＝高さ2.4m） | Run / Attack_Lunge_Std ＋ 既存 | 完了 |
| 008 | 魔族（下っ端） | 人型 Demon | Idle / Move / Run / Attack_Punch / Attack_Kick（予告0.3＋0.3→攻撃0.15→硬直0.7）/ Hit / Death | 完了 |
| 065 | 魔族の群れ頭 | 人型 Demon（2.5倍） | 008 と同じ | 完了 |
| 063 | ベリット | 人型 Berit | 008 と同じ ＋ Attack_Flame（両腕を上げる→1.8秒）/ Attack_Charge_Start / Attack_Charge_Loop / Attack_Charge_End（硬直0.8） | 完了 |
| 095 | 空鯨 | SkyWhale（新しい体・20倍＝全長30m） | Idle / Move / Attack_Breath（0.3＋0.9→1.2）/ Attack_TailSweep（0.3＋0.7→0.5）/ Attack_Inhale（0.3＋1.2→4）/ Shake（0.4）/ Hit（銛）/ Crash / Death | 完了 |

- 作業ファイルをコミット `564aabd` から戻して開始
- 人型以外に追加：Mushroom / Bee / Plant の Run と Attack_Lunge_Std（イベント Telegraph 0 / Strike 0.85 / Recover 1.03 / RecoverEnd 1.93）、新しい体 SkyWhale（尾・ひれ・あご）と 9 クリップ。確認画面は大きな敵のカメラを離すよう修正
- 人型に追加：Demon（No.008 / 065）と Berit（No.063）。パンチ・キックのイベント Telegraph 0 / Strike 0.6 / Recover 0.75 / RecoverEnd 1.45、火炎 FlameStart 0.85 / FlameEnd 2.65、突進 ChargeStart / ChargeEnd
- 合計：人型以外 43 体・121 クリップ、人型 20 体・109 クリップ ＝ 230 クリップ
