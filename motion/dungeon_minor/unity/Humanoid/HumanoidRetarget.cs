using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 見えない代理の骨組み（子「Proxy」。EnemyMotion がクリップで関節の位置を動かす）の姿勢を、
/// 人型モデル（Rig が Humanoid）のボーンへ毎フレーム写す。
/// 骨の「向き」だけを写すので、モデルの体格や骨の軸の向きが違っても使える。
/// 腰・胸・頭は向き全体（ひねりを含む）、腕・脚・首・背骨は骨の向き（ねじれは元のまま）を写す。
/// 構成：この GameObject（Animator ＋ EnemyMotion ＋ HumanoidRetarget）→ 子にモデル（正面 +Z、足元が原点）
/// </summary>
[DefaultExecutionOrder(-100)]   // EnemyMotion より先に Proxy を作る
public class HumanoidRetarget : MonoBehaviour
{
    [Tooltip("人型モデルの Animator（Humanoid）。空なら子から自動で探す")]
    public Animator target;

    [Tooltip("腰の上下・前後の動きの大きさ（1 = 脚の長さの比に合わせる）")]
    public float hipsMotionScale = 1f;

    struct Limb
    {
        public Transform bone;
        public Quaternion restRot;     // この GameObject から見た初期の向き
        public Vector3 restDir;        // この GameObject から見た初期の骨の向き（次の関節へ）
        public Transform from, to;     // 代理の骨組みの関節
    }

    struct Frame
    {
        public Transform bone;
        public Quaternion restRot;
        public Quaternion restBasis;   // 初期の「上・右」から作った向き
    }

    readonly Dictionary<string, Transform> proxy = new Dictionary<string, Transform>();
    readonly List<Limb> limbs = new List<Limb>();
    Frame hips, chest, head;
    Vector3 hipsRestPos, proxyHipsRest;
    float legRatio = 1f;
    bool ready;

    void Awake()
    {
        BuildProxy();
    }

    void BuildProxy()
    {
        Transform root = transform.Find("Proxy");
        if (root == null)
        {
            root = new GameObject("Proxy").transform;
            root.SetParent(transform, false);
        }
        proxy["Proxy"] = root;
        for (int i = 0; i < HumanoidProxyBones.Paths.Length; i++)
        {
            string path = HumanoidProxyBones.Paths[i];
            int slash = path.LastIndexOf('/');
            Transform parent = proxy[path.Substring(0, slash)];
            string name = path.Substring(slash + 1);
            Transform t = parent.Find(name);
            if (t == null)
            {
                t = new GameObject(name).transform;
                t.SetParent(parent, false);
            }
            t.localPosition = HumanoidProxyBones.RestLocalPositions[i];
            t.localRotation = Quaternion.identity;
            proxy[name] = t;
        }
    }

    void Start()
    {
        if (target == null)
        {
            var self = GetComponent<Animator>();
            foreach (var a in GetComponentsInChildren<Animator>())
                if (a != self && a.isHuman) { target = a; break; }
        }
        if (target == null || !target.isHuman)
        {
            Debug.LogWarning("HumanoidRetarget: 人型（Humanoid）の Animator が見つかりません。Target に設定してください", this);
            return;
        }
        Capture();
    }

    Transform B(HumanBodyBones b) => target.GetBoneTransform(b);
    Vector3 LP(Transform t) => transform.InverseTransformPoint(t.position);
    Quaternion LR(Transform t) => Quaternion.Inverse(transform.rotation) * t.rotation;
    Vector3 PP(string name) => transform.InverseTransformPoint(proxy[name].position);

    static Quaternion Basis(Vector3 up, Vector3 right)
    {
        return Quaternion.LookRotation(Vector3.Cross(right, up), up);
    }

    void Capture()
    {
        Transform hipsT = B(HumanBodyBones.Hips);
        Transform spine = B(HumanBodyBones.Spine);
        Transform chestTop = B(HumanBodyBones.UpperChest) ?? B(HumanBodyBones.Chest) ?? spine;
        Transform neck = B(HumanBodyBones.Neck);
        Transform headT = B(HumanBodyBones.Head);
        Transform lUpLeg = B(HumanBodyBones.LeftUpperLeg), rUpLeg = B(HumanBodyBones.RightUpperLeg);
        Transform lUpArm = B(HumanBodyBones.LeftUpperArm), rUpArm = B(HumanBodyBones.RightUpperArm);
        Transform neckOrHead = neck != null ? neck : headT;

        hips = new Frame { bone = hipsT, restRot = LR(hipsT), restBasis = Basis(LP(spine) - LP(hipsT), LP(rUpLeg) - LP(lUpLeg)) };
        chest = new Frame { bone = chestTop, restRot = LR(chestTop), restBasis = Basis(LP(neckOrHead) - LP(chestTop), LP(rUpArm) - LP(lUpArm)) };
        head = new Frame { bone = headT, restRot = LR(headT), restBasis = Basis(LP(headT) - LP(neckOrHead), Vector3.Cross(LP(headT) - LP(neckOrHead), Vector3.forward)) };

        // 背骨：Spine の向きだけ（胸の骨が別にあるとき）
        if (chestTop != spine) AddLimb(spine, chestTop, "Spine", "Chest");
        if (neck != null) AddLimb(neck, headT, "Neck", "Head");
        foreach (var side in new[] { "Left", "Right" })
        {
            bool l = side == "Left";
            Transform up = B(l ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
            Transform lo = B(l ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
            Transform hand = B(l ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
            Transform finger = B(l ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
            AddLimb(up, lo, side + "UpperArm", side + "LowerArm");
            AddLimb(lo, hand, side + "LowerArm", side + "Hand");
            if (finger != null) AddLimb(hand, finger, side + "Hand", side + "HandTip");
            Transform thigh = B(l ? HumanBodyBones.LeftUpperLeg : HumanBodyBones.RightUpperLeg);
            Transform shin = B(l ? HumanBodyBones.LeftLowerLeg : HumanBodyBones.RightLowerLeg);
            Transform foot = B(l ? HumanBodyBones.LeftFoot : HumanBodyBones.RightFoot);
            Transform toes = B(l ? HumanBodyBones.LeftToes : HumanBodyBones.RightToes);
            AddLimb(thigh, shin, side + "UpperLeg", side + "LowerLeg");
            AddLimb(shin, foot, side + "LowerLeg", side + "Foot");
            if (toes != null) AddLimb(foot, toes, side + "Foot", side + "Toes");
        }

        // 腰の動きの大きさは脚の長さの比で合わせる
        hipsRestPos = LP(hipsT);
        proxyHipsRest = PP("Hips");
        float modelLeg = Vector3.Distance(LP(lUpLeg), LP(B(HumanBodyBones.LeftLowerLeg))) + Vector3.Distance(LP(B(HumanBodyBones.LeftLowerLeg)), LP(B(HumanBodyBones.LeftFoot)));
        float proxyLeg = Vector3.Distance(PP("LeftUpperLeg"), PP("LeftLowerLeg")) + Vector3.Distance(PP("LeftLowerLeg"), PP("LeftFoot"));
        legRatio = proxyLeg > 1e-4f ? modelLeg / proxyLeg : 1f;
        ready = true;
    }

    void AddLimb(Transform bone, Transform child, string from, string to)
    {
        if (bone == null || child == null) return;
        limbs.Add(new Limb
        {
            bone = bone,
            restRot = LR(bone),
            restDir = (LP(child) - LP(bone)).normalized,
            from = proxy[from],
            to = proxy[to],
        });
    }

    void ApplyFrame(Frame f, Vector3 up, Vector3 right)
    {
        if (f.bone == null) return;
        Quaternion delta = Basis(up, right) * Quaternion.Inverse(f.restBasis);
        f.bone.rotation = transform.rotation * delta * f.restRot;
    }

    void LateUpdate()
    {
        if (!ready) return;

        // 腰：位置と向き全体
        Vector3 hipsPos = hipsRestPos + (PP("Hips") - proxyHipsRest) * legRatio * hipsMotionScale;
        hips.bone.position = transform.TransformPoint(hipsPos);
        ApplyFrame(hips, PP("Spine") - PP("Hips"), PP("RightUpperLeg") - PP("LeftUpperLeg"));

        // 背骨・胸・首・頭・腕・脚（親から順に。各骨の向きを絶対値で決める）
        foreach (var l in limbs)
        {
            if (l.from == proxy["Spine"]) ApplyLimb(l);
        }
        ApplyFrame(chest, PP("Neck") - PP("Chest"), PP("RightUpperArm") - PP("LeftUpperArm"));
        foreach (var l in limbs)
        {
            if (l.from == proxy["Spine"]) continue;
            ApplyLimb(l);
            if (l.from == proxy["Neck"])
            {
                Vector3 up = PP("Head") - PP("Neck");
                Vector3 fwd = PP("HeadForward") - PP("Head");
                ApplyFrame(head, up, Vector3.Cross(up, fwd));
            }
        }
        if (proxy.ContainsKey("Neck") && !HasNeckLimb())
        {
            Vector3 up = PP("Head") - PP("Neck");
            ApplyFrame(head, up, Vector3.Cross(up, PP("HeadForward") - PP("Head")));
        }
    }

    bool HasNeckLimb()
    {
        foreach (var l in limbs) if (l.from == proxy["Neck"]) return true;
        return false;
    }

    void ApplyLimb(Limb l)
    {
        Vector3 dir = PP(l.to.name) - PP(l.from.name);
        if (dir.sqrMagnitude < 1e-8f) return;
        Quaternion delta = Quaternion.FromToRotation(l.restDir, dir.normalized);
        l.bone.rotation = transform.rotation * delta * l.restRot;
    }
}
