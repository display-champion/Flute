// このファイルは motion/bee_sting/tools/export_unity.mjs が自動生成します。手で編集しないでください。
// BeeSting.anim のカーブはこの階層（Animator を付けた GameObject からの相対パス）に対応します。
using UnityEngine;

public static class BeeRigBones
{
    public enum Vis { None, Sphere, Line, Wing }

    public struct Bone
    {
        public string path;
        public Vector3 restPosition;     // 初期姿勢（クリップで動かない値はこのまま使われる）
        public Quaternion restRotation;
        public Vis vis;
        public float size;               // Sphere: 半径 / Line: 太さ / Wing: 長さ
        public float size2;              // Wing: 幅
        public float offset;             // Sphere: 骨方向(+Y)へのずらし
        public int color;                // 0 黒, 1 黄, 2 琥珀, 3 アクセント, 4 羽

        public Bone(string path, Vector3 restPosition, Quaternion restRotation, Vis vis, float size, float size2, float offset, int color)
        {
            this.path = path; this.restPosition = restPosition; this.restRotation = restRotation;
            this.vis = vis; this.size = size; this.size2 = size2; this.offset = offset; this.color = color;
        }
    }

    public const float CycleSeconds = 3f;
    public const float HitTime = 1.98f;   // 針が最も突き出る時刻（秒）

    // 親が先に来る順
    public static readonly Bone[] Bones =
    {
        new Bone("Body", new Vector3(0f, 1.35f, 0f), new Quaternion(-0.0831637f, 0.02127867f, -0.08722776f, 0.9924829f), Vis.Sphere, 0.13f, 0f, 0f, 2),
        new Bone("Body/Head", new Vector3(0f, 0.02f, 0.21f), new Quaternion(0f, 0f, 0f, 1f), Vis.Sphere, 0.095f, 0f, 0f, 0),
        new Bone("Body/Head/Eye_L", new Vector3(-0.065f, 0.02f, 0.05f), new Quaternion(0f, 0f, 0f, 1f), Vis.Sphere, 0.035f, 0f, 0f, 3),
        new Bone("Body/Head/Antenna_L_a", new Vector3(-0.035f, 0.06f, 0.06f), new Quaternion(0.08213124f, 0.6489259f, 0.2808829f, 0.7023208f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Head/Antenna_L_a/Antenna_L_b", new Vector3(0f, 0.1041864f, 0f), new Quaternion(-0.04823213f, -0.09773204f, 0.2740892f, 0.9555089f), Vis.Line, 0.012f, 0f, 0f, 0),
        new Bone("Body/Head/Antenna_L_a/Antenna_L_b/Antenna_L_c", new Vector3(0f, 0.1566922f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.01f, 0f, 0f, 0),
        new Bone("Body/Head/Eye_R", new Vector3(0.065f, 0.02f, 0.05f), new Quaternion(0f, 0f, 0f, 1f), Vis.Sphere, 0.035f, 0f, 0f, 3),
        new Bone("Body/Head/Antenna_R_a", new Vector3(0.035f, 0.06f, 0.06f), new Quaternion(0.1743093f, 0.7055899f, 0.0462909f, 0.6852855f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Head/Antenna_R_a/Antenna_R_b", new Vector3(0f, 0.1643504f, 0f), new Quaternion(0.09931912f, 0.181519f, 0.5707672f, 0.794614f), Vis.Line, 0.012f, 0f, 0f, 0),
        new Bone("Body/Head/Antenna_R_a/Antenna_R_b/Antenna_R_c", new Vector3(0f, 0.143225f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.01f, 0f, 0f, 0),
        new Bone("Body/Abdomen_1", new Vector3(0f, -0.02f, -0.12f), new Quaternion(0.5804288f, -0.4038594f, 0.5804288f, -0.4038594f), Vis.Sphere, 0.08f, 0f, 0.05f, 0),
        new Bone("Body/Abdomen_1/Abdomen_2", new Vector3(0f, 0.1f, 0f), new Quaternion(0f, 0f, -0.05497228f, 0.9984879f), Vis.Sphere, 0.14f, 0f, 0.055f, 1),
        new Bone("Body/Abdomen_1/Abdomen_2/Abdomen_3", new Vector3(0f, 0.11f, 0f), new Quaternion(0f, 0f, -0.05497228f, 0.9984879f), Vis.Sphere, 0.15f, 0f, 0.055f, 0),
        new Bone("Body/Abdomen_1/Abdomen_2/Abdomen_3/Abdomen_4", new Vector3(0f, 0.11f, 0f), new Quaternion(0f, 0f, -0.05497228f, 0.9984879f), Vis.Sphere, 0.13f, 0f, 0.05f, 1),
        new Bone("Body/Abdomen_1/Abdomen_2/Abdomen_3/Abdomen_4/Abdomen_5", new Vector3(0f, 0.1f, 0f), new Quaternion(0f, 0f, -0.05497228f, 0.9984879f), Vis.Sphere, 0.085f, 0f, 0.04f, 0),
        new Bone("Body/Abdomen_1/Abdomen_2/Abdomen_3/Abdomen_4/Abdomen_5/Stinger", new Vector3(0f, 0.08f, 0f), new Quaternion(0f, 0f, -0.0412383f, 0.9991493f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Abdomen_1/Abdomen_2/Abdomen_3/Abdomen_4/Abdomen_5/Stinger/StingerTip", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.03f, 0f, 0f, 3),
        new Bone("Body/Wing_FL", new Vector3(-0.05f, 0.11f, 0.03f), new Quaternion(-0.6190376f, 0.7360297f, 0.005943897f, 0.2738931f), Vis.Wing, 0.42f, 0.15f, 0f, 4),
        new Bone("Body/Wing_FR", new Vector3(0.05f, 0.11f, 0.03f), new Quaternion(0.6190376f, 0.7360297f, 0.005943897f, -0.2738931f), Vis.Wing, 0.42f, 0.15f, 0f, 4),
        new Bone("Body/Wing_HL", new Vector3(-0.05f, 0.1f, -0.04f), new Quaternion(0.7152759f, -0.5942823f, 0.07043394f, -0.360899f), Vis.Wing, 0.28f, 0.1f, 0f, 4),
        new Bone("Body/Wing_HR", new Vector3(0.05f, 0.1f, -0.04f), new Quaternion(0.7152759f, 0.5942823f, -0.07043394f, -0.360899f), Vis.Wing, 0.28f, 0.1f, 0f, 4),
        new Bone("Body/Leg_L1_a", new Vector3(-0.06f, -0.09f, 0.07f), new Quaternion(-0.5210184f, 0.342851f, 0.743858f, 0.2401422f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Leg_L1_a/Leg_L1_b", new Vector3(0f, 0.13f, 0f), new Quaternion(-0.241664f, -0.8965323f, 0.3663002f, 0.06043649f), Vis.Line, 0.018f, 0f, 0f, 0),
        new Bone("Body/Leg_L1_a/Leg_L1_b/Leg_L1_c", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.014f, 0f, 0f, 0),
        new Bone("Body/Leg_L2_a", new Vector3(-0.06f, -0.09f, 0f), new Quaternion(-0.02703064f, -0.06110417f, 0.9124706f, 0.4036495f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Leg_L2_a/Leg_L2_b", new Vector3(0f, 0.13f, 0f), new Quaternion(0.1837776f, -0.7281217f, 0.2719292f, 0.6017633f), Vis.Line, 0.018f, 0f, 0f, 0),
        new Bone("Body/Leg_L2_a/Leg_L2_b/Leg_L2_c", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.014f, 0f, 0f, 0),
        new Bone("Body/Leg_L3_a", new Vector3(-0.06f, -0.09f, -0.07f), new Quaternion(-0.09885111f, -0.2234581f, 0.8867936f, 0.3922908f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Leg_L3_a/Leg_L3_b", new Vector3(0f, 0.13f, 0f), new Quaternion(0.3008994f, -0.7584885f, 0.1277428f, 0.5637699f), Vis.Line, 0.018f, 0f, 0f, 0),
        new Bone("Body/Leg_L3_a/Leg_L3_b/Leg_L3_c", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.014f, 0f, 0f, 0),
        new Bone("Body/Leg_R1_a", new Vector3(0.06f, -0.09f, 0.07f), new Quaternion(0.5210184f, 0.342851f, 0.743858f, -0.2401422f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Leg_R1_a/Leg_R1_b", new Vector3(0f, 0.13f, 0f), new Quaternion(-0.3663002f, -0.06043649f, 0.241664f, 0.8965323f), Vis.Line, 0.018f, 0f, 0f, 0),
        new Bone("Body/Leg_R1_a/Leg_R1_b/Leg_R1_c", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.014f, 0f, 0f, 0),
        new Bone("Body/Leg_R2_a", new Vector3(0.06f, -0.09f, 0f), new Quaternion(0.02703064f, -0.06110417f, 0.9124706f, -0.4036495f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Leg_R2_a/Leg_R2_b", new Vector3(0f, 0.13f, 0f), new Quaternion(-0.2719292f, -0.6017633f, -0.1837776f, 0.7281217f), Vis.Line, 0.018f, 0f, 0f, 0),
        new Bone("Body/Leg_R2_a/Leg_R2_b/Leg_R2_c", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.014f, 0f, 0f, 0),
        new Bone("Body/Leg_R3_a", new Vector3(0.06f, -0.09f, -0.07f), new Quaternion(0.09885111f, -0.2234581f, 0.8867936f, -0.3922908f), Vis.None, 0f, 0f, 0f, 0),
        new Bone("Body/Leg_R3_a/Leg_R3_b", new Vector3(0f, 0.13f, 0f), new Quaternion(-0.1277428f, -0.5637699f, -0.3008994f, 0.7584885f), Vis.Line, 0.018f, 0f, 0f, 0),
        new Bone("Body/Leg_R3_a/Leg_R3_b/Leg_R3_c", new Vector3(0f, 0.15f, 0f), new Quaternion(0f, 0f, 0f, 1f), Vis.Line, 0.014f, 0f, 0f, 0),
    };
}
