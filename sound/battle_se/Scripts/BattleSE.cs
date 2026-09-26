using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Audio;

/// <summary>
/// バトルの攻撃 SE を名前で鳴らす。
///   BattleSE.Play("Fina_Hit_A");                        // 2D で鳴らす
///   BattleSE.Play("Enemy_Stomp", transform.position);   // その位置で鳴らす（3D の割合は spatialBlend）
///   var h = BattleSE.PlayLoop("Flamethrower_Loop", transform);  … BattleSE.Stop(h);  // ループ
///   BattleSE.PlayMagic("Shot", "Ice");                  // Magic_Shot_Ice
/// 音は Resources/BattleSE/ から名前で読む（clips に入れた音があればそちらが先）。
/// シーンに置かなくても、最初に鳴らしたときに自動で作られる（置いておけば Inspector で音量などを変えられる）。
/// </summary>
public class BattleSE : MonoBehaviour
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

    [Tooltip("同じ音を続けて鳴らすとき、この秒数以内の2回目は鳴らさない（多段ヒットで音が重なりすぎないように）")]
    public float sameSoundInterval = 0.03f;

    [Tooltip("同じ音を同時に鳴らせる数")]
    public int maxSameSound = 4;

    [Tooltip("出力先の AudioMixer グループ（無ければそのまま）")]
    public AudioMixerGroup output;

    [Tooltip("Resources 以外から使う音（名前が同じなら Resources より先に使う）")]
    public AudioClip[] clips;

    [Tooltip("Resources の中の置き場所")]
    public string resourcesFolder = "BattleSE";

    static BattleSE instance;
    readonly Dictionary<string, AudioClip> cache = new Dictionary<string, AudioClip>();
    readonly Dictionary<string, float> lastPlayed = new Dictionary<string, float>();
    readonly List<AudioSource> pool = new List<AudioSource>();
    readonly Dictionary<AudioSource, Transform> follows = new Dictionary<AudioSource, Transform>();

    public static BattleSE Instance
    {
        get
        {
            if (instance == null)
            {
                instance = FindObjectOfType<BattleSE>();
                if (instance == null) instance = new GameObject("BattleSE").AddComponent<BattleSE>();
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

    /// <summary>魔法の音（kind は "Shot" か "Impact"、element は "Fire" など）</summary>
    public static AudioSource PlayMagic(string kind, string element, Vector3? position = null)
    {
        string name = $"Magic_{kind}_{element}";
        return position.HasValue ? Play(name, position.Value) : Play(name);
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
            Debug.LogWarning($"BattleSE: 音「{name}」が見つかりません（Resources/{resourcesFolder}/ か clips に入れてください）", this);
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
