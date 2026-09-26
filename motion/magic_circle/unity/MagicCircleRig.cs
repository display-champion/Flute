using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Events;
using UnityEngine.Playables;
using UnityEngine.Rendering;

/// <summary>
/// 魔法陣から玉やビームを撃つ演出を組み立てて再生する。
/// 構成（無ければ Awake で自動で作る。クリップが動かすのはこの名前の Transform）：
///   Circle（RingOuter / RingInner / Runes / Core）、Orb_0〜Orb_7、Beam
/// 見た目はそれぞれの子「Visual」に付く。属性ごとの味付け（ゆらめき・回転など）は Visual だけを動かすので、クリップの動きとぶつからない。
/// 原点は術者の足元、+Z が正面。AnimatorController は不要（Playables API で直接再生する）。
/// </summary>
[RequireComponent(typeof(Animator))]
public class MagicCircleRig : MonoBehaviour
{
    public enum Element { Fire, Ice, Thunder, Wind, Water, Earth, Light, Dark }

    [System.Serializable]
    public class MotionEvent : UnityEvent<string> { }

    [Tooltip("使う撃ち方のクリップ（MagicCircle_Beam など）")]
    public AnimationClip[] clips;

    [Tooltip("属性（色と味付け）")]
    public Element element = Element.Fire;

    [Tooltip("再生速度（1 = 元の速さ）")]
    public float speed = 1f;

    [Tooltip("始まったときに Clips の最初のクリップを再生する（確認用）")]
    public bool playOnStart = false;

    [Tooltip("終わったら同じクリップを繰り返す（確認用）")]
    public bool repeat = false;

    [Tooltip("クリップ内のイベント（Appear / Charge / Fire:0 / Impact:0 / BeamStart / BeamEnd / PillarStart / PillarEnd / Vanish）を受け取る")]
    public MotionEvent onMotionEvent;

    [Tooltip("クリップが終わったときに、そのクリップ名で呼ばれる")]
    public MotionEvent onMotionFinished;

    public const int OrbCount = 8;

    // 属性ごとの色（main = 本体、core = 芯）。確認用 HTML と同じ
    static readonly Dictionary<Element, (string main, string core)> Colors = new Dictionary<Element, (string, string)>
    {
        { Element.Fire, ("#f97316", "#fde68a") },
        { Element.Ice, ("#38bdf8", "#f0f9ff") },
        { Element.Thunder, ("#facc15", "#fffbeb") },
        { Element.Wind, ("#4ade80", "#f0fdf4") },
        { Element.Water, ("#3b82f6", "#dbeafe") },
        { Element.Earth, ("#a16207", "#fde68a") },
        { Element.Light, ("#fde047", "#ffffff") },
        { Element.Dark, ("#7c3aed", "#1e1b4b") },
    };

    PlayableGraph graph;
    AnimationClipPlayable playable;
    AnimationClip currentClip;
    bool finishedSent;

    Transform circle, beam;
    readonly Transform[] orbs = new Transform[OrbCount];
    readonly Transform[] orbVisuals = new Transform[OrbCount];
    readonly TrailRenderer[] trails = new TrailRenderer[OrbCount];
    Transform beamVisual, coreVisual;

    // 色を差し替えるために、役割ごとに Renderer を覚えておく
    readonly List<Renderer> mainRenderers = new List<Renderer>();
    readonly List<Renderer> coreRenderers = new List<Renderer>();
    readonly List<Renderer> ringRenderers = new List<Renderer>();
    readonly List<Material> ownedMaterials = new List<Material>();
    Material ringMaterial;
    Element appliedElement;
    bool built;

    /// <summary>今再生しているクリップ名（無ければ空）</summary>
    public string CurrentClip => currentClip != null ? currentClip.name : "";

    /// <summary>番号 i の玉の Transform（当たり判定や着弾エフェクトの位置に使う）</summary>
    public Transform GetOrb(int i) => i >= 0 && i < OrbCount ? orbs[i] : null;

    /// <summary>ビームの付け根（+Z 方向へ localScale.z の長さで伸びる）</summary>
    public Transform BeamTransform => beam;

    /// <summary>魔法陣の中心</summary>
    public Transform CircleTransform => circle;

    void Awake()
    {
        Build();
        HideAll();
    }

    void Start()
    {
        if (playOnStart && clips != null && clips.Length > 0 && clips[0] != null) Cast(clips[0].name);
    }

    void OnDestroy()
    {
        if (graph.IsValid()) graph.Destroy();
        foreach (var m in ownedMaterials) if (m != null) Destroy(m);
    }

    void OnDisable()
    {
        if (graph.IsValid()) graph.Destroy();
        currentClip = null;
    }

    /// <summary>
    /// 撃ち方のクリップを最初から再生する。clipName はクリップ名、または末尾（"Beam"、"Orb_Triple" など）。
    /// element を渡すと属性も切り替える。
    /// </summary>
    public bool Cast(string clipName, Element? newElement = null)
    {
        var clip = Find(clipName);
        if (clip == null)
        {
            Debug.LogWarning($"MagicCircleRig: クリップ「{clipName}」が見つかりません（Clips に入れてください）", this);
            return false;
        }
        if (newElement.HasValue) element = newElement.Value;
        Build();
        ApplyElement();
        if (graph.IsValid()) graph.Destroy();
        graph = PlayableGraph.Create($"MagicCircle_{name}");
        graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
        var output = AnimationPlayableOutput.Create(graph, "MagicCircle", GetComponent<Animator>());
        playable = AnimationClipPlayable.Create(graph, clip);
        playable.SetApplyFootIK(false);
        playable.SetTime(0);
        playable.SetTime(0);   // 2回呼ぶと前回との差分がリセットされ、最初のイベントが飛ばない
        playable.SetSpeed(speed);
        output.SetSourcePlayable(playable);
        graph.Play();
        currentClip = clip;
        finishedSent = false;
        foreach (var tr in trails) if (tr != null) tr.Clear();
        return true;
    }

    /// <summary>再生を止めて、全部を隠す</summary>
    public void Stop()
    {
        if (graph.IsValid()) graph.Destroy();
        currentClip = null;
        HideAll();
    }

    /// <summary>今クリップを再生中か</summary>
    public bool IsCasting => currentClip != null && !finishedSent;

    AnimationClip Find(string clipName)
    {
        if (clips == null) return null;
        foreach (var c in clips)
            if (c != null && (c.name == clipName || c.name.EndsWith("_" + clipName))) return c;
        return null;
    }

    void Update()
    {
        if (appliedElement != element && built) ApplyElement();
        if (currentClip == null || !graph.IsValid()) return;
        playable.SetSpeed(speed);
        if (playable.GetTime() >= currentClip.length)
        {
            if (!finishedSent)
            {
                finishedSent = true;
                onMotionFinished?.Invoke(currentClip.name);
            }
            if (repeat) Cast(currentClip.name);
            else playable.SetSpeed(0);   // 最後の姿（全部が大きさ 0）で止める
        }
    }

    // 属性の味付け（Visual だけを動かす）
    void LateUpdate()
    {
        if (!built) return;
        float t = Time.time;
        for (int i = 0; i < OrbCount; i++)
        {
            var v = orbVisuals[i];
            float s = orbs[i].localScale.x;
            Vector3 scale = Vector3.one, offset = Vector3.zero;
            Quaternion rot = Quaternion.identity;
            switch (element)
            {
                case Element.Fire: scale *= 1f + 0.12f * Mathf.Sin(t * 40f + i); break;
                case Element.Ice: rot = Quaternion.Euler(t * 90f + i * 40f, t * 140f + i * 25f, 0f); break;
                case Element.Thunder: offset = Random.insideUnitSphere * 0.08f; scale *= Random.Range(0.85f, 1.15f); break;
                case Element.Wind: rot = Quaternion.Euler(0f, 0f, t * 720f + i * 45f); scale = new Vector3(1.1f, 0.9f, 1f); break;
                case Element.Water: { float w = 0.08f * Mathf.Sin(t * 18f + i); scale = new Vector3(1f + w, 1f - w, 1f + w * 0.5f); break; }
                case Element.Earth: rot = Quaternion.Euler(t * 300f + i * 30f, 0f, 0f); break;
                case Element.Light: scale *= 1f + 0.06f * Mathf.Sin(t * 25f + i * 2f); break;
                case Element.Dark: scale *= 1f + 0.05f * Mathf.Sin(t * 9f + i); rot = Quaternion.Euler(0f, 0f, t * 60f); break;
            }
            v.localScale = scale;
            v.localPosition = offset;
            v.localRotation = rot;

            // 尾：玉が見えている間だけ伸ばす（消えたら消す。次に出たとき前の場所から線が伸びないように）
            var tr = trails[i];
            bool visible = s > 0.02f;
            if (!visible && tr.positionCount > 0) tr.Clear();
            tr.emitting = visible;
            tr.widthMultiplier = s * (element == Element.Fire ? 0.9f : 0.7f);
        }

        // ビーム：雷はちらつき、それ以外はゆるく脈打つ
        float bw = element == Element.Thunder ? Random.Range(0.75f, 1.25f) : 1f + 0.05f * Mathf.Sin(t * 30f);
        beamVisual.localScale = new Vector3(bw, bw, 1f);
        beamVisual.localPosition = element == Element.Thunder ? (Vector3)(Random.insideUnitCircle * 0.04f) : Vector3.zero;

        // 中心の光：光はきらめき、闇は揺らぐ
        float cs = element == Element.Light ? 1f + 0.15f * Mathf.Sin(t * 20f) : element == Element.Dark ? 1f + 0.1f * Mathf.Sin(t * 5f) : 1f;
        coreVisual.localScale = Vector3.one * cs;
        if (element == Element.Light && ringMaterial != null)
            SetColor(ringMaterial, Hex(Colors[element].main) * (0.8f + 0.2f * Mathf.Sin(t * 12f)));
    }

    // クリップの AnimationEvent（関数名 OnMotionEvent）から呼ばれる
    void OnMotionEvent(string eventName)
    {
        onMotionEvent?.Invoke(eventName);
    }

    // ---------------- 組み立て ----------------

    void HideAll()
    {
        if (!built) return;
        circle.localScale = Vector3.zero;
        beam.localScale = Vector3.zero;
        foreach (var o in orbs) o.localScale = Vector3.zero;
    }

    void Build()
    {
        if (built) return;
        built = true;

        circle = Child(transform, "Circle");
        var outer = Child(circle, "RingOuter");
        var inner = Child(circle, "RingInner");
        var runes = Child(circle, "Runes");
        var core = Child(circle, "Core");

        // 外の輪（太い輪と細い輪）
        AddMesh(Child(outer, "Visual"), RingMesh(1.0f, 0.045f), ringRenderers);
        AddMesh(Child(outer, "Visual2"), RingMesh(0.88f, 0.02f), ringRenderers);
        // 内の輪と六芒星（一緒に回る）
        var innerVisual = Child(inner, "Visual");
        AddMesh(innerVisual, RingMesh(0.55f, 0.03f), ringRenderers);
        AddMesh(Child(inner, "Hexagram"), HexagramMesh(0.86f, 0.02f), ringRenderers);
        // ルーン（外周の目盛り 24 本）
        AddMesh(Child(runes, "Visual"), TicksMesh(24, 0.9f, 0.03f), ringRenderers);
        // 中心の光（ふちへ向かって薄くなる円盤）
        coreVisual = Child(core, "Visual");
        AddMesh(coreVisual, GlowDiscMesh(0.5f), mainRenderers);
        AddMesh(Child(coreVisual, "Inner"), GlowDiscMesh(0.22f), coreRenderers);

        // 玉（直径 1 の球。クリップの大きさ = 直径）
        for (int i = 0; i < OrbCount; i++)
        {
            orbs[i] = Child(transform, $"Orb_{i}");
            orbVisuals[i] = Child(orbs[i], "Visual");
            AddMesh(orbVisuals[i], element == Element.Ice ? Crystal : Sphere, mainRenderers);
            var coreObj = Child(orbVisuals[i], "Core");
            coreObj.localScale = Vector3.one * 0.55f;
            AddMesh(coreObj, Sphere, coreRenderers);

            var tr = orbs[i].gameObject.GetComponent<TrailRenderer>();
            if (tr == null) tr = orbs[i].gameObject.AddComponent<TrailRenderer>();
            tr.time = 0.18f;
            tr.minVertexDistance = 0.05f;
            tr.widthCurve = AnimationCurve.Linear(0f, 1f, 1f, 0f);
            tr.shadowCastingMode = ShadowCastingMode.Off;
            tr.receiveShadows = false;
            tr.emitting = false;
            trails[i] = tr;
            mainRenderers.Add(tr);
        }

        // ビーム（付け根が原点、+Z 方向へ長さ 1・直径 1 の筒。クリップが (太さ, 太さ, 長さ) に伸ばす）
        beam = Child(transform, "Beam");
        beamVisual = Child(beam, "Visual");
        AddMesh(beamVisual, TubeMesh(20), mainRenderers);
        var beamCore = Child(beamVisual, "Core");
        beamCore.localScale = new Vector3(0.45f, 0.45f, 1f);
        AddMesh(beamCore, TubeMesh(12), coreRenderers);

        var animator = GetComponent<Animator>();
        if (animator != null) animator.Rebind();   // 作った子をアニメーションの対象として認識させる
        appliedElement = (Element)(-1);
        ApplyElement();
    }

    static Transform Child(Transform parent, string childName)
    {
        var found = parent.Find(childName);
        if (found != null) return found;
        var t = new GameObject(childName).transform;
        t.SetParent(parent, false);
        return t;
    }

    static void AddMesh(Transform t, Mesh mesh, List<Renderer> role)
    {
        var mf = t.GetComponent<MeshFilter>();
        if (mf == null) mf = t.gameObject.AddComponent<MeshFilter>();
        mf.sharedMesh = mesh;
        var mr = t.GetComponent<MeshRenderer>();
        if (mr == null) mr = t.gameObject.AddComponent<MeshRenderer>();
        mr.shadowCastingMode = ShadowCastingMode.Off;
        mr.receiveShadows = false;
        role.Add(mr);
    }

    // ---------------- 色（属性） ----------------

    void ApplyElement()
    {
        if (appliedElement == element) return;
        appliedElement = element;
        foreach (var m in ownedMaterials) if (m != null) Destroy(m);
        ownedMaterials.Clear();

        var (mainHex, coreHex) = Colors[element];
        Color main = Hex(mainHex), coreCol = Hex(coreHex);
        // 土は光らせず（通常の半透明）、闇の芯は暗い色なので半透明で重ねる
        bool additive = element != Element.Earth;
        bool coreAdditive = additive && element != Element.Dark;

        var mainMat = MakeMaterial(main, additive);
        var coreMat = MakeMaterial(coreCol, coreAdditive);
        ringMaterial = MakeMaterial(main, additive);
        foreach (var r in mainRenderers) r.sharedMaterial = mainMat;
        foreach (var r in coreRenderers) r.sharedMaterial = coreMat;
        foreach (var r in ringRenderers) r.sharedMaterial = ringMaterial;

        // 尾は付け根ほど濃く、先ほど薄く（炎は赤みを帯びる）
        var tail = element == Element.Fire ? Hex("#dc2626") : main;
        var g = new Gradient();
        g.SetKeys(new[] { new GradientColorKey(main, 0f), new GradientColorKey(tail, 1f) },
                  new[] { new GradientAlphaKey(0.8f, 0f), new GradientAlphaKey(0f, 1f) });
        foreach (var tr in trails) if (tr != null) { tr.colorGradient = g; tr.time = element == Element.Fire ? 0.26f : 0.18f; }

        // 氷は結晶、それ以外は球
        foreach (var v in orbVisuals)
            if (v != null) v.GetComponent<MeshFilter>().sharedMesh = element == Element.Ice ? Crystal : Sphere;
    }

    static Shader FindShader(bool additive, out bool urp)
    {
        urp = false;
        if (GraphicsSettings.currentRenderPipeline != null)
        {
            var s = Shader.Find("Universal Render Pipeline/Particles/Unlit");
            if (s != null) { urp = true; return s; }
        }
        var legacy = Shader.Find(additive ? "Legacy Shaders/Particles/Additive" : "Legacy Shaders/Particles/Alpha Blended");
        if (legacy != null) return legacy;
        return Shader.Find("Sprites/Default");
    }

    Material MakeMaterial(Color color, bool additive)
    {
        var shader = FindShader(additive, out bool urp);
        var m = new Material(shader) { name = $"MagicCircle_{element}", renderQueue = 3000 };
        if (urp)
        {
            // 透明＋加算（または通常の半透明）にする
            m.SetFloat("_Surface", 1f);
            m.SetFloat("_Blend", additive ? 2f : 0f);
            m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
            m.SetFloat("_DstBlend", additive ? (float)BlendMode.One : (float)BlendMode.OneMinusSrcAlpha);
            m.SetFloat("_ZWrite", 0f);
            m.SetFloat("_Cull", (float)CullMode.Off);
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.SetOverrideTag("RenderType", "Transparent");
        }
        SetColor(m, color);
        ownedMaterials.Add(m);
        return m;
    }

    static void SetColor(Material m, Color c)
    {
        if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
        if (m.HasProperty("_TintColor")) m.SetColor("_TintColor", c * 0.5f);   // Legacy の加算は色が 2 倍になる
        if (m.HasProperty("_Color")) m.SetColor("_Color", c);
    }

    static Color Hex(string hex)
    {
        ColorUtility.TryParseHtmlString(hex, out var c);
        return c;
    }

    static Mesh sphereMesh, crystalMesh;
    static Mesh Sphere => sphereMesh != null ? sphereMesh : (sphereMesh = SphereMesh(16, 12));
    static Mesh Crystal => crystalMesh != null ? crystalMesh : (crystalMesh = OctahedronMesh());

    // ---------------- メッシュ（XY 平面が魔法陣の面、+Z が正面） ----------------

    static Mesh RingMesh(float radius, float width, int segments = 96)
    {
        var v = new List<Vector3>(); var tri = new List<int>(); var col = new List<Color>();
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments;
            var d = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f);
            v.Add(d * (radius - width / 2f)); v.Add(d * (radius + width / 2f));
            col.Add(Color.white); col.Add(Color.white);
            if (i < segments) { int k = i * 2; tri.AddRange(new[] { k, k + 1, k + 3, k, k + 3, k + 2 }); }
        }
        return Finish("Ring", v, tri, col);
    }

    static void Segment(List<Vector3> v, List<int> tri, List<Color> col, Vector3 a, Vector3 b, float width)
    {
        var n = Vector3.Cross(b - a, Vector3.forward).normalized * (width / 2f);
        int k = v.Count;
        v.Add(a - n); v.Add(a + n); v.Add(b + n); v.Add(b - n);
        for (int i = 0; i < 4; i++) col.Add(Color.white);
        tri.AddRange(new[] { k, k + 1, k + 2, k, k + 2, k + 3 });
    }

    static Mesh HexagramMesh(float radius, float width)
    {
        var v = new List<Vector3>(); var tri = new List<int>(); var col = new List<Color>();
        for (int k = 0; k < 2; k++)
            for (int i = 0; i < 3; i++)
            {
                float a0 = (k * 60 + i * 120 + 90) * Mathf.Deg2Rad, a1 = (k * 60 + (i + 1) * 120 + 90) * Mathf.Deg2Rad;
                Segment(v, tri, col, new Vector3(Mathf.Cos(a0), Mathf.Sin(a0)) * radius, new Vector3(Mathf.Cos(a1), Mathf.Sin(a1)) * radius, width);
            }
        return Finish("Hexagram", v, tri, col);
    }

    static Mesh TicksMesh(int count, float from, float width)
    {
        var v = new List<Vector3>(); var tri = new List<int>(); var col = new List<Color>();
        for (int i = 0; i < count; i++)
        {
            float a = i * Mathf.PI * 2f / count;
            var d = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f);
            Segment(v, tri, col, d * from, d * (i % 3 != 0 ? 0.95f : 0.99f), width);
        }
        return Finish("Runes", v, tri, col);
    }

    static Mesh GlowDiscMesh(float radius, int segments = 32)
    {
        var v = new List<Vector3> { Vector3.zero }; var tri = new List<int>();
        var col = new List<Color> { Color.white };
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments;
            v.Add(new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * radius);
            col.Add(new Color(1f, 1f, 1f, 0f));
            if (i < segments) tri.AddRange(new[] { 0, i + 2, i + 1 });
        }
        return Finish("Glow", v, tri, col);
    }

    static Mesh SphereMesh(int lon, int lat)
    {
        var v = new List<Vector3>(); var tri = new List<int>(); var col = new List<Color>();
        for (int y = 0; y <= lat; y++)
        {
            float p = Mathf.PI * y / lat;
            for (int x = 0; x <= lon; x++)
            {
                float a = Mathf.PI * 2f * x / lon;
                v.Add(new Vector3(Mathf.Sin(p) * Mathf.Cos(a), Mathf.Cos(p), Mathf.Sin(p) * Mathf.Sin(a)) * 0.5f);
                col.Add(Color.white);
            }
        }
        for (int y = 0; y < lat; y++)
            for (int x = 0; x < lon; x++)
            {
                int k = y * (lon + 1) + x;
                tri.AddRange(new[] { k, k + 1, k + lon + 1, k + 1, k + lon + 2, k + lon + 1 });
            }
        return Finish("Orb", v, tri, col);
    }

    static Mesh OctahedronMesh()
    {
        // 縦に少し長い八面体（氷の結晶）
        var p = new[] { new Vector3(0, 0.7f, 0), new Vector3(0, -0.7f, 0), new Vector3(0.45f, 0, 0), new Vector3(-0.45f, 0, 0), new Vector3(0, 0, 0.45f), new Vector3(0, 0, -0.45f) };
        var v = new List<Vector3>(p); var col = new List<Color>();
        foreach (var _ in p) col.Add(Color.white);
        var tri = new List<int> { 0, 2, 4, 0, 4, 3, 0, 3, 5, 0, 5, 2, 1, 4, 2, 1, 3, 4, 1, 5, 3, 1, 2, 5 };
        return Finish("Crystal", v, tri, col);
    }

    static Mesh TubeMesh(int segments)
    {
        var v = new List<Vector3>(); var tri = new List<int>(); var col = new List<Color>();
        for (int i = 0; i <= segments; i++)
        {
            float a = i * Mathf.PI * 2f / segments;
            var d = new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * 0.5f;
            v.Add(d); v.Add(d + Vector3.forward);
            col.Add(Color.white); col.Add(new Color(1f, 1f, 1f, 0.6f));   // 先の方を少し薄く
            if (i < segments) { int k = i * 2; tri.AddRange(new[] { k, k + 1, k + 3, k, k + 3, k + 2 }); }
        }
        // 先端のふた
        int c = v.Count; v.Add(Vector3.forward); col.Add(new Color(1f, 1f, 1f, 0.6f));
        for (int i = 0; i < segments; i++) tri.AddRange(new[] { c, i * 2 + 1, i * 2 + 3 });
        return Finish("Beam", v, tri, col);
    }

    static Mesh Finish(string meshName, List<Vector3> v, List<int> tri, List<Color> col)
    {
        // 裏からも見えるように、面を裏返したものも足す（加算シェーダーが裏面を消す場合の保険）
        int n = tri.Count;
        for (int i = 0; i < n; i += 3) tri.AddRange(new[] { tri[i], tri[i + 2], tri[i + 1] });
        var m = new Mesh { name = meshName };
        m.SetVertices(v);
        m.SetColors(col);
        m.SetTriangles(tri, 0);
        m.RecalculateBounds();
        return m;
    }
}
