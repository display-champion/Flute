using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Events;
using UnityEngine.Playables;

/// <summary>
/// ダンジョン雑魚の「体全体を動かす」モーションを再生する。
/// 構成：この GameObject（Animator ＋ EnemyMotion）→ 子「Motion」（クリップが動かす）→ モデル
/// 子「Motion」が無ければ自動で作り、今ある子を全部その下へ移す。
/// AnimatorController は不要（Playables API で直接再生する）。
/// </summary>
[RequireComponent(typeof(Animator))]
public class EnemyMotion : MonoBehaviour
{
    [System.Serializable]
    public class MotionEvent : UnityEvent<string> { }

    [Tooltip("この敵で使うクリップ（例：Mushroom_Idle, Mushroom_Move, Mushroom_Attack_Lunge ...）")]
    public AnimationClip[] clips;

    [Tooltip("待機クリップの名前（クリップ名の末尾が一致すればよい）")]
    public string idleClip = "Idle";

    [Tooltip("クリップを切り替えるときのフェード時間（秒）")]
    public float fadeTime = 0.12f;

    [Tooltip("再生速度（1 = 元の速さ）")]
    public float speed = 1f;

    [Tooltip("クリップ内のイベント（Hit / Stomp / SporeBurst / ChargeStart など）を受け取る")]
    public MotionEvent onMotionEvent;

    [Tooltip("1回きりのクリップが終わったときに、そのクリップ名で呼ばれる")]
    public MotionEvent onMotionFinished;

    PlayableGraph graph;
    AnimationMixerPlayable mixer;
    AnimationClipPlayable[] playables;
    int current = -1, previous = -1;
    float fadeElapsed;
    bool finishedSent;

    /// <summary>今再生しているクリップ名（無ければ空）</summary>
    public string CurrentClip => current >= 0 ? clips[current].name : "";

    void Awake()
    {
        EnsureMotionRoot();
    }

    void EnsureMotionRoot()
    {
        if (transform.Find("Motion") != null) return;
        var motion = new GameObject("Motion").transform;
        var children = new Transform[transform.childCount];
        for (int i = 0; i < children.Length; i++) children[i] = transform.GetChild(i);
        motion.SetParent(transform, false);
        foreach (var c in children) c.SetParent(motion, true);
        GetComponent<Animator>().Rebind();   // 新しくできた Motion をアニメーションの対象として認識させる
    }

    void OnEnable()
    {
        if (clips == null || clips.Length == 0)
        {
            Debug.LogWarning("EnemyMotion: Clips にクリップを設定してください", this);
            return;
        }
        graph = PlayableGraph.Create($"EnemyMotion_{name}");
        graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
        var output = AnimationPlayableOutput.Create(graph, "EnemyMotion", GetComponent<Animator>());
        mixer = AnimationMixerPlayable.Create(graph, clips.Length);
        playables = new AnimationClipPlayable[clips.Length];
        for (int i = 0; i < clips.Length; i++)
        {
            if (clips[i] == null) continue;   // 空の枠は飛ばす
            playables[i] = AnimationClipPlayable.Create(graph, clips[i]);
            graph.Connect(playables[i], 0, mixer, i);
            mixer.SetInputWeight(i, 0f);
        }
        output.SetSourcePlayable(mixer);
        graph.Play();
        current = previous = -1;
        Play(idleClip, 0f);
    }

    void OnDisable()
    {
        if (graph.IsValid()) graph.Destroy();
    }

    /// <summary>
    /// クリップを最初から再生する。name はクリップ名、または末尾（"Attack_Lunge" など）。
    /// 末尾が一致するクリップが無ければ "_name_" を含むクリップを使う（"Death" で Death_SporeBurst、"Move" で Move_Flee）
    /// </summary>
    public bool Play(string clipName) => Play(clipName, fadeTime);

    public bool Play(string clipName, float fade)
    {
        int index = Find(clipName);
        if (index < 0 || !graph.IsValid())
        {
            if (index < 0) Debug.LogWarning($"EnemyMotion: クリップ「{clipName}」が見つかりません", this);
            return false;
        }
        previous = index == current ? -1 : current;
        current = index;
        // 使っていないクリップは止めておく（時間が進んでイベントが出ないように）
        for (int i = 0; i < playables.Length; i++)
            if (i != current && i != previous && playables[i].IsValid()) playables[i].SetSpeed(0);
        playables[index].SetTime(0);
        playables[index].SetTime(0);   // 2回呼ぶと前回との差分がリセットされ、途中のイベントが飛ばない
        playables[index].SetSpeed(1);
        fadeElapsed = fade <= 0f ? float.MaxValue : 0f;
        finishedSent = false;
        return true;
    }

    /// <summary>指定したクリップを再生中か（名前の末尾一致）</summary>
    public bool IsPlaying(string clipName) => current >= 0 && current == Find(clipName);

    int Find(string clipName)
    {
        if (clips == null) return -1;
        for (int i = 0; i < clips.Length; i++)
        {
            if (clips[i] == null) continue;
            string n = clips[i].name;
            if (n == clipName || n.EndsWith("_" + clipName)) return i;
        }
        for (int i = 0; i < clips.Length; i++)
        {
            if (clips[i] != null && clips[i].name.Contains("_" + clipName + "_")) return i;
        }
        return -1;
    }

    void Update()
    {
        if (!graph.IsValid() || current < 0) return;
        mixer.SetSpeed(speed);

        // フェード：前のクリップから今のクリップへ重みを移す
        fadeElapsed += Time.deltaTime * speed;
        float w = fadeTime <= 0f ? 1f : Mathf.Clamp01(fadeElapsed / fadeTime);
        for (int i = 0; i < clips.Length; i++)
        {
            float weight = i == current ? w : i == previous ? 1f - w : 0f;
            mixer.SetInputWeight(i, weight);
        }
        if (w >= 1f) previous = -1;

        // 1回きりのクリップが終わったら待機へ戻る（Death を含む名前は最後の姿勢で止める）
        var clip = clips[current];
        if (!clip.isLooping && playables[current].GetTime() >= clip.length)
        {
            if (!finishedSent)
            {
                finishedSent = true;
                onMotionFinished?.Invoke(clip.name);
            }
            int idle = Find(idleClip);
            if (clip.name.Contains("Death")) playables[current].SetSpeed(0);
            else if (idle >= 0 && idle != current) Play(idleClip);
        }
    }

    // クリップの AnimationEvent（関数名 OnMotionEvent）から呼ばれる
    void OnMotionEvent(string eventName)
    {
        onMotionEvent?.Invoke(eventName);
    }
}
