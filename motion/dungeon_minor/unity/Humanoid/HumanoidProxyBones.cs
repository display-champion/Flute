// このファイルは tools/export_humanoid.mjs が自動生成します。手で編集しないでください。
// 代理の骨組み（Proxy）の階層と、立ち姿での各関節の位置（親からのずれ、m）。回転は使いません。
using UnityEngine;

public static class HumanoidProxyBones
{
    public static readonly string[] Paths =
    {
        "Proxy/Hips",
        "Proxy/Hips/Spine",
        "Proxy/Hips/Spine/Chest",
        "Proxy/Hips/Spine/Chest/Neck",
        "Proxy/Hips/Spine/Chest/Neck/Head",
        "Proxy/Hips/Spine/Chest/Neck/Head/HeadForward",
        "Proxy/Hips/Spine/Chest/LeftUpperArm",
        "Proxy/Hips/Spine/Chest/LeftUpperArm/LeftLowerArm",
        "Proxy/Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand",
        "Proxy/Hips/Spine/Chest/LeftUpperArm/LeftLowerArm/LeftHand/LeftHandTip",
        "Proxy/Hips/Spine/Chest/RightUpperArm",
        "Proxy/Hips/Spine/Chest/RightUpperArm/RightLowerArm",
        "Proxy/Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand",
        "Proxy/Hips/Spine/Chest/RightUpperArm/RightLowerArm/RightHand/RightHandTip",
        "Proxy/Hips/LeftUpperLeg",
        "Proxy/Hips/LeftUpperLeg/LeftLowerLeg",
        "Proxy/Hips/LeftUpperLeg/LeftLowerLeg/LeftFoot",
        "Proxy/Hips/LeftUpperLeg/LeftLowerLeg/LeftFoot/LeftToes",
        "Proxy/Hips/RightUpperLeg",
        "Proxy/Hips/RightUpperLeg/RightLowerLeg",
        "Proxy/Hips/RightUpperLeg/RightLowerLeg/RightFoot",
        "Proxy/Hips/RightUpperLeg/RightLowerLeg/RightFoot/RightToes",
    };

    public static readonly Vector3[] RestLocalPositions =
    {
        new Vector3(0f, 0.95f, 0f),
        new Vector3(0f, 0.119959f, 0.00314123f),
        new Vector3(0f, 0.219807f, 0.00921264f),
        new Vector3(0f, 0.199726f, 0.0104672f),
        new Vector3(0f, 0.099863f, 0.0052336f),
        new Vector3(0f, -0.00628031f, 0.119836f),
        new Vector3(-0.18f, 0.139808f, 0.00732703f),
        new Vector3(-0.0865568f, -0.260925f, -0.0531584f),
        new Vector3(0.028133f, -0.247268f, 0.0752784f),
        new Vector3(0.0140327f, -0.0794684f, 0.0398479f),
        new Vector3(0.18f, 0.139808f, 0.00732703f),
        new Vector3(0.0865568f, -0.260925f, -0.0531584f),
        new Vector3(-0.028133f, -0.247268f, 0.0752784f),
        new Vector3(-0.0140327f, -0.0794684f, 0.0398479f),
        new Vector3(-0.1f, -0.06f, 0f),
        new Vector3(-0.0272986f, -0.403486f, 0.17336f),
        new Vector3(0.00735228f, -0.404342f, -0.17336f),
        new Vector3(-0.0133485f, -0.0400454f, 0.133485f),
        new Vector3(0.1f, -0.06f, 0f),
        new Vector3(0.0272986f, -0.403486f, 0.17336f),
        new Vector3(-0.00735228f, -0.404342f, -0.17336f),
        new Vector3(0.0133485f, -0.0400454f, 0.133485f),
    };
}
