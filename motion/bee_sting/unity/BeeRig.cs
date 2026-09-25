using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Events;
using UnityEngine.Playables;

/// <summary>
/// 蜂を組み立てて BeeSting.anim（ホバリング → 構え → しっぽの針で突き刺し → 戻る）を再生する。
/// 空の GameObject に付けて Clip に BeeSting.anim を入れるだけで動く（AnimatorController 不要）。
/// </summary>
[RequireComponent(typeof(Animator))]
public class BeeRig : MonoBehaviour
{
    [Tooltip("BeeSting.anim")]
    public AnimationClip clip;

    [Tooltip("再生速度（1 = 元の速さ）")]
    [Range(0.05f, 2f)] public float speed = 1f;

    [Tooltip("前方（+Z）へ飛んで迫ってくる。オフならその場で攻撃を繰り返す")]
    public bool approach = false;

    [Tooltip("迫ってくる速さ (m/秒)")]
    public float approachSpeed = 2.3f;

    [Tooltip("この距離を進んだらスタート地点へ戻る (m)")]
    public float approachDistance = 20f;

    [Tooltip("針が最も突き出た瞬間に呼ばれる（ダメージ判定などに）")]
    public UnityEvent onSting;

    public Color black = new Color(0.13f, 0.12f, 0.11f);
    public Color yellow = new Color(0.95f, 0.72f, 0.02f);
    public Color amber = new Color(0.85f, 0.56f, 0.02f);
    public Color accent = new Color(0.98f, 0.45f, 0.09f);
    public Color wing = new Color(0.65f, 0.82f, 0.95f, 0.35f);

    struct Line
    {
        public Transform from, to;
        public LineRenderer renderer;
    }

    readonly List<Line> lines = new List<Line>();
    PlayableGraph graph;
    AnimationClipPlayable playable;
    Vector3 startPosition;
    float traveled;
    double lastClipTime;

    void Awake()
    {
        startPosition = transform.position;
        Build();
    }

    void OnEnable()
    {
        if (clip == null)
        {
            Debug.LogWarning("BeeRig: Clip に BeeSting.anim を設定してください", this);
            return;
        }
        graph = PlayableGraph.Create("BeeSting");
        graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
        var output = AnimationPlayableOutput.Create(graph, "BeeSting", GetComponent<Animator>());
        playable = AnimationClipPlayable.Create(graph, clip);
        output.SetSourcePlayable(playable);
        graph.Play();
        lastClipTime = 0;
    }

    void OnDisable()
    {
        if (graph.IsValid()) graph.Destroy();
    }

    void Update()
    {
        if (playable.IsValid())
        {
            playable.SetSpeed(speed);
            // 針を突き出す時刻をまたいだらイベント
            double t = playable.GetTime();
            double cycle = BeeRigBones.CycleSeconds;
            double hit = BeeRigBones.HitTime;
            if (System.Math.Floor((t - hit) / cycle) > System.Math.Floor((lastClipTime - hit) / cycle)) onSting?.Invoke();
            lastClipTime = t;
        }

        if (approach)
        {
            traveled += approachSpeed * speed * Time.deltaTime;
            if (traveled > approachDistance) traveled = 0f;
            transform.position = startPosition + transform.forward * traveled;
        }
    }

    void LateUpdate()
    {
        foreach (var l in lines)
        {
            l.renderer.SetPosition(0, l.from.position);
            l.renderer.SetPosition(1, l.to.position);
        }
    }

    void Build()
    {
        var mats = new Material[]
        {
            Lit(black), Lit(yellow), Lit(amber), Unlit(accent), Transparent(wing),
        };
        var unlitBlack = Unlit(black);
        var map = new Dictionary<string, Transform>();

        foreach (var b in BeeRigBones.Bones)
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
            map[b.path] = t;

            switch (b.vis)
            {
                case BeeRigBones.Vis.Sphere:
                    AddMesh(t, "Mesh", new Vector3(0f, b.offset, 0f), Vector3.one * (b.size * 2f), mats[b.color]);
                    break;
                case BeeRigBones.Vis.Wing:
                    // 羽の面は骨の Y（付け根→先端）と Z（前縁→後縁）。X 方向に薄くつぶす
                    AddMesh(t, "Mesh", new Vector3(0f, b.size / 2f, b.size2 * 0.12f), new Vector3(0.006f, b.size, b.size2), mats[b.color]);
                    break;
                case BeeRigBones.Vis.Line:
                    lines.Add(new Line { from = parent, to = t, renderer = AddLine(t, b.size, b.color == 3 ? mats[3] : unlitBlack) });
                    break;
            }
        }
    }

    static void AddMesh(Transform parent, string name, Vector3 localPos, Vector3 scale, Material mat)
    {
        if (parent.Find(name) != null) return;
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = name;
        Destroy(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.localPosition = localPos;
        go.transform.localScale = scale;
        go.GetComponent<Renderer>().sharedMaterial = mat;
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
    static Material Transparent(Color c) => Make(c, "Sprites/Default", "Unlit/Color");
}
