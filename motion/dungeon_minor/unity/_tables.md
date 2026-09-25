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

## 体の種類

| 体の種類 | 軸の位置（足元が原点） | モデルの置き方 |
|---|---|---|
| Mushroom（キノコ） | (0, 0, 0) | 足元が原点。キノコ CHR-013 をそのまま Motion の子に置く |
| Bee（ハチ） | (0, 1, 0) | 胴体の中心が高さ 1.0m に来るよう置く（その高さでホバリング） |
| Fairy（光の妖精） | (0, 1.2, 0) | 光の玉の中心が高さ 1.2m に来るよう置く |
| RockBall（岩ダンゴ） | (0, 0.3, 0) | 足元が原点。丸まったときの球の中心が高さ 0.3m（0.6倍のクリーチャーを想定） |
| Slug（ナメクジ） | (0, 0.06, -0.3) | 足元が原点、頭が +Z。しっぽの付け根（後ろ 0.3m）を軸に伸び縮みする |
