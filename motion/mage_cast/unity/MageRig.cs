using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Events;
using UnityEngine.Playables;

/// <summary>
/// 魔術師（とんがり帽子の棒人間）を組み立てて MageCast.anim を再生する。
/// 両腕を掲げてゆらゆら魔力を溜め、胸の前へ振り下ろして術を発動する。
/// 空の GameObject に付けて Clip に MageCast.anim を入れるだけで動く（AnimatorController 不要）。
/// </summary>
[RequireComponent(typeof(Animator))]
public class MageRig : MonoBehaviour
{
    [Tooltip("MageCast.anim")]
    public AnimationClip clip;

    [Tooltip("再生速度（1 = 元の速さ）")]
    [Range(0.1f, 2f)] public float speed = 1f;

    [Tooltip("オフにすると1回だけ再生して最後の姿勢で止まる")]
    public bool loop = true;

    [Tooltip("魔力の玉に点光源を付ける")]
    public bool orbLight = true;

    [Tooltip("両腕を掲げて魔力を溜め始めた瞬間")]
    public UnityEvent onGatherStart;

    [Tooltip("胸の前へ振り下ろして術が発動した瞬間（ここで魔法を出す）")]
    public UnityEvent onCast;

    public Color bodyColor = new Color(0.11f, 0.10f, 0.09f);
    public Color hatColor = new Color(0.30f, 0.11f, 0.58f);
    public Color accentColor = new Color(0.98f, 0.45f, 0.09f);
    public Color magicColor = new Color(0.55f, 0.36f, 0.96f);

    struct Line
    {
        public Transform from, to;
        public LineRenderer renderer;
    }

    readonly List<Line> lines = new List<Line>();
    PlayableGraph graph;
    AnimationClipPlayable playable;
    Transform orb;
    Light orbLightComponent;
    double lastClipTime;

    void Awake()
    {
        Build();
    }

    void OnEnable()
    {
        if (clip == null)
        {
            Debug.LogWarning("MageRig: Clip に MageCast.anim を設定してください", this);
            return;
        }
        graph = PlayableGraph.Create("MageCast");
        graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
        var output = AnimationPlayableOutput.Create(graph, "MageCast", GetComponent<Animator>());
        playable = AnimationClipPlayable.Create(graph, clip);
        output.SetSourcePlayable(playable);
        graph.Play();
        lastClipTime = 0;
    }

    void OnDisable()
    {
        if (graph.IsValid()) graph.Destroy();
    }

    /// <summary>最初から再生し直す（loop オフで1回ずつ撃たせたいとき用）</summary>
    public void Cast()
    {
        if (!playable.IsValid()) return;
        playable.SetTime(0);
        playable.SetTime(0);   // 2回呼ぶと前フレームとの差分（ルートモーション等）がリセットされる
        lastClipTime = 0;
    }

    void Update()
    {
        if (!playable.IsValid()) return;
        playable.SetSpeed(speed);
        double t = playable.GetTime();
        double cycle = MageRigBones.CycleSeconds;
        if (!loop && t >= cycle)
        {
            playable.SetTime(cycle - 1e-4);
            playable.SetSpeed(0);
            t = cycle - 1e-4;
        }
        if (Crossed(lastClipTime, t, MageRigBones.GatherStartTime, cycle)) onGatherStart?.Invoke();
        if (Crossed(lastClipTime, t, MageRigBones.CastTime, cycle)) onCast?.Invoke();
        lastClipTime = t;
    }

    static bool Crossed(double from, double to, double at, double cycle)
    {
        return System.Math.Floor((to - at) / cycle) > System.Math.Floor((from - at) / cycle);
    }

    void LateUpdate()
    {
        foreach (var l in lines)
        {
            l.renderer.SetPosition(0, l.from.position);
            l.renderer.SetPosition(1, l.to.position);
        }
        if (orbLightComponent != null) orbLightComponent.intensity = orb.localScale.x * 12f;
    }

    void Build()
    {
        var mats = new Material[] { Lit(bodyColor), Lit(hatColor), Unlit(accentColor), Unlit(magicColor) };
        var lineMat = Unlit(bodyColor);
        var map = new Dictionary<string, Transform>();

        foreach (var b in MageRigBones.Bones)
        {
            int slash = b.path.LastIndexOf('/');
            Transform parent = slash < 0 ? transform : map[b.path.Substring(0, slash)];
            string name = b.path.Substring(slash + 1);
            Transform t = parent.Find(name);
            if (t == null)
            {
                t = new GameObject(name).transform;
                t.SetParent(parent, false);
            }
            t.localPosition = b.restPosition;
            t.localRotation = b.restRotation;
            t.localScale = b.restScale;
            map[b.path] = t;

            switch (b.vis)
            {
                case MageRigBones.Vis.Sphere:
                    AddSphere(t, b.size, mats[b.color]);
                    break;
                case MageRigBones.Vis.Line:
                    lines.Add(new Line { from = parent, to = t, renderer = AddLine(t, b.size, lineMat) });
                    break;
                case MageRigBones.Vis.Hat:
                    AddSphere(t, b.size, mats[0]);
                    AddHat(t, b.size, mats[1], mats[2]);
                    break;
            }
        }

        orb = map["Orb"];
        if (orbLight && orb.Find("Light") == null)
        {
            var go = new GameObject("Light");
            go.transform.SetParent(orb, false);
            orbLightComponent = go.AddComponent<Light>();
            orbLightComponent.type = LightType.Point;
            orbLightComponent.color = magicColor;
            orbLightComponent.range = 4f;
            orbLightComponent.intensity = 0f;
        }
    }

    static void AddSphere(Transform parent, float radius, Material mat)
    {
        if (parent.Find("Mesh") != null) return;
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = "Mesh";
        Destroy(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.localScale = Vector3.one * (radius * 2f);
        go.GetComponent<Renderer>().sharedMaterial = mat;
    }

    // とんがり帽子：つば・円錐（先端は少し後ろへ）・アクセント色の帯。頭の骨は +Y が頭頂、+Z が顔の向き
    static void AddHat(Transform head, float headRadius, Material hatMat, Material bandMat)
    {
        if (head.Find("Hat") != null) return;
        float baseY = headRadius * 0.55f;
        float r = MageRigBones.HatRadius;
        var hat = new GameObject("Hat").transform;
        hat.SetParent(head, false);
        AddMesh(hat, "Brim", Frustum(r * 1.45f, r * 1.4f, 0.012f, 0f, 28), new Vector3(0f, baseY - 0.006f, 0f), hatMat);
        AddMesh(hat, "Cone", Frustum(r, 0f, MageRigBones.HatHeight, -0.1f, 24), new Vector3(0f, baseY, 0f), hatMat);
        AddMesh(hat, "Band", Frustum(r * 0.99f, r * 0.9f, 0.045f, -0.013f, 24), new Vector3(0f, baseY + 0.008f, 0f), bandMat);
    }

    static void AddMesh(Transform parent, string name, Mesh mesh, Vector3 localPos, Material mat)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        go.AddComponent<MeshRenderer>().sharedMaterial = mat;
    }

    // 下面の半径 r0、上面の半径 r1、高さ h の錐台（上面の中心は Z 方向へ tipZ ずれる）。r1 = 0 で円錐
    static Mesh Frustum(float r0, float r1, float h, float tipZ, int n)
    {
        var verts = new List<Vector3>();
        var tris = new List<int>();
        for (int i = 0; i <= n; i++)
        {
            float a = i * Mathf.PI * 2f / n;
            var d = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
            verts.Add(d * r0);
            verts.Add(d * r1 + new Vector3(0f, h, tipZ));
        }
        for (int i = 0; i < n; i++)
        {
            int k = i * 2;
            tris.AddRange(new[] { k, k + 1, k + 2, k + 2, k + 1, k + 3 });
        }
        // 底面（下向き）と上面（上向き）のふた。陰影が側面と混ざらないよう頂点は別に持つ
        int c0 = verts.Count; verts.Add(Vector3.zero);
        int c1 = verts.Count; verts.Add(new Vector3(0f, h, tipZ));
        int ring = verts.Count;
        for (int i = 0; i <= n; i++)
        {
            float a = i * Mathf.PI * 2f / n;
            var d = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a));
            verts.Add(d * r0);
            verts.Add(d * r1 + new Vector3(0f, h, tipZ));
        }
        for (int i = 0; i < n; i++)
        {
            int k = ring + i * 2;
            tris.AddRange(new[] { c0, k, k + 2 });
            tris.AddRange(new[] { c1, k + 3, k + 1 });
        }
        var mesh = new Mesh { name = "Frustum" };
        mesh.SetVertices(verts);
        mesh.SetTriangles(tris, 0);
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        return mesh;
    }

    static LineRenderer AddLine(Transform owner, float width, Material mat)
    {
        var go = new GameObject("Line");
        go.transform.SetParent(owner, false);
        var lr = go.AddComponent<LineRenderer>();
        lr.useWorldSpace = true;
        lr.positionCount = 2;
        lr.widthMultiplier = width;
        lr.numCapVertices = 4;
        lr.sharedMaterial = mat;
        return lr;
    }

    // URP / HDRP / ビルトインのどれでも見えるシェーダーを順に探す
    static Material Make(Color color, params string[] shaders)
    {
        Shader shader = null;
        foreach (var s in shaders)
        {
            shader = Shader.Find(s);
            if (shader != null) break;
        }
        var mat = new Material(shader);
        mat.color = color;
        if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", color);
        if (mat.HasProperty("_UnlitColor")) mat.SetColor("_UnlitColor", color);
        return mat;
    }

    static Material Lit(Color c) => Make(c, "Universal Render Pipeline/Lit", "HDRP/Lit", "Standard");
    static Material Unlit(Color c) => Make(c, "Universal Render Pipeline/Unlit", "HDRP/Unlit", "Unlit/Color", "Sprites/Default");
}
