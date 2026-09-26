using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Audio;

/// <summary>
/// 操作系・マップ系の SE を名前で鳴らす（BattleSE と同じ使い方。BattleSE が無くても動く）。
///   FieldSE.Play("Switch_On");                         // 2D で鳴らす
///   FieldSE.Play("Wall_Lower", wall.position);          // その位置で鳴らす（3D の割合は spatialBlend）
///   var h = FieldSE.PlayLoop("Water_Stream_Loop", transform);  … FieldSE.Stop(h);  // ループ
///   FieldSE.PlayStep("Stone");                         // Step_Stone_01〜04 から前回と違うものを選ぶ
/// 音は Resources/FieldSE/ から名前で読む（clips に入れた音があればそちらが先）。
/// シーンに置かなくても、最初に鳴らしたときに自動で作られる（置いておけば Inspector で音量などを変えられる）。
/// </summary>
public class FieldSE : MonoBehaviour
{
    [Tooltip("全体の音量")]
    [Range(0f, 1f)] public float volume = 1f;

    [Tooltip("鳴らすたびに高さを少し揺らす幅（0.04 = ±4%）。同じ音の連打が機械的に聞こえないように")]
    [Range(0f, 0.2f)] public float pitchJitter = 0.04f;

    [Tooltip("鳴らすたびに音量を少し下げる幅（0.1 = 最大 -10%）")]
    [Range(0f, 0.5f)] public float volumeJitter = 0.1f;

    [Tooltip("位置を指定して鳴らしたときの 3D の割合（0 = 2D、1 = 完全に 3D）")]
    [Range(0f, 1f)] public float spatialBlend = 0.6f;

    [Tooltip("3D で音が小さくなり始める距離・聞こえなくなる距離（m）")]
    public float minDistance = 4f, maxDistance = 40f;

    [Tooltip("同時に鳴らせる数（超えたら一番古い音を止める。ループは止めない）")]
    public int voices = 24;

    [Tooltip("同じ音を続けて鳴らすとき、この秒数以内の2回目は鳴らさない（音が重なりすぎないように）")]
    public float sameSoundInterval = 0.03f;

    [Tooltip("同じ音を同時に鳴らせる数")]
    public int maxSameSound = 4;

    [Tooltip("出力先の AudioMixer グループ（無ければそのまま）")]
    public AudioMixerGroup output;

    [Tooltip("Resources 以外から使う音（名前が同じなら Resources より先に使う）")]
    public AudioClip[] clips;

    [Tooltip("Resources の中の置き場所")]
    public string resourcesFolder = "FieldSE";

    static FieldSE instance;
    readonly Dictionary<string, AudioClip> cache = new Dictionary<string, AudioClip>();
    readonly Dictionary<string, float> lastPlayed = new Dictionary<string, float>();
    readonly List<AudioSource> pool = new List<AudioSource>();
    readonly Dictionary<AudioSource, Transform> follows = new Dictionary<AudioSource, Transform>();

    public static FieldSE Instance
    {
        get
        {
            if (instance == null)
            {
                instance = FindObjectOfType<FieldSE>();
                if (instance == null) instance = new GameObject("FieldSE").AddComponent<FieldSE>();
            }
            return instance;
        }
    }

    void Awake()
    {
        if (instance != null && instance != this) { Destroy(gameObject); return; }
        instance = this;
        if (transform.parent == null) DontDestroyOnLoad(gameObject);
    }

    // ---------------- 鳴らす ----------------

    /// <summary>2D で鳴らす。volumeScale・pitch は 1 が元のまま</summary>
    public static AudioSource Play(string name, float volumeScale = 1f, float pitch = 1f) => Instance.PlayInternal(name, null, null, volumeScale, pitch, false);

    /// <summary>その位置で鳴らす</summary>
    public static AudioSource Play(string name, Vector3 position, float volumeScale = 1f, float pitch = 1f) => Instance.PlayInternal(name, position, null, volumeScale, pitch, false);

    /// <summary>ループで鳴らす（follow を渡すとその位置についていく）。止めるときは Stop に戻り値を渡す</summary>
    public static AudioSource PlayLoop(string name, Transform follow = null, float volumeScale = 1f) => Instance.PlayInternal(name, follow != null ? follow.position : (Vector3?)null, follow, volumeScale, 1f, true);

    readonly Dictionary<string, int> lastVariation = new Dictionary<string, int>();

    /// <summary>
    /// 足音（surface は "Grass" "Dirt" "Stone" "Wood" "Water" "Mud" "Metal"）。4 通りから前回と違うものを選ぶ。
    /// run = true で少し大きく・高めに鳴らす（走り）
    /// </summary>
    public static AudioSource PlayStep(string surface, Vector3? position = null, bool run = false, float volumeScale = 1f)
    {
        var self = Instance;
        self.lastVariation.TryGetValue(surface, out int last);
        int v;
        if (last == 0) v = Random.Range(1, 5);   // 初めては 1〜4 のどれか
        else { v = Random.Range(1, 4); if (v >= last) v++; }   // 2回目からは前回以外
        self.lastVariation[surface] = v;
        string name = $"Step_{surface}_{v:00}";
        float vol = volumeScale * (run ? 1.3f : 1f);
        float pitch = run ? 1.06f : 1f;
        return position.HasValue ? Play(name, position.Value, vol, pitch) : Play(name, vol, pitch);
    }

    /// <summary>鳴っている音を止める（fade 秒かけて小さくする）</summary>
    public static void Stop(AudioSource source, float fade = 0.1f)
    {
        if (source == null || instance == null) return;
        instance.StartCoroutine(instance.FadeOut(source, fade));
    }

    /// <summary>その名前の音をすべて止める</summary>
    public static void StopAll(string name = null, float fade = 0.05f)
    {
        if (instance == null) return;
        foreach (var s in instance.pool)
            if (s.isPlaying && (name == null || (s.clip != null && s.clip.name == name))) Stop(s, fade);
    }

    /// <summary>名前から AudioClip を取る（無ければ null）</summary>
    public static AudioClip GetClip(string name) => Instance.Find(name);

    AudioSource PlayInternal(string name, Vector3? position, Transform follow, float volumeScale, float pitch, bool loop)
    {
        var clip = Find(name);
        if (clip == null)
        {
            Debug.LogWarning($"FieldSE: 音「{name}」が見つかりません（Resources/{resourcesFolder}/ か clips に入れてください）", this);
            return null;
        }
        if (!loop)
        {
            if (lastPlayed.TryGetValue(name, out float t) && Time.unscaledTime - t < sameSoundInterval) return null;
            int same = 0;
            foreach (var s in pool) if (s.isPlaying && s.clip == clip) same++;
            if (same >= maxSameSound) return null;
        }
        lastPlayed[name] = Time.unscaledTime;

        var src = GetFreeSource();
        src.clip = clip;
        src.loop = loop;
        src.outputAudioMixerGroup = output;
        src.pitch = pitch * (loop ? 1f : 1f + Random.Range(-pitchJitter, pitchJitter));
        src.volume = volume * volumeScale * (loop ? 1f : 1f - Random.Range(0f, volumeJitter));
        src.spatialBlend = position.HasValue ? spatialBlend : 0f;
        src.minDistance = minDistance;
        src.maxDistance = maxDistance;
        src.rolloffMode = AudioRolloffMode.Linear;
        src.transform.position = position ?? transform.position;
        if (follow != null) follows[src] = follow; else follows.Remove(src);
        src.Play();
        return src;
    }

    AudioClip Find(string name)
    {
        if (string.IsNullOrEmpty(name)) return null;
        if (cache.TryGetValue(name, out var c) && c != null) return c;
        if (clips != null)
            foreach (var clip in clips)
                if (clip != null && clip.name == name) { cache[name] = clip; return clip; }
        c = Resources.Load<AudioClip>($"{resourcesFolder}/{name}");
        if (c != null) cache[name] = c;
        return c;
    }

    AudioSource GetFreeSource()
    {
        foreach (var s in pool) if (!s.isPlaying) return s;
        if (pool.Count < voices)
        {
            var go = new GameObject($"Voice{pool.Count}");
            go.transform.SetParent(transform, false);
            var s = go.AddComponent<AudioSource>();
            s.playOnAwake = false;
            s.dopplerLevel = 0f;
            pool.Add(s);
            return s;
        }
        // いっぱいなら、ループ以外で一番長く鳴っているものを使い回す
        AudioSource oldest = null;
        foreach (var s in pool)
            if (!s.loop && (oldest == null || s.time > oldest.time)) oldest = s;
        oldest = oldest ?? pool[0];
        oldest.Stop();
        return oldest;
    }

    void LateUpdate()
    {
        if (follows.Count == 0) return;
        var ended = new List<AudioSource>();
        foreach (var kv in follows)
        {
            if (kv.Key == null || !kv.Key.isPlaying || kv.Value == null) { ended.Add(kv.Key); continue; }
            kv.Key.transform.position = kv.Value.position;
        }
        foreach (var s in ended) follows.Remove(s);
    }

    System.Collections.IEnumerator FadeOut(AudioSource s, float fade)
    {
        float v0 = s.volume;
        for (float t = 0; t < fade && s != null && s.isPlaying; t += Time.unscaledDeltaTime)
        {
            s.volume = v0 * (1f - t / fade);
            yield return null;
        }
        if (s != null) { s.Stop(); s.loop = false; s.volume = v0; follows.Remove(s); }
    }
}
