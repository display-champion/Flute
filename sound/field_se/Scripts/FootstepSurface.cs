using UnityEngine;

/// <summary>
/// 地面（や床・橋）に付けて、足音の種類を直接決める。FootstepSE は名前から推測するより先にこれを見る。
/// 子のコライダーにも効く（親に付ければよい）。
/// </summary>
public class FootstepSurface : MonoBehaviour
{
    [Tooltip("Grass / Dirt / Stone / Wood / Water / Mud / Metal")]
    public string surface = "Stone";
}
