using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// モーションのイベント（AnimationEvent の OnMotionEvent）で SE を鳴らす。
/// Animator と同じ GameObject に付けると、MagicCircleRig・EnemyMotion のクリップのイベントをそのまま受け取れる。
/// 「Fire:3」のように番号付きのイベントは「Fire」でも一致する。
/// SE 名の中の {Element} は、同じ GameObject の MagicCircleRig の属性（Fire / Ice ...）に置き換わる。
/// 右上の ⋮ メニューの「魔法陣の既定を入れる」で、魔法陣用の組み合わせを入れられる。
/// </summary>
public class SEEventMap : MonoBehaviour
{
    [System.Serializable]
    public class Entry
    {
        [Tooltip("イベント名（例：Fire、Impact、Hit、Stomp）")]
        public string eventName;
        [Tooltip("鳴らす SE の名前（例：Magic_Shot_{Element}、Enemy_Stomp）")]
        public string se;
        [Tooltip("音量（1 = 元のまま）")]
        [Range(0f, 2f)] public float volume = 1f;
    }

    public List<Entry> entries = new List<Entry>();

    [Tooltip("この GameObject の位置で鳴らす（オフなら 2D）")]
    public bool positional = true;

    [Tooltip("{Element} に入れる属性（MagicCircleRig が無いとき、または上書きしたいとき）")]
    public string elementOverride = "";

    [Tooltip("イベントを受け取るたびにコンソールに出す（組み合わせを決めるとき用）")]
    public bool logEvents = false;

    Component rig;

    // クリップの AnimationEvent（関数名 OnMotionEvent）から呼ばれる。UnityEvent<string> からつないでもよい
    public void OnMotionEvent(string eventName)
    {
        if (logEvents) Debug.Log($"SEEventMap: {name} ← {eventName}", this);
        string baseName = eventName;
        int colon = eventName.IndexOf(':');
        if (colon >= 0) baseName = eventName.Substring(0, colon);
        foreach (var e in entries)
        {
            if (e == null || string.IsNullOrEmpty(e.se)) continue;
            if (e.eventName != eventName && e.eventName != baseName) continue;
            string se = e.se.Replace("{Element}", CurrentElement());
            if (positional) BattleSE.Play(se, transform.position, e.volume);
            else BattleSE.Play(se, e.volume);
        }
    }

    string CurrentElement()
    {
        if (!string.IsNullOrEmpty(elementOverride)) return elementOverride;
        // MagicCircleRig が無いプロジェクトでもコンパイルできるよう、名前で探して属性を読む
        if (rig == null) rig = GetComponent("MagicCircleRig");
        if (rig != null)
        {
            var f = rig.GetType().GetField("element");
            if (f != null) return f.GetValue(rig).ToString();
        }
        return "Fire";
    }

    [ContextMenu("魔法陣の既定を入れる")]
    void FillMagicCircleDefaults()
    {
        entries = new List<Entry>
        {
            new Entry { eventName = "Appear", se = "Magic_Circle_Appear" },
            new Entry { eventName = "Charge", se = "Magic_Charge" },
            new Entry { eventName = "Fire", se = "Magic_Shot_{Element}" },
            new Entry { eventName = "Impact", se = "Magic_Impact_{Element}" },
            new Entry { eventName = "BeamStart", se = "Magic_Beam" },
            new Entry { eventName = "PillarStart", se = "Magic_Pillar" },
        };
    }
}
