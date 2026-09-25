# ダンジョン雑魚モーション（Unity 用）

`../dungeon_minor.html` をブラウザで開くと、敵ごとに全クリップの動きを確認できます。
このファイルは `../tools/export_unity.mjs` が自動生成します（手で編集しても作り直すと消えます）。

## 仕組み

- 骨を使わず、モデル全体の位置・回転・伸び縮みだけで動かす方式です。どのモデルにも付けられます。
- 構成：`敵の本体（Animator ＋ EnemyMotion）` → 子 `Motion`（クリップが動かす） → モデル
- 回転や伸び縮みの中心（軸）は体の種類ごとに決めてあり、クリップに織り込み済みです（下の表）。
- 敵の大きさ（1.3倍・2倍など）は、敵の本体の Scale で変えてください。動きの幅も一緒に大きくなります。

## 使い方

1. `EnemyMotion.cs` と、使う体の種類のフォルダ（例：`Mushroom/`）を Assets に置く。
2. 敵の本体の GameObject に `EnemyMotion` を付ける（Animator も自動で付きます）。
   - 子に `Motion` が無ければ自動で作り、今ある子（モデル）をその下へ移します。
   - モデルは `Motion` の下に、足元が原点・+Z が正面になるよう置く（浮く敵は下の表の高さに体の中心を合わせる）。
3. **Clips** にその敵のクリップを入れる（下の「敵ごとのクリップ」）。
4. ゲーム側から `GetComponent<EnemyMotion>().Play("Attack_Lunge")` のように名前の末尾で再生する。
   - `Play("Death")` で Death_SporeBurst、`Play("Move")` で妖精の Move_Flee も再生されるので、どの敵も同じ名前（Idle / Move / Hit / Death）で呼べます。
   - 1回きりのクリップが終わると自動で待機（Idle）に戻ります。名前に Death を含むクリップは最後の姿勢で止まります。
   - 移動中は `Play("Move")`、止まったら `Play("Idle")`。
5. **On Motion Event** に処理をつなぐと、攻撃が当たる瞬間などにイベント名（Hit / Stomp など）付きで呼ばれます。
   **On Motion Finished** は1回きりのクリップが終わったときに呼ばれます。

長い突進（ハチの Attack_Charge）と転がり（岩ダンゴの Attack_Roll）は、クリップはその場で「構え → 突進中の姿勢 → 止まる」だけを動かします。
ChargeStart〜ChargeEnd、RollStart〜RollEnd の間に、ゲーム側で敵の本体を前へ動かしてください。
短い飛びかかり・噛みつき・刺す動きは、クリップの中で前に出て元の位置に戻ります。

## 敵ごとのクリップ

| ID | 名前 | 体の種類 | クリップ（unity/<体>/<体>_<名前>.anim） | 大きさ |
|---|---|---|---|---|
| EN-01 | 胞子キノコ | Mushroom | Idle / Move / Attack_Lunge / Hit / Death_SporeBurst | 1倍 |
| EN-02 | 巣守りのバチ | Bee | Idle / Move / Attack_Sting / Attack_Charge / Hit / Death | 1.3倍 |
| EN-03 | 妖精の灯 | Fairy | Idle / Move_Flee / Attack_Powder / Hit / Death | 1倍 |
| EN-04 | 輪の茸番 | Mushroom | Idle / Move / Attack_Stomp / Hit / Death | 2倍 |
| EN-16 | 洞窟茸 | Mushroom | Idle / Move / Attack_Lunge / Hit / Death | 1倍 |
| EN-17 | 岩ダンゴ | RockBall | Idle / Move / Attack_Roll / Hit / Death | 1倍 |
| EN-42 | 水路ナメクジ | Slug | Idle / Move / Attack_Bite / Hit / Death | 1倍 |
| EN-43 | 苔キノコ | Mushroom | Idle / Move / Attack_Lunge / Hit / Death | 1倍 |
| EN-05 | 沼の魔物 | Creature | Idle / Move / Burrow / Emerge_Bite / Hit / Death | 1倍 |
| EN-06 | 毒吐き草 | Plant | Idle / Attack_Spit / Hit / Death | 1倍 |
| EN-07 | 毒羽のバチ | Bee | Idle / Move / Attack_Sting / Hit / Death | 1倍 |
| EN-08 | 大蛍 | Bee | Idle / Move / Attack_Ram / Hit / Death | 0.6倍 |
| EN-10 | 根喰い虫の幼虫 | Creature | Idle / Move / Emerge_Bite / Attack_Bite / Hit / Death | 0.6倍 |
| EN-11 | 世界樹の瘤 | Plant | Dormant / WakeUp / Idle / Attack_Slam / Hit / Death | 1倍 |
| EN-14 | 翼の悪魔（小） | Flyer | Idle / Move / Attack_Dive / Hit / Death | 0.8倍 |
| EN-15 | 岩の魔物 | RockBall | Idle / Move / Attack_Roll_Long / Hit / Death | 1.67倍 |
| EN-18 | 石くれ人形 | Upright | Idle / Move / Attack_HeavySlam / Hit / Death | 1倍 |
| EN-19 | 洞の小蜘蛛 | Spider | Idle / Move / Descend / Attack_Web / Hit / Death | 1倍 |
| EN-20 | 骨の小竜 | Flyer | Idle / Move / Attack_GlideBite / Hit / Death_Collapse / Reassemble | 0.8倍 |
| EN-21 | 炎の魔物 | Creature | Idle / Move / Attack_Tackle / Hit / Death | 1倍 |
| EN-22 | 火蜥蜴 | Creature | Idle / Move / Attack_Breath / Hit / Death | 0.7倍 |
| EN-23 | 鉄殻虫 | Creature | Idle / Move / Attack_Bite / Flipped / Hit / Death | 1倍 |
| EN-24 | 湯煙の精 | Phantom | Idle / Move / Appear / Attack_Blow / Vanish / Hit / Death | 1倍 |
| EN-25 | 湯あたりガエル | Creature | Idle / Move / Attack_Pounce / Hit / Death | 1倍 |
| EN-26 | 巡回の検品機 | Clockwork | Idle / Move / Alert | 1倍 |
| EN-27 | 天の番兵 | Upright | Idle / Move / Attack_Swing / Hit / Death | 1倍 |
| EN-28 | 仕分けの手 | Upright | Idle / Move / Attack_GrabThrow / Hit / Death | 1.2倍 |
| EN-29 | 水路の清掃機 | Whale | Idle / Move / Attack_LeapTackle / Hit / Death | 1倍 |
| EN-30 | 歯車の子 | Clockwork | Idle / Move / Attack_SpinJump / Hit / Death | 0.5倍 |
| EN-31 | 迷い羽根 | Bee | Idle / Move_Flutter / Attack_Slash / Hit / Death | 1倍 |
| EN-32 | 監督の魔物 | Creature | Idle / Move / Attack_Whip / Hit / Death | 1倍 |
| EN-34 | 炎喰いの子 | Creature | Idle / Move / Attack_Bite / Grow / Hit / Death | 0.6倍 |
| EN-35 | 冷えた溶岩の殻 | RockBall | Idle / Move / Attack_Roll_Long / Hit / Death_Shatter | 1.67倍 |
| EN-36 | 看守の犬 | Hound | Idle / Move / Sniff / Bark / Attack_Bite / Hit / Death | 1倍 |
| EN-37 | 鎖の魂 | Phantom | Dormant / WakeUp / Idle / Move / Attack_ChainLash / Hit / Death | 1倍 |
| EN-38 | 無音の影 | Phantom | Idle / Move / Attack_Strike / Hit / Death | 1倍 |
| EN-39 | 聖堂騎士 | Upright | Idle / Move / Attack_Combo2 / Hit / Death | 1倍 |
| EN-40 | 動く鎧 | Upright | Idle / Move / Attack_HeavySlam / Hit / Death | 1.1倍 |
| EN-41 | 書架の魔物 | Clockwork | Idle / Move / Attack_Throw / Hit / Death | 1倍 |
| EN-44 | 酔いバチ | Bee | Idle / Move_Drunk / Attack_DoubleSting / Hit / Death | 1倍 |
| EN-45 | 樽の子 | Barrel | Disguise / Reveal / Idle / Move / Attack_Roll / Hit / Death | 0.8倍 |
| EN-46 | 箱入りの忘れ物 | Box | Disguise / Attack_Bite / Idle / Move / Hit / Death | 1倍 |
| EN-47 | 名を失くした亡者 | Upright | Idle / Move / Attack_Punch / Hit / Death | 1倍 |
| EN-48 | 苔の石像 | Upright | Disguise / Ambush_Punch / Idle / Move / Hit / Death | 1倍 |
| EN-49 | 墓守の鬼火 | Fairy | Idle / Move / Attack_Touch / Hit / Death | 1倍 |
| EN-50 | 墓荒らしの魔物 | Creature | Idle / Move / Attack_Bite / Dig_Escape / Hit / Death | 1倍 |
| EN-51 | 笑う死者 | Upright | Idle_Laugh / Move / Attack_Grab / Hit / Death_Crumble | 1倍 |
| EN-52 | 侵食の蔦 | Plant | Submerged / Attack_Erupt / Idle / Hit / Death | 1倍 |
| EN-53 | 庭の番 | Plant | Idle / Move / Attack_Lunge / Hit / Death | 1倍 |
| EN-55 | 刈り込み鋏 | Shears | Idle / Move / Attack_Snip2 / Hit / Death | 1倍 |
| EN-56 | 受粉の蜂 | Bee | Idle / Move / Attack_Sting / Hit / Death | 1倍 |

## クリップ一覧

| クリップ | 長さ | ループ | イベント |
|---|---|---|---|
| Mushroom_Idle | 2秒 | する | ― |
| Mushroom_Move | 0.6秒 | する | ― |
| Mushroom_Attack_Lunge | 1.4秒 | しない | Hit（0.68秒） |
| Mushroom_Attack_Stomp | 2.2秒 | しない | Stomp（1秒）、Recover（1.9秒） |
| Mushroom_Hit | 0.45秒 | しない | ― |
| Mushroom_Death | 1.6秒 | しない | Down（0.6秒） |
| Mushroom_Death_SporeBurst | 2.3秒 | しない | Down（0.6秒）、SporeBurst（1.6秒） |
| Bee_Idle | 1.2秒 | する | ― |
| Bee_Move | 1秒 | する | ― |
| Bee_Attack_Sting | 1.2秒 | しない | Hit（0.55秒） |
| Bee_Attack_Charge | 1.9秒 | しない | ChargeStart（0.6秒）、ChargeEnd（1.5秒） |
| Bee_Hit | 0.4秒 | しない | ― |
| Bee_Death | 1.4秒 | しない | Down（0.9秒） |
| Fairy_Idle | 2.4秒 | する | ― |
| Fairy_Move_Flee | 0.8秒 | する | ― |
| Fairy_Attack_Powder | 1.6秒 | しない | Powder（0.7秒） |
| Fairy_Hit | 0.4秒 | しない | ― |
| Fairy_Death | 1.2秒 | しない | Vanish（1.15秒） |
| RockBall_Idle | 1.6秒 | する | ― |
| RockBall_Move | 0.7秒 | する | ― |
| RockBall_Attack_Roll | 2.6秒 | しない | RollStart（0.5秒）、RollEnd（1.8秒） |
| RockBall_Hit | 0.4秒 | しない | ― |
| RockBall_Death | 1.4秒 | しない | Crumble（0.6秒） |
| Slug_Idle | 2秒 | する | ― |
| Slug_Move | 1.2秒 | する | ― |
| Slug_Attack_Bite | 1.3秒 | しない | Hit（0.62秒） |
| Slug_Hit | 0.4秒 | しない | ― |
| Slug_Death | 1.6秒 | しない | Melt（0.3秒） |
| Bee_Attack_Ram | 1.1秒 | しない | Hit（0.5秒） |
| Bee_Move_Flutter | 2秒 | する | ― |
| Bee_Attack_Slash | 1秒 | しない | Hit（0.45秒） |
| Bee_Move_Drunk | 1.6秒 | する | ― |
| Bee_Attack_DoubleSting | 1.8秒 | しない | Hit（0.5秒）、Hit（1.1秒） |
| RockBall_Attack_Roll_Long | 3.8秒 | しない | RollStart（0.5秒）、RollEnd（1.8秒）、GetUp（3.5秒） |
| RockBall_Death_Shatter | 1.2秒 | しない | Shatter（0.5秒） |
| Fairy_Move | 2秒 | する | ― |
| Fairy_Attack_Touch | 1秒 | しない | Hit（0.45秒） |
| Creature_Idle | 2秒 | する | ― |
| Creature_Move | 0.6秒 | する | ― |
| Creature_Attack_Bite | 1.2秒 | しない | Hit（0.55秒） |
| Creature_Hit | 0.4秒 | しない | ― |
| Creature_Death | 1.6秒 | しない | Down（0.6秒） |
| Creature_Attack_Tackle | 1.3秒 | しない | Hit（0.6秒） |
| Creature_Attack_Breath | 2秒 | しない | BreathStart（0.4秒）、BreathEnd（1.4秒） |
| Creature_Attack_Pounce | 1.8秒 | しない | JumpStart（0.5秒）、Land（1.1秒） |
| Creature_Attack_Whip | 1.5秒 | しない | Hit（0.65秒） |
| Creature_Burrow | 1.2秒 | しない | Hidden（1.1秒） |
| Creature_Emerge_Bite | 1.4秒 | しない | Warn（0秒）、Emerge（0.4秒）、Hit（0.7秒） |
| Creature_Flipped | 2.6秒 | しない | Flipped（0.3秒）、Recover（2.1秒） |
| Creature_Grow | 1.2秒 | しない | Grow（0.6秒） |
| Creature_Dig_Escape | 1.6秒 | しない | Escaped（1.5秒） |
| Plant_Idle | 2.4秒 | する | ― |
| Plant_Move | 0.8秒 | する | ― |
| Plant_Hit | 0.4秒 | しない | ― |
| Plant_Death | 1.8秒 | しない | Down（1秒） |
| Plant_Attack_Spit | 1.4秒 | しない | Spit（0.6秒） |
| Plant_Dormant | 2秒 | する | ― |
| Plant_WakeUp | 1.2秒 | しない | Awake（0.7秒） |
| Plant_Attack_Slam | 1.6秒 | しない | Hit（0.68秒） |
| Plant_Submerged | 2秒 | する | ― |
| Plant_Attack_Erupt | 2秒 | しない | Warn（0秒）、Hit（1.1秒） |
| Plant_Attack_Lunge | 1.3秒 | しない | Hit（0.58秒） |
| Flyer_Idle | 1秒 | する | ― |
| Flyer_Move | 2秒 | する | ― |
| Flyer_Hit | 0.4秒 | しない | ― |
| Flyer_Death | 1.5秒 | しない | Down（0.8秒） |
| Flyer_Attack_Dive | 2.8秒 | しない | Hit（0.88秒）、Land（0.9秒）、TakeOff（1.9秒） |
| Flyer_Attack_GlideBite | 1.8秒 | しない | Hit（0.85秒） |
| Flyer_Death_Collapse | 1.2秒 | しない | Collapse（0.5秒） |
| Flyer_Reassemble | 1.6秒 | しない | Reformed（1.2秒） |
| Upright_Idle | 2.4秒 | する | ― |
| Upright_Move | 0.9秒 | する | ― |
| Upright_Hit | 0.4秒 | しない | ― |
| Upright_Death | 1.6秒 | しない | Down（0.8秒） |
| Upright_Attack_HeavySlam | 2.4秒 | しない | Hit（0.98秒）、Recover（1.6秒） |
| Upright_Attack_Swing | 1.3秒 | しない | Hit（0.5秒） |
| Upright_Attack_Combo2 | 1.9秒 | しない | Hit（0.43秒）、Hit（0.83秒） |
| Upright_Attack_GrabThrow | 2.6秒 | しない | Grab（1秒）、Throw（1.5秒） |
| Upright_Attack_Punch | 1.1秒 | しない | Hit（0.45秒） |
| Upright_Attack_Grab | 1.8秒 | しない | Grab（0.5秒）、Release（1.4秒） |
| Upright_Disguise | 2秒 | する | ― |
| Upright_Ambush_Punch | 1.4秒 | しない | Awake（0.15秒）、Hit（0.58秒） |
| Upright_Idle_Laugh | 1.2秒 | する | ― |
| Upright_Death_Crumble | 2秒 | しない | Crumble（0.6秒） |
| Spider_Idle | 1.6秒 | する | ― |
| Spider_Move | 0.3秒 | する | ― |
| Spider_Hit | 0.4秒 | しない | ― |
| Spider_Death | 1.2秒 | しない | Down（0.5秒） |
| Spider_Descend | 1.6秒 | しない | Land（1.35秒） |
| Spider_Attack_Web | 1.3秒 | しない | Web（0.52秒） |
| Phantom_Idle | 2.4秒 | する | ― |
| Phantom_Move | 1.6秒 | する | ― |
| Phantom_Hit | 0.4秒 | しない | ― |
| Phantom_Death | 1.4秒 | しない | Vanish（1.3499999999999999秒） |
| Phantom_Appear | 1秒 | しない | Visible（0.5秒） |
| Phantom_Vanish | 0.8秒 | しない | Hidden（0.75秒） |
| Phantom_Attack_Blow | 2.2秒 | しない | BlowStart（0.4秒）、BlowEnd（1.8秒） |
| Phantom_Dormant | 3秒 | する | ― |
| Phantom_WakeUp | 1.2秒 | しない | Awake（0.8秒） |
| Phantom_Attack_ChainLash | 1.4秒 | しない | Hit（0.6秒） |
| Phantom_Attack_Strike | 1秒 | しない | Hit（0.38秒） |
| Clockwork_Idle | 1秒 | する | ― |
| Clockwork_Move | 0.8秒 | する | ― |
| Clockwork_Hit | 0.4秒 | しない | ― |
| Clockwork_Death | 1.6秒 | しない | Down（0.6秒） |
| Clockwork_Alert | 1.2秒 | しない | Spotted（0.2秒） |
| Clockwork_Attack_SpinJump | 1.4秒 | しない | Hit（0.8秒） |
| Clockwork_Attack_Throw | 1.4秒 | しない | Throw（0.52秒） |
| Whale_Idle | 2秒 | する | ― |
| Whale_Move | 2秒 | する | ― |
| Whale_Hit | 0.4秒 | しない | ― |
| Whale_Death | 2秒 | しない | Down（1.2秒） |
| Whale_Attack_LeapTackle | 2秒 | しない | LeapStart（0.5秒）、Hit（1.05秒） |
| Hound_Idle | 1秒 | する | ― |
| Hound_Move | 0.4秒 | する | ― |
| Hound_Sniff | 1.6秒 | する | ― |
| Hound_Bark | 1.2秒 | しない | Bark（0.35秒）、Bark（0.75秒） |
| Hound_Attack_Bite | 1秒 | しない | Hit（0.45秒） |
| Hound_Hit | 0.4秒 | しない | ― |
| Hound_Death | 1.6秒 | しない | Down（0.6秒） |
| Barrel_Disguise | 2秒 | する | ― |
| Barrel_Reveal | 0.9秒 | しない | Reveal（0.2秒） |
| Barrel_Idle | 1.6秒 | する | ― |
| Barrel_Move | 0.5秒 | する | ― |
| Barrel_Attack_Roll | 2.2秒 | しない | RollStart（0.3秒）、RollEnd（1.6秒） |
| Barrel_Hit | 0.4秒 | しない | ― |
| Barrel_Death | 1.4秒 | しない | Break（0.3秒） |
| Box_Disguise | 2秒 | する | ― |
| Box_Attack_Bite | 1.2秒 | しない | Hit（0.45秒） |
| Box_Idle | 1.6秒 | する | ― |
| Box_Move | 0.5秒 | する | ― |
| Box_Hit | 0.4秒 | しない | ― |
| Box_Death | 1.4秒 | しない | Down（0.5秒） |
| Shears_Idle | 2秒 | する | ― |
| Shears_Move | 1.6秒 | する | ― |
| Shears_Attack_Snip2 | 1.6秒 | しない | Hit（0.4秒）、Hit（0.7秒） |
| Shears_Hit | 0.4秒 | しない | ― |
| Shears_Death | 1.3秒 | しない | Down（0.6秒） |

## 体の種類

| 体の種類 | 軸の位置（足元が原点） | モデルの置き方 |
|---|---|---|
| Mushroom（キノコ） | (0, 0, 0) | 足元が原点。キノコ CHR-013 をそのまま Motion の子に置く |
| Bee（ハチ） | (0, 1, 0) | 胴体の中心が高さ 1.0m に来るよう置く（その高さでホバリング） |
| Fairy（光の妖精） | (0, 1.2, 0) | 光の玉の中心が高さ 1.2m に来るよう置く |
| RockBall（岩ダンゴ） | (0, 0.3, 0) | 足元が原点。丸まったときの球の中心が高さ 0.3m（0.6倍のクリーチャーを想定） |
| Slug（ナメクジ） | (0, 0.06, -0.3) | 足元が原点、頭が +Z。しっぽの付け根（後ろ 0.3m）を軸に伸び縮みする |
| Creature（四つ足の獣） | (0, 0.35, 0) | 足元が原点。ファンタジークリーチャー CHR-011（体の中心が高さ 0.35m 前後） |
| Plant（植物） | (0, 0, 0) | 根元が原点。植物クリーチャー CHR-016 |
| Flyer（翼の悪魔） | (0, 1.6, 0) | 胴体の中心が高さ 1.6m に来るよう置く（翼の悪魔 CHR-023） |
| Upright（人の形（体全体）） | (0, 0, 0) | 足元が原点。鎧戦士・ロボット・亡者など（人型の骨は使わず体全体で動かす） |
| Spider（蜘蛛） | (0, 0.2, 0) | 足元が原点。体の中心が高さ 0.2m |
| Phantom（浮かぶ人影） | (0, 1, 0) | 体の中心が高さ 1.0m に来るよう置く（湯気・鎖・影でできた人影） |
| Clockwork（時計仕掛け） | (0, 0.45, 0) | 足元が原点。スチームパンク時計クリーチャー CHR-015（体の中心が高さ 0.45m） |
| Whale（小型のクジラ） | (0, 0.3, 0) | 水面（または底）が原点。サイバークジラ CHR-009 を 0.5 倍で |
| Hound（四つ足の犬） | (0, 0.6, 0) | 足元が原点。狼の獣人 CHR-025 を四つ足にしたもの（体の中心が高さ 0.6m） |
| Barrel（樽） | (0, 0.4, 0) | 足元が原点。高さ 0.8m・半径 0.3m の樽 |
| Box（木箱） | (0, 0, -0.3) | 足元が原点。箱の後ろ下の角（後ろ 0.3m）を軸に傾く |
| Shears（浮かぶ鋏） | (0, 1.1, 0) | 鋏の留め具が高さ 1.1m に来るよう置く。刃先が +Z |

## 作り直し方

`../dungeon_minor.html` の `==POSE-BEGIN==`〜`==POSE-END==` にクリップ定義があります。編集したら次を実行すると .anim とこの README が作り直されます（Node.js のみ必要）。

```
node <dungeon_minor フォルダ>/tools/export_unity.mjs
```

## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面を教えてください。
