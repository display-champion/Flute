# ダンジョン雑魚・人型（Unity 用）

名前に「人」を含む敵（EN-09 / 12 / 13 / 33 / 54）用です。`../../dungeon_humanoid.html` で動きを確認できます。
このファイルは `../../tools/export_humanoid.mjs` が自動生成します。

## 仕組み

- 見えない「代理の骨組み（Proxy）」を Generic クリップで動かします（関節の位置だけ。回転は持たない）。
- `HumanoidRetarget` が毎フレーム（LateUpdate）、モデルの Humanoid ボーンを代理の骨と同じ向きに回します。
  - 骨の向きだけを写すので、モデルの体格・骨の軸の向きが違っても使えます。腰の上下・前後の動きは脚の長さの比で合わせます。
  - 腕や脚のねじれ（手のひらの向きなど）はモデルの元の姿勢のままです。

## 使い方

1. `EnemyMotion.cs`（ひとつ上のフォルダ）と、このフォルダの `HumanoidRetarget.cs`・`HumanoidProxyBones.cs`・使うクリップを Assets に置く。
2. 敵の本体（空の GameObject）に `EnemyMotion` と `HumanoidRetarget` を付ける。
3. 人型モデル（Rig が Humanoid のもの）を本体の子に置く。モデルの正面を +Z、足元を本体の原点に合わせる。
   - モデル自身の Animator には Controller を入れないでください（入れても LateUpdate で上書きしますが、無駄な計算になります）。
4. `HumanoidRetarget` の **Target** にモデルの Animator を入れる（空なら子から自動で探します）。
5. `EnemyMotion` の **Clips** にその敵のクリップを入れ、`Play("Attack_Punch")` のように再生する。イベントの受け取りは人型以外と同じです。

## 敵ごとのクリップ

| ID | 名前 | 骨組み | クリップ（Humanoid/<骨組み>_<名前>.anim） |
|---|---|---|---|
| EN-09 | 溺れた村人 | Drowned（溺れた死者） | Idle / Move / Attack_Grab / Hit / Death |
| EN-12 | 狼の獣人 | Wolfman（拳で戦う獣人） | Idle / Move / Attack_Punch / Attack_Kick / Howl / Hit / Death |
| EN-13 | 狼の獣人（弓） | Archer（弓を撃つ獣人） | Idle / Move_Back / Attack_Bow / Hit / Death |
| EN-33 | 罪人の影 | Shade（影の人） | Idle / Move / Sink / Rise / Attack_Claw / Hit / Death |
| EN-54 | 光の番人 | Guardian（光の人影） | Idle / Appear / Attack_Shoot / Hit / Death |
| EN-18 | 石くれ人形 | Heavy（大振りの鎧・人形） | Idle / Move / Attack_HeavySlam / Hit / Death |
| EN-24 | 湯煙の精 | Steam（湯気の人影） | Idle / Move / Appear / Attack_Blow / Vanish / Hit / Death |
| EN-27 | 天の番兵 | Sentry（警棒の番兵） | Idle / Move / Attack_Swing / Hit / Death |
| EN-28 | 仕分けの手 | Grabber（掴んで投げる機械） | Idle / Move / Attack_GrabThrow / Hit / Death |
| EN-36 | 看守の犬 | Hound（四つ足の獣人） | Idle / Move / Sniff / Bark / Attack_Bite / Hit / Death |
| EN-37 | 鎖の魂 | Chained（鎖の人影） | Dormant / WakeUp / Idle / Move / Attack_ChainLash / Hit / Death |
| EN-38 | 無音の影 | Silent（音のない人影） | Idle / Move / Attack_Strike / Hit / Death |
| EN-39 | 聖堂騎士 | Knight（剣の騎士） | Idle / Move / Attack_Combo2 / Hit / Death |
| EN-40 | 動く鎧 | Heavy（大振りの鎧・人形） | Idle / Move / Attack_HeavySlam / Hit / Death |
| EN-47 | 名を失くした亡者 | Ghoul（暴れる亡者） | Idle / Move / Attack_Punch / Hit / Death |
| EN-48 | 苔の石像 | Statue（動く石像） | Disguise / Ambush_Punch / Idle / Move / Hit / Death |
| EN-51 | 笑う死者 | Laugher（笑う死者） | Idle_Laugh / Move / Attack_Grab / Hit / Death_Crumble |

## クリップ一覧

| クリップ | 長さ | ループ | イベント |
|---|---|---|---|
| Wolfman_Idle | 2秒 | する | ― |
| Wolfman_Move | 0.6秒 | する | ― |
| Wolfman_Attack_Punch | 1秒 | しない | Hit（0.4秒） |
| Wolfman_Attack_Kick | 1.2秒 | しない | Hit（0.5秒） |
| Wolfman_Howl | 1.6秒 | しない | Howl（0.5秒） |
| Wolfman_Hit | 0.45秒 | しない | ― |
| Wolfman_Death | 1.8秒 | しない | Down（1.2秒） |
| Archer_Idle | 2.2秒 | する | ― |
| Archer_Move_Back | 0.8秒 | する | ― |
| Archer_Attack_Bow | 2秒 | しない | Shoot（1.2秒） |
| Archer_Hit | 0.45秒 | しない | ― |
| Archer_Death | 1.8秒 | しない | Down（1.2秒） |
| Drowned_Idle | 2.6秒 | する | ― |
| Drowned_Move | 1.6秒 | する | ― |
| Drowned_Attack_Grab | 2.6秒 | しない | Grab（0.7秒）、Release（2.2秒） |
| Drowned_Hit | 0.45秒 | しない | ― |
| Drowned_Death | 1.8秒 | しない | Down（1.2秒） |
| Shade_Idle | 2秒 | する | ― |
| Shade_Move | 0.8秒 | する | ― |
| Shade_Sink | 1秒 | しない | Hidden（0.9秒） |
| Shade_Rise | 1秒 | しない | Emerge（0.5秒） |
| Shade_Attack_Claw | 1.1秒 | しない | Hit（0.5秒） |
| Shade_Hit | 0.45秒 | しない | ― |
| Shade_Death | 1.6秒 | しない | Vanish（1.5秒） |
| Guardian_Idle | 3秒 | する | ― |
| Guardian_Appear | 1.2秒 | しない | Visible（0.6秒） |
| Guardian_Attack_Shoot | 1.8秒 | しない | Shoot（1.1秒） |
| Guardian_Hit | 0.45秒 | しない | ― |
| Guardian_Death | 1.6秒 | しない | Vanish（1.5秒） |
| Knight_Idle | 2.4秒 | する | ― |
| Knight_Move | 1秒 | する | ― |
| Knight_Attack_Combo2 | 1.9秒 | しない | Hit（0.45秒）、Hit（0.85秒） |
| Knight_Hit | 0.45秒 | しない | ― |
| Knight_Death | 1.8秒 | しない | Down（1.2秒） |
| Heavy_Idle | 3秒 | する | ― |
| Heavy_Move | 1.3秒 | する | ― |
| Heavy_Attack_HeavySlam | 2.4秒 | しない | Hit（0.98秒）、Recover（1.6秒） |
| Heavy_Hit | 0.45秒 | しない | ― |
| Heavy_Death | 1.8秒 | しない | Down（1.2秒） |
| Sentry_Idle | 3秒 | する | ― |
| Sentry_Move | 1秒 | する | ― |
| Sentry_Attack_Swing | 1.3秒 | しない | Hit（0.5秒） |
| Sentry_Hit | 0.45秒 | しない | ― |
| Sentry_Death | 1.8秒 | しない | Down（1.2秒） |
| Grabber_Idle | 2.4秒 | する | ― |
| Grabber_Move | 1.1秒 | する | ― |
| Grabber_Attack_GrabThrow | 2.6秒 | しない | Grab（1秒）、Throw（1.5秒） |
| Grabber_Hit | 0.45秒 | しない | ― |
| Grabber_Death | 1.8秒 | しない | Down（1.2秒） |
| Ghoul_Idle | 3秒 | する | ― |
| Ghoul_Move | 1.1秒 | する | ― |
| Ghoul_Attack_Punch | 1.1秒 | しない | Hit（0.45秒） |
| Ghoul_Hit | 0.45秒 | しない | ― |
| Ghoul_Death | 1.8秒 | しない | Down（1.2秒） |
| Statue_Disguise | 2秒 | する | ― |
| Statue_Ambush_Punch | 1.4秒 | しない | Awake（0.15秒）、Hit（0.6秒） |
| Statue_Idle | 3秒 | する | ― |
| Statue_Move | 1.3秒 | する | ― |
| Statue_Hit | 0.45秒 | しない | ― |
| Statue_Death | 1.8秒 | しない | Down（1.2秒） |
| Laugher_Idle_Laugh | 1.2秒 | する | ― |
| Laugher_Move | 1秒 | する | ― |
| Laugher_Attack_Grab | 1.8秒 | しない | Grab（0.5秒）、Release（1.4秒） |
| Laugher_Hit | 0.45秒 | しない | ― |
| Laugher_Death_Crumble | 2秒 | しない | Crumble（0.6秒）、Down（1.5秒） |
| Hound_Idle | 1秒 | する | ― |
| Hound_Move | 0.45秒 | する | ― |
| Hound_Sniff | 1.6秒 | する | ― |
| Hound_Bark | 1.2秒 | しない | Bark（0.35秒）、Bark（0.75秒） |
| Hound_Attack_Bite | 1秒 | しない | Hit（0.45秒） |
| Hound_Hit | 0.45秒 | しない | ― |
| Hound_Death | 1.6秒 | しない | Down（0.8秒） |
| Steam_Idle | 2.4秒 | する | ― |
| Steam_Move | 1.6秒 | する | ― |
| Steam_Appear | 1秒 | しない | Visible（0.5秒） |
| Steam_Vanish | 1秒 | しない | Hidden（0.75秒） |
| Steam_Attack_Blow | 2.2秒 | しない | BlowStart（0.4秒）、BlowEnd（1.8秒） |
| Steam_Hit | 0.45秒 | しない | ― |
| Steam_Death | 1秒 | しない | Vanish（0.9秒） |
| Chained_Dormant | 3秒 | する | ― |
| Chained_WakeUp | 1.2秒 | しない | Awake（0.8秒） |
| Chained_Idle | 2.4秒 | する | ― |
| Chained_Move | 1.6秒 | する | ― |
| Chained_Attack_ChainLash | 1.4秒 | しない | Hit（0.6秒） |
| Chained_Hit | 0.45秒 | しない | ― |
| Chained_Death | 1秒 | しない | Vanish（0.9秒） |
| Silent_Idle | 2.4秒 | する | ― |
| Silent_Move | 1.6秒 | する | ― |
| Silent_Attack_Strike | 1秒 | しない | Hit（0.38秒） |
| Silent_Hit | 0.45秒 | しない | ― |
| Silent_Death | 1秒 | しない | Vanish（0.9秒） |

## 注意

- Unity での実際の動作はまだ確認できていません。うまく動かないときはエラーの文面や見た目を教えてください。
