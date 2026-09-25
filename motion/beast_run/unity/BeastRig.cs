using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

/// <summary>
/// 獣走りの棒人間を組み立てて BeastRun.anim を再生する。
/// 空の GameObject に付けて Clip に BeastRun.anim を入れるだけで動く（AnimatorController 不要）。
/// </summary>
[RequireComponent(typeof(Animator))]
public class BeastRig : MonoBehaviour
{
    [Tooltip("BeastRun.anim")]
    public AnimationClip clip;

    [Tooltip("再生速度（1 = 元の速さ）")]
    [Range(0.1f, 2f)] public float speed = 1f;

    [Tooltip("前方（+Z）へ走って迫ってくる。オフならその場で走る")]
    public bool approach = true;

    [Tooltip("この距離を走ったらスタート地点へ戻る (m)")]
    public float approachDistance = 30f;

    public Color bodyColor = new Color(0.11f, 0.10f, 0.09f);
    public Color accentColor = new Color(0.98f, 0.57f, 0.24f);
    public float lineWidth = 0.05f;

    [Tooltip("任意。空なら上の色で自動生成（ビルドでシェーダーが見つからない場合はここに指定）")]
    public Material bodyMaterialOverride;
    public Material accentMaterialOverride;

    struct Bone
    {
        public Transform from, to;
        public LineRenderer line;
    }

    readonly List<Bone> bones = new List<Bone>();
    PlayableGraph graph;
    AnimationClipPlayable playable;
    Vector3 startPosition;
    float traveled;
    Material bodyMaterial, accentMaterial;

    void Awake()
    {
        startPosition = transform.position;
        bodyMaterial = bodyMaterialOverride != null ? bodyMaterialOverride : CreateMaterial(bodyColor);
        accentMaterial = accentMaterialOverride != null ? accentMaterialOverride : CreateMaterial(accentColor);
        BuildSkeleton();
    }

    void OnEnable()
    {
        if (clip == null)
        {
            Debug.LogWarning("BeastRig: Clip に BeastRun.anim を設定してください", this);
            return;
        }
        graph = PlayableGraph.Create("BeastRun");
        graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
        var output = AnimationPlayableOutput.Create(graph, "BeastRun", GetComponent<Animator>());
        playable = AnimationClipPlayable.Create(graph, clip);
        output.SetSourcePlayable(playable);
        graph.Play();
    }

    void OnDisable()
    {
        if (graph.IsValid()) graph.Destroy();
    }

    void Update()
    {
        if (playable.IsValid()) playable.SetSpeed(speed);

        if (approach)
        {
            traveled += BeastRigBones.Stride * BeastRigBones.CyclesPerSecond * speed * Time.deltaTime;
            if (traveled > approachDistance) traveled = 0f;
            transform.position = startPosition + transform.forward * traveled;
        }
    }

    void LateUpdate()
    {
        foreach (var b in bones)
        {
            b.line.SetPosition(0, b.from.position);
            b.line.SetPosition(1, b.to.position);
        }
    }

    void BuildSkeleton()
    {
        var map = new Dictionary<string, Transform>();
        foreach (var path in BeastRigBones.Paths)
        {
            int slash = path.LastIndexOf('/');
            Transform parent = slash < 0 ? transform : map[path.Substring(0, slash)];
            string name = path.Substring(slash + 1);
            Transform t = parent.Find(name);
            if (t == null)
            {
                t = new GameObject(name).transform;
                t.SetParent(parent, false);
            }
            map[path] = t;

            if (parent == transform || name.StartsWith("Eye_")) continue;
            // 爪の先端（*_c と親指の *_b）はアクセント色の細い線
            bool tip = name.EndsWith("_c") || (name.StartsWith("Thumb") && name.EndsWith("_b"));
            bool claw = name.StartsWith("Claw") || name.StartsWith("Thumb");
            float width = tip ? 0.018f : claw ? 0.026f : lineWidth;
            bones.Add(new Bone { from = parent, to = t, line = CreateLine(t, width, tip ? accentMaterial : bodyMaterial) });
        }

        // 頭と光る目
        CreateSphere("HeadMesh", map["Hips/Spine/Chest/Neck/Head"], BeastRigBones.HeadRadius * 2f, bodyMaterial);
        CreateSphere("EyeMesh", map["Hips/Spine/Chest/Neck/Head/Eye_L"], 0.035f, accentMaterial);
        CreateSphere("EyeMesh", map["Hips/Spine/Chest/Neck/Head/Eye_R"], 0.035f, accentMaterial);
    }

    LineRenderer CreateLine(Transform owner, float width, Material mat)
    {
        var go = new GameObject("Line");
        go.transform.SetParent(owner, false);
        var lr = go.AddComponent<LineRenderer>();
        lr.useWorldSpace = true;
        lr.positionCount = 2;
        lr.widthMultiplier = width;
        lr.numCapVertices = 4;
        lr.sharedMaterial = mat;
        lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
        return lr;
    }

    void CreateSphere(string name, Transform parent, float diameter, Material mat)
    {
        if (parent.Find(name) != null) return;
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = name;
        Destroy(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.localScale = Vector3.one * diameter;
        go.GetComponent<Renderer>().sharedMaterial = mat;
    }

    static Material CreateMaterial(Color color)
    {
        // URP / HDRP / ビルトインのどれでも見えるシェーダーを順に探す
        string[] shaders = { "Universal Render Pipeline/Unlit", "HDRP/Unlit", "Unlit/Color", "Sprites/Default" };
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
}
