using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// キャラクターの足音・ジャンプ・着地を鳴らす（FieldSE を使う）。フィナ（やアスカ）に付ける。
/// 足元の地面の種類は、次の順に調べる：
///   1. 地面の GameObject（か親）に付いた FootstepSurface
///   2. Terrain なら、足元でいちばん濃いテレインレイヤーの名前
///   3. コライダーの Physic Material の名前 → マテリアルの名前 → GameObject の名前・タグ
///   を Rules のキーワードと照らし合わせる（大文字・小文字は区別しない）。どれにも当たらなければ Default Surface。
/// 歩いた距離で自動で鳴らす（Auto By Distance）か、アニメーションのイベント（関数名 OnMotionEvent、文字列 "Footstep"）で鳴らす。
/// </summary>
public class FootstepSE : MonoBehaviour
{
    [System.Serializable]
    public class SurfaceRule
    {
        [Tooltip("名前に含まれていたらこの地面にする言葉（例：grass、stone、wood）")]
        public string keyword;
        [Tooltip("Grass / Dirt / Stone / Wood / Water / Mud / Metal")]
        public string surface;
        public SurfaceRule(string k, string s) { keyword = k; surface = s; }
    }

    [Header("地面の種類")]
    [Tooltip("どれにも当てはまらないときの地面")]
    public string defaultSurface = "Dirt";

    public List<SurfaceRule> rules = new List<SurfaceRule>
    {
        new SurfaceRule("grass", "Grass"), new SurfaceRule("草", "Grass"), new SurfaceRule("leaf", "Grass"), new SurfaceRule("forest", "Grass"),
        new SurfaceRule("water", "Water"), new SurfaceRule("水", "Water"), new SurfaceRule("puddle", "Water"),
        new SurfaceRule("mud", "Mud"), new SurfaceRule("swamp", "Mud"), new SurfaceRule("bog", "Mud"), new SurfaceRule("沼", "Mud"), new SurfaceRule("泥", "Mud"),
        new SurfaceRule("wood", "Wood"), new SurfaceRule("plank", "Wood"), new SurfaceRule("bridge", "Wood"), new SurfaceRule("木", "Wood"),
        new SurfaceRule("metal", "Metal"), new SurfaceRule("iron", "Metal"), new SurfaceRule("steel", "Metal"), new SurfaceRule("金属", "Metal"),
        new SurfaceRule("stone", "Stone"), new SurfaceRule("rock", "Stone"), new SurfaceRule("brick", "Stone"), new SurfaceRule("tile", "Stone"),
        new SurfaceRule("cave", "Stone"), new SurfaceRule("marble", "Stone"), new SurfaceRule("石", "Stone"), new SurfaceRule("岩", "Stone"),
        new SurfaceRule("dirt", "Dirt"), new SurfaceRule("soil", "Dirt"), new SurfaceRule("sand", "Dirt"), new SurfaceRule("ground", "Dirt"), new SurfaceRule("土", "Dirt"),
    };

    [Tooltip("足元を調べる線の長さ（m）と、地面として扱うレイヤー")]
    public float rayLength = 1.5f;
    public LayerMask groundMask = ~0;

    [Header("足音")]
    [Tooltip("歩いた距離で自動で鳴らす（オフなら、アニメーションのイベント \"Footstep\" か Step() で鳴らす）")]
    public bool autoByDistance = true;

    [Tooltip("1歩の長さ（m）：歩き・走り")]
    public float walkStride = 0.75f, runStride = 1.15f;

    [Tooltip("この速さ（m/秒）以上で「走り」（フィナは歩き 4.5・走り 9）")]
    public float runSpeed = 6.5f;

    [Tooltip("これより遅いときは足音を鳴らさない（m/秒）")]
    public float minSpeed = 0.4f;

    [Tooltip("足音の音量")]
    [Range(0f, 2f)] public float volume = 1f;

    [Tooltip("キャラクターの位置で鳴らす（オフなら 2D。操作キャラは 2D がおすすめ）")]
    public bool positional = false;

    [Header("ジャンプ・着地")]
    [Tooltip("地面を離れた・降りたのを見て、Jump・Land を自動で鳴らす")]
    public bool autoJumpLand = true;

    [Tooltip("この速さ（m/秒）より速く落ちて着地したら Land_Heavy")]
    public float heavyLandSpeed = 9f;

    [Tooltip("この速さ（m/秒）より速く上へ離れたらジャンプとみなす（段差から落ちただけでは鳴らさない）")]
    public float jumpUpSpeed = 1.5f;

    CharacterController controller;
    Vector3 lastPos;
    float walked, fallSpeed, lastStepTime;
    bool wasGrounded = true;
    string lastSurface;

    /// <summary>直前に調べた足元の地面</summary>
    public string CurrentSurface => lastSurface ?? defaultSurface;

    void Awake()
    {
        controller = GetComponent<CharacterController>();
        lastPos = transform.position;
    }

    void Update()
    {
        float dt = Mathf.Max(Time.deltaTime, 1e-5f);
        Vector3 pos = transform.position;
        Vector3 delta = pos - lastPos;
        lastPos = pos;
        float vy = delta.y / dt;
        float speed = new Vector2(delta.x, delta.z).magnitude / dt;
        bool grounded = IsGrounded();

        if (autoJumpLand)
        {
            if (wasGrounded && !grounded && vy > jumpUpSpeed) PlayJump();
            if (!grounded) fallSpeed = Mathf.Max(fallSpeed, -vy);
            if (!wasGrounded && grounded) { PlayLand(fallSpeed); walked = 0f; }
            if (grounded) fallSpeed = 0f;
        }
        wasGrounded = grounded;

        if (autoByDistance && grounded && speed > minSpeed && speed < 60f)
        {
            walked += speed * dt;
            bool run = speed >= runSpeed;
            if (walked >= (run ? runStride : walkStride))
            {
                walked = 0f;
                Step(run);
            }
        }
    }

    bool IsGrounded()
    {
        if (controller != null) return controller.isGrounded;
        return Physics.Raycast(transform.position + Vector3.up * 0.1f, Vector3.down, 0.25f, groundMask, QueryTriggerInteraction.Ignore);
    }

    // アニメーションの AnimationEvent（関数名 OnMotionEvent、文字列 "Footstep" / "FootstepRun"）から呼べる
    public void OnMotionEvent(string eventName)
    {
        if (eventName == "Footstep" || eventName == "Step") Step(false);
        else if (eventName == "FootstepRun") Step(true);
    }

    /// <summary>足音を1歩鳴らす</summary>
    public void Step(bool run)
    {
        if (Time.time - lastStepTime < 0.08f) return;   // 自動とイベントの二重鳴りを防ぐ
        lastStepTime = Time.time;
        string surface = DetectSurface();
        if (positional) FieldSE.PlayStep(surface, transform.position, run, volume);
        else FieldSE.PlayStep(surface, null, run, volume);
    }

    /// <summary>ジャンプの踏み切り</summary>
    public void PlayJump()
    {
        Play("Jump", 1f);
    }

    /// <summary>着地（fallSpeed：着地したときの落ちる速さ m/秒）</summary>
    public void PlayLand(float landingFallSpeed)
    {
        Play(landingFallSpeed >= heavyLandSpeed ? "Land_Heavy" : "Land", 1f);
        string surface = DetectSurface();
        if (positional) FieldSE.PlayStep(surface, transform.position, false, volume * 0.8f);
        else FieldSE.PlayStep(surface, null, false, volume * 0.8f);
    }

    void Play(string name, float vol)
    {
        if (positional) FieldSE.Play(name, transform.position, vol * volume);
        else FieldSE.Play(name, vol * volume);
    }

    /// <summary>足元の地面の種類を調べる</summary>
    public string DetectSurface()
    {
        lastSurface = defaultSurface;
        if (!Physics.Raycast(transform.position + Vector3.up * 0.5f, Vector3.down, out var hit, rayLength + 0.5f, groundMask, QueryTriggerInteraction.Ignore))
            return lastSurface;

        var marker = hit.collider.GetComponentInParent<FootstepSurface>();
        if (marker != null && !string.IsNullOrEmpty(marker.surface)) return lastSurface = marker.surface;

        if (hit.collider is TerrainCollider)
        {
            var terrain = hit.collider.GetComponent<Terrain>();
            string layer = TerrainLayerAt(terrain, hit.point);
            if (Match(layer, out var s)) return lastSurface = s;
            return lastSurface;
        }

        if (hit.collider.sharedMaterial != null && Match(hit.collider.sharedMaterial.name, out var s1)) return lastSurface = s1;
        var rend = hit.collider.GetComponent<Renderer>();
        if (rend != null && rend.sharedMaterial != null && Match(rend.sharedMaterial.name, out var s2)) return lastSurface = s2;
        if (Match(hit.collider.gameObject.name, out var s3)) return lastSurface = s3;
        if (Match(hit.collider.tag, out var s4)) return lastSurface = s4;
        return lastSurface;
    }

    static string TerrainLayerAt(Terrain terrain, Vector3 world)
    {
        if (terrain == null || terrain.terrainData == null) return null;
        var td = terrain.terrainData;
        if (td.terrainLayers == null || td.terrainLayers.Length == 0) return null;
        Vector3 p = world - terrain.transform.position;
        int x = Mathf.Clamp((int)(p.x / td.size.x * td.alphamapWidth), 0, td.alphamapWidth - 1);
        int z = Mathf.Clamp((int)(p.z / td.size.z * td.alphamapHeight), 0, td.alphamapHeight - 1);
        float[,,] a = td.GetAlphamaps(x, z, 1, 1);
        int best = 0;
        for (int i = 1; i < a.GetLength(2); i++) if (a[0, 0, i] > a[0, 0, best]) best = i;
        var layer = best < td.terrainLayers.Length ? td.terrainLayers[best] : null;
        return layer != null ? layer.name : null;
    }

    bool Match(string text, out string surface)
    {
        surface = null;
        if (string.IsNullOrEmpty(text)) return false;
        string t = text.ToLowerInvariant();
        foreach (var r in rules)
        {
            if (r == null || string.IsNullOrEmpty(r.keyword)) continue;
            if (t.Contains(r.keyword.ToLowerInvariant())) { surface = r.surface; return true; }
        }
        return false;
    }
}
