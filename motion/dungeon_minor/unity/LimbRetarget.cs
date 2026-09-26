using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 手足・羽・しっぽ・刃・ふたを動かす。
/// クリップが動かす「代理の関節」（子 Motion/Limbs/...）の、初期からの向きの変化と同じだけ、
/// Inspector で割り当てたモデルの骨を回す（LateUpdate）。モデルの骨の軸や初期の曲がり方が違っても使える。
/// 構成：この GameObject（Animator ＋ EnemyMotion ＋ LimbRetarget）→ 子 Motion → モデル
/// </summary>
[DefaultExecutionOrder(-100)]   // EnemyMotion より先に代理の関節を作る
public class LimbRetarget : MonoBehaviour
{
    [System.Serializable]
    public class ChainBinding
    {
        [Tooltip("手足の名前（LegFL・WingL など。体の種類から自動で並ぶ）")]
        public string name;

        [Tooltip("モデルの骨を、付け根から先へ順に（例：脚の付け根・ひざ）。空の欄は動かさない")]
        public Transform[] bones;
    }

    [Tooltip("体の種類（Creature / RockBall / Mushroom / Bee / Fairy / Flyer / Plant / Spider / Clockwork / Whale / Shears / Box / Barrel / Slug）")]
    public string body = "Creature";

    [Tooltip("手足ごとに、モデルの骨を割り当てる")]
    public ChainBinding[] chains;

    struct Segment
    {
        public Transform bone;
        public Quaternion restRot;   // Motion から見た初期の向き
        public Vector3 restDir;      // 代理の関節の初期の向き（Motion から見た）
        public Transform from, to;   // 代理の関節
    }

    readonly Dictionary<string, Transform[]> proxy = new Dictionary<string, Transform[]>();
    readonly List<Segment> segments = new List<Segment>();
    Transform motion;

    void Awake()
    {
        motion = EnemyMotion.EnsureMotionRoot(transform);
        BuildProxy();
    }

    // 体の種類に合わせて Chains の欄を並べる（割り当て済みの骨は名前が同じなら残す）
    void OnValidate()
    {
        var rig = LimbRigs.Get(body);
        if (rig.Length == 0) return;
        var old = new Dictionary<string, Transform[]>();
        if (chains != null) foreach (var c in chains) if (c != null && !string.IsNullOrEmpty(c.name)) old[c.name] = c.bones;
        var list = new ChainBinding[rig.Length];
        for (int i = 0; i < rig.Length; i++)
        {
            var bones = new Transform[rig[i].rest.Length - 1];
            if (old.TryGetValue(rig[i].name, out var prev) && prev != null)
                for (int k = 0; k < bones.Length && k < prev.Length; k++) bones[k] = prev[k];
            list[i] = new ChainBinding { name = rig[i].name, bones = bones };
        }
        chains = list;
    }

    void Reset() => OnValidate();

    void BuildProxy()
    {
        Transform limbs = motion.Find("Limbs");
        if (limbs == null)
        {
            limbs = new GameObject("Limbs").transform;
            limbs.SetParent(motion, false);
        }
        foreach (var chain in LimbRigs.Get(body))
        {
            var joints = new Transform[chain.rest.Length];
            Transform parent = limbs;
            for (int i = 0; i < chain.rest.Length; i++)
            {
                string name = $"{chain.name}_{i}";
                Transform t = parent.Find(name);
                if (t == null)
                {
                    t = new GameObject(name).transform;
                    t.SetParent(parent, false);
                }
                t.localPosition = i == 0 ? chain.rest[0] : chain.rest[i] - chain.rest[i - 1];
                t.localRotation = Quaternion.identity;
                t.localScale = Vector3.one;
                joints[i] = t;
                parent = t;
            }
            proxy[chain.name] = joints;
        }
    }

    void Start()
    {
        // 初期の向きを覚える（この時点ではモデルも代理の関節も初期姿勢）
        if (chains == null) return;
        Quaternion inv = Quaternion.Inverse(motion.rotation);
        foreach (var c in chains)
        {
            if (c == null || c.bones == null || !proxy.TryGetValue(c.name, out var joints)) continue;
            for (int i = 0; i < c.bones.Length && i + 1 < joints.Length; i++)
            {
                if (c.bones[i] == null) continue;
                Vector3 dir = Local(joints[i + 1]) - Local(joints[i]);
                segments.Add(new Segment
                {
                    bone = c.bones[i],
                    restRot = inv * c.bones[i].rotation,
                    restDir = dir.normalized,
                    from = joints[i],
                    to = joints[i + 1],
                });
            }
        }
    }

    Vector3 Local(Transform t) => motion.InverseTransformPoint(t.position);

    void LateUpdate()
    {
        // 付け根から先へ順に、各骨の向きを決める
        foreach (var s in segments)
        {
            Vector3 dir = Local(s.to) - Local(s.from);
            if (dir.sqrMagnitude < 1e-10f) continue;
            Quaternion delta = Quaternion.FromToRotation(s.restDir, dir.normalized);
            s.bone.rotation = motion.rotation * delta * s.restRot;
        }
    }
}
