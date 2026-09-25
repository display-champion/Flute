// このファイルは motion/mage_cast/tools/export_unity.mjs が自動生成します。手で編集しないでください。
// MageCast.anim のカーブはこの階層（Animator を付けた GameObject からの相対パス）に対応します。
using UnityEngine;

public static class MageRigBones
{
    public enum Vis { None, Sphere, Line, Hat }

    public struct Bone
    {
        public string path;
        public Vector3 restPosition;     // 初期姿勢（クリップで動かない値はこのまま使われる）
        public Quaternion restRotation;
        public Vector3 restScale;
        public Vis vis;
        public float size;               // Sphere: 半径 / Line: 太さ / Hat: 頭の半径
        public int color;                // 0 体, 1 帽子, 2 アクセント, 3 魔力

        public Bone(string path, Vector3 restPosition, Quaternion restRotation, Vector3 restScale, Vis vis, float size, int color)
        {
            this.path = path; this.restPosition = restPosition; this.restRotation = restRotation; this.restScale = restScale;
            this.vis = vis; this.size = size; this.color = color;
        }
    }

    public const float CycleSeconds = 5f;
    public const float GatherStartTime = 1.2f;   // ゆらゆら（魔力を溜める）開始
    public const float GatherEndTime = 3.2f;
    public const float CastTime = 3.8f;           // 胸の前へ振り下ろして術が発動する時刻
    public const float HatRadius = 0.15f;
    public const float HatHeight = 0.34f;

    // 親が先に来る順
    public static readonly Bone[] Bones =
    {
        new Bone("Hips", new Vector3(0f, 0.93f, 0f), new Quaternion(0.005303251f, 0.7070869f, 0.005303251f, 0.7070869f), new Vector3(1f, 1f, 1f), Vis.None, 0f, 0),
        new Bone("Hips/Spine", new Vector3(0f, 0.26f, 0f), new Quaternion(0f, 0f, 0.00749993f, 0.9999719f), new Vector3(1f, 1f, 1f), Vis.Line, 0.055f, 0),
        new Bone("Hips/Spine/Chest", new Vector3(0f, 0.26f, 0f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.055f, 0),
        new Bone("Hips/Spine/Chest/Neck", new Vector3(0f, 0.08f, 0f), new Quaternion(0f, 0f, 0.04964365f, 0.998767f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/Spine/Chest/Neck/Head", new Vector3(0f, 0.13f, 0f), new Quaternion(0f, -0.7071068f, 0f, 0.7071068f), new Vector3(1f, 1f, 1f), Vis.Hat, 0.11f, 0),
        new Bone("Hips/Spine/Chest/Neck/Head/LeftEye", new Vector3(-0.04f, 0.02f, 0.099f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Sphere, 0.018f, 3),
        new Bone("Hips/Spine/Chest/Neck/Head/RightEye", new Vector3(0.04f, 0.02f, 0.099f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Sphere, 0.018f, 3),
        new Bone("Hips/Spine/Chest/LeftUpperArm", new Vector3(0f, -0.03f, -0.19f), new Quaternion(0.0009571336f, -0.1726701f, 0.9849641f, -0.005459789f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/Spine/Chest/LeftUpperArm/LeftLowerArm", new Vector3(0f, 0.3f, 0f), new Quaternion(0.2059366f, 0.02249439f, -0.1634806f, 0.9645508f), new Vector3(1f, 1f, 1f), Vis.Line, 0.048f, 0),
        new Bone("Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand", new Vector3(0f, 0.27f, 0f), new Quaternion(0.0117378f, -0.004157048f, -0.04858129f, 0.9987416f), new Vector3(1f, 1f, 1f), Vis.Line, 0.044f, 0),
        new Bone("Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand/LeftHandTip", new Vector3(0f, 0.08f, 0f), new Quaternion(-0.01405491f, 0.004827088f, 0.05800035f, 0.9982059f), new Vector3(1f, 1f, 1f), Vis.Line, 0.04f, 0),
        new Bone("Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand/LeftHandTip/LeftFinger1", new Vector3(-0.00593554f, 0.06549353f, 0.0239868f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.018f, 0),
        new Bone("Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand/LeftHandTip/LeftFinger2", new Vector3(0f, 0.07f, 0f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.018f, 0),
        new Bone("Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand/LeftHandTip/LeftFinger3", new Vector3(0.00593554f, 0.06549353f, -0.0239868f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.018f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm", new Vector3(0f, -0.03f, 0.19f), new Quaternion(-0.0009571336f, 0.1726701f, 0.9849641f, -0.005459789f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm/RightLowerArm", new Vector3(0f, 0.3f, 0f), new Quaternion(-0.2059366f, -0.02249439f, -0.1634806f, 0.9645508f), new Vector3(1f, 1f, 1f), Vis.Line, 0.048f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand", new Vector3(0f, 0.27f, 0f), new Quaternion(-0.0117378f, 0.004157048f, -0.04858129f, 0.9987416f), new Vector3(1f, 1f, 1f), Vis.Line, 0.044f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand/RightHandTip", new Vector3(0f, 0.08f, 0f), new Quaternion(0.01405491f, -0.004827088f, 0.05800035f, 0.9982059f), new Vector3(1f, 1f, 1f), Vis.Line, 0.04f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand/RightHandTip/RightFinger1", new Vector3(0.00593554f, 0.06549353f, 0.0239868f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.018f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand/RightHandTip/RightFinger2", new Vector3(0f, 0.07f, 0f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.018f, 0),
        new Bone("Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand/RightHandTip/RightFinger3", new Vector3(-0.00593554f, 0.06549353f, -0.0239868f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.018f, 0),
        new Bone("Hips/LeftUpperLeg", new Vector3(0f, 0f, -0.1f), new Quaternion(-0.006091947f, -0.03927881f, 0.9874045f, 0.1531415f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/LeftUpperLeg/LeftLowerLeg", new Vector3(0f, 0.45f, 0f), new Quaternion(0.03340153f, -0.01299017f, 0.2911064f, 0.9560192f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/LeftUpperLeg/LeftLowerLeg/LeftFoot", new Vector3(0f, 0.44f, 0f), new Quaternion(-0.07015533f, 0.07420728f, -0.6895486f, 0.7170036f), new Vector3(1f, 1f, 1f), Vis.Line, 0.045f, 0),
        new Bone("Hips/LeftUpperLeg/LeftLowerLeg/LeftFoot/LeftToes", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.04f, 0),
        new Bone("Hips/RightUpperLeg", new Vector3(0f, 0f, 0.1f), new Quaternion(0.005786042f, 0.04507827f, 0.990838f, 0.1271795f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/RightUpperLeg/RightLowerLeg", new Vector3(0f, 0.45f, 0f), new Quaternion(-0.03360511f, 0.01596781f, 0.2856094f, 0.9576236f), new Vector3(1f, 1f, 1f), Vis.Line, 0.05f, 0),
        new Bone("Hips/RightUpperLeg/RightLowerLeg/RightFoot", new Vector3(0f, 0.44f, 0f), new Quaternion(0.06484577f, -0.07968962f, -0.7037488f, 0.702981f), new Vector3(1f, 1f, 1f), Vis.Line, 0.045f, 0),
        new Bone("Hips/RightUpperLeg/RightLowerLeg/RightFoot/RightToes", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(1f, 1f, 1f), Vis.Line, 0.04f, 0),
        new Bone("Orb", new Vector3(0f, 0.9463024f, 0.1064577f), new Quaternion(0f, 0f, 0f, 1f), new Vector3(0f, 0f, 0f), Vis.Sphere, 0.5f, 3),
    };
}
