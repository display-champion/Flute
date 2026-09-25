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
        new Vector3(0f, 0.1199589f, 0.003141234f),
        new Vector3(0f, 0.219807f, 0.009212644f),
        new Vector3(0f, 0.1997259f, 0.01046719f),
        new Vector3(0f, 0.09986295f, 0.005233596f),
        new Vector3(0f, -0.006280315f, 0.1198355f),
        new Vector3(-0.18f, 0.1398081f, 0.007327034f),
        new Vector3(-0.08655681f, -0.2609255f, -0.05315836f),
        new Vector3(0.02813298f, -0.2472685f, 0.07527838f),
        new Vector3(0.01403271f, -0.07946842f, 0.03984787f),
        new Vector3(0.18f, 0.1398081f, 0.007327034f),
        new Vector3(0.08655681f, -0.2609255f, -0.05315836f),
        new Vector3(-0.02813298f, -0.2472685f, 0.07527838f),
        new Vector3(-0.01403271f, -0.07946842f, 0.03984787f),
        new Vector3(-0.1f, -0.06f, 0f),
        new Vector3(-0.02729865f, -0.4034861f, 0.1733603f),
        new Vector3(0.007352284f, -0.4043416f, -0.1733603f),
        new Vector3(-0.01334848f, -0.04004543f, 0.1334848f),
        new Vector3(0.1f, -0.06f, 0f),
        new Vector3(0.02729865f, -0.4034861f, 0.1733603f),
        new Vector3(-0.007352284f, -0.4043416f, -0.1733603f),
        new Vector3(0.01334848f, -0.04004543f, 0.1334848f),
    };
}
