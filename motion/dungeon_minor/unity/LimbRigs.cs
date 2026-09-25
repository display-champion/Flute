// このファイルは tools/export_unity.mjs が自動生成します。手で編集しないでください。
// 体の種類ごとの手足（鎖）と、代理の関節の初期位置（Motion から見た位置、m）。
using UnityEngine;

public static class LimbRigs
{
    public struct Chain
    {
        public string name;
        public Vector3[] rest;   // 付け根から先へ

        public Chain(string name, params Vector3[] rest) { this.name = name; this.rest = rest; }
    }

    public static readonly string[] Bodies = { "Creature", "RockBall", "Mushroom", "Bee", "Fairy", "Flyer", "Plant", "Spider", "Clockwork", "Whale", "Shears", "Box", "Barrel", "Slug" };

    public static Chain[] Get(string body)
    {
        switch (body)
        {
            case "Creature": return new[]
            {
                new Chain("LegFL", new Vector3(-0.18f, 0.3f, 0.25f), new Vector3(-0.19f, 0.15f, 0.27f), new Vector3(-0.2f, 0f, 0.28f)),
                new Chain("LegBL", new Vector3(-0.18f, 0.3f, -0.3f), new Vector3(-0.19f, 0.15f, -0.32f), new Vector3(-0.2f, 0f, -0.3f)),
                new Chain("Tail", new Vector3(0f, 0.38f, -0.48f), new Vector3(0f, 0.37f, -0.66f), new Vector3(0f, 0.36f, -0.84f)),
                new Chain("Neck", new Vector3(0f, 0.45f, 0.28f), new Vector3(0f, 0.5f, 0.42f)),
                new Chain("LegFR", new Vector3(0.18f, 0.3f, 0.25f), new Vector3(0.19f, 0.15f, 0.27f), new Vector3(0.2f, 0f, 0.28f)),
                new Chain("LegBR", new Vector3(0.18f, 0.3f, -0.3f), new Vector3(0.19f, 0.15f, -0.32f), new Vector3(0.2f, 0f, -0.3f)),
            };
            case "RockBall": return new[]
            {
                new Chain("LegFL", new Vector3(-0.108f, 0.18f, 0.15f), new Vector3(-0.114f, 0.09f, 0.162f), new Vector3(-0.12f, 0f, 0.168f)),
                new Chain("LegBL", new Vector3(-0.108f, 0.18f, -0.18f), new Vector3(-0.114f, 0.09f, -0.192f), new Vector3(-0.12f, 0f, -0.18f)),
                new Chain("LegFR", new Vector3(0.108f, 0.18f, 0.15f), new Vector3(0.114f, 0.09f, 0.162f), new Vector3(0.12f, 0f, 0.168f)),
                new Chain("LegBR", new Vector3(0.108f, 0.18f, -0.18f), new Vector3(0.114f, 0.09f, -0.192f), new Vector3(0.12f, 0f, -0.18f)),
            };
            case "Mushroom": return new[]
            {
                new Chain("ArmL", new Vector3(-0.14f, 0.22f, 0.02f), new Vector3(-0.25f, 0.12f, 0.05f)),
                new Chain("ArmR", new Vector3(0.14f, 0.22f, 0.02f), new Vector3(0.25f, 0.12f, 0.05f)),
                new Chain("FootL", new Vector3(-0.07f, 0.07f, 0f), new Vector3(-0.07f, 0f, 0.07f)),
                new Chain("FootR", new Vector3(0.07f, 0.07f, 0f), new Vector3(0.07f, 0f, 0.07f)),
            };
            case "Bee": return new[]
            {
                new Chain("WingL", new Vector3(-0.03f, 1.1f, -0.02f), new Vector3(-0.3f, 1.14f, -0.05f)),
                new Chain("WingR", new Vector3(0.03f, 1.1f, -0.02f), new Vector3(0.3f, 1.14f, -0.05f)),
                new Chain("HindWingL", new Vector3(-0.03f, 1.08f, -0.07f), new Vector3(-0.2f, 1.1f, -0.12f)),
                new Chain("HindWingR", new Vector3(0.03f, 1.08f, -0.07f), new Vector3(0.2f, 1.1f, -0.12f)),
                new Chain("Leg1L", new Vector3(-0.05f, 0.92f, 0.06f), new Vector3(-0.11f, 0.78f, 0.12f)),
                new Chain("Leg1R", new Vector3(0.05f, 0.92f, 0.06f), new Vector3(0.11f, 0.78f, 0.12f)),
                new Chain("Leg2L", new Vector3(-0.06f, 0.9f, 0f), new Vector3(-0.13f, 0.75f, -0.02f)),
                new Chain("Leg2R", new Vector3(0.06f, 0.9f, 0f), new Vector3(0.13f, 0.75f, -0.02f)),
                new Chain("Leg3L", new Vector3(-0.05f, 0.9f, -0.06f), new Vector3(-0.12f, 0.76f, -0.14f)),
                new Chain("Leg3R", new Vector3(0.05f, 0.9f, -0.06f), new Vector3(0.12f, 0.76f, -0.14f)),
            };
            case "Fairy": return new[]
            {
                new Chain("WingL", new Vector3(-0.05f, 1.25f, -0.02f), new Vector3(-0.22f, 1.3f, -0.05f)),
                new Chain("WingR", new Vector3(0.05f, 1.25f, -0.02f), new Vector3(0.22f, 1.3f, -0.05f)),
            };
            case "Flyer": return new[]
            {
                new Chain("WingL", new Vector3(-0.1f, 1.75f, -0.05f), new Vector3(-0.45f, 1.82f, -0.1f), new Vector3(-0.82f, 1.72f, -0.12f)),
                new Chain("WingR", new Vector3(0.1f, 1.75f, -0.05f), new Vector3(0.45f, 1.82f, -0.1f), new Vector3(0.82f, 1.72f, -0.12f)),
                new Chain("LegL", new Vector3(-0.07f, 1.4f, 0f), new Vector3(-0.07f, 1.22f, 0.04f), new Vector3(-0.07f, 1.06f, 0f)),
                new Chain("LegR", new Vector3(0.07f, 1.4f, 0f), new Vector3(0.07f, 1.22f, 0.04f), new Vector3(0.07f, 1.06f, 0f)),
                new Chain("Tail", new Vector3(0f, 1.42f, -0.12f), new Vector3(0f, 1.38f, -0.35f), new Vector3(0f, 1.33f, -0.56f)),
            };
            case "Plant": return new[]
            {
                new Chain("LeafL", new Vector3(-0.1f, 0.45f, 0f), new Vector3(-0.35f, 0.42f, 0.05f), new Vector3(-0.58f, 0.34f, 0.1f)),
                new Chain("LeafR", new Vector3(0.1f, 0.45f, 0f), new Vector3(0.35f, 0.42f, 0.05f), new Vector3(0.58f, 0.34f, 0.1f)),
            };
            case "Spider": return new[]
            {
                new Chain("Leg1L", new Vector3(-0.1f, 0.2f, 0.12f), new Vector3(-0.3f, 0.32f, 0.18f), new Vector3(-0.42f, 0f, 0.24f)),
                new Chain("Leg1R", new Vector3(0.1f, 0.2f, 0.12f), new Vector3(0.3f, 0.32f, 0.18f), new Vector3(0.42f, 0f, 0.24f)),
                new Chain("Leg2L", new Vector3(-0.1f, 0.2f, 0.03f), new Vector3(-0.3f, 0.32f, 0.05f), new Vector3(-0.42f, 0f, 0.06f)),
                new Chain("Leg2R", new Vector3(0.1f, 0.2f, 0.03f), new Vector3(0.3f, 0.32f, 0.05f), new Vector3(0.42f, 0f, 0.06f)),
                new Chain("Leg3L", new Vector3(-0.1f, 0.2f, -0.06f), new Vector3(-0.3f, 0.32f, -0.08f), new Vector3(-0.42f, 0f, -0.12f)),
                new Chain("Leg3R", new Vector3(0.1f, 0.2f, -0.06f), new Vector3(0.3f, 0.32f, -0.08f), new Vector3(0.42f, 0f, -0.12f)),
                new Chain("Leg4L", new Vector3(-0.1f, 0.2f, -0.15f), new Vector3(-0.3f, 0.32f, -0.21f), new Vector3(-0.42f, 0f, -0.3f)),
                new Chain("Leg4R", new Vector3(0.1f, 0.2f, -0.15f), new Vector3(0.3f, 0.32f, -0.21f), new Vector3(0.42f, 0f, -0.3f)),
            };
            case "Clockwork": return new[]
            {
                new Chain("ArmL", new Vector3(-0.3f, 0.55f, 0.05f), new Vector3(-0.45f, 0.42f, 0.15f), new Vector3(-0.5f, 0.3f, 0.3f)),
                new Chain("ArmR", new Vector3(0.3f, 0.55f, 0.05f), new Vector3(0.45f, 0.42f, 0.15f), new Vector3(0.5f, 0.3f, 0.3f)),
                new Chain("LegL", new Vector3(-0.15f, 0.18f, 0.02f), new Vector3(-0.17f, 0.08f, 0.04f), new Vector3(-0.17f, 0f, 0.06f)),
                new Chain("LegR", new Vector3(0.15f, 0.18f, 0.02f), new Vector3(0.17f, 0.08f, 0.04f), new Vector3(0.17f, 0f, 0.06f)),
                new Chain("LegB", new Vector3(0f, 0.18f, -0.12f), new Vector3(0f, 0.08f, -0.15f), new Vector3(0f, 0f, -0.17f)),
            };
            case "Whale": return new[]
            {
                new Chain("Tail", new Vector3(0f, 0.32f, -0.62f), new Vector3(0f, 0.34f, -0.82f), new Vector3(0f, 0.36f, -1.02f)),
                new Chain("FinL", new Vector3(-0.27f, 0.22f, 0.1f), new Vector3(-0.48f, 0.18f, 0.06f)),
                new Chain("FinR", new Vector3(0.27f, 0.22f, 0.1f), new Vector3(0.48f, 0.18f, 0.06f)),
            };
            case "Shears": return new[]
            {
                new Chain("BladeL", new Vector3(0f, 1.1f, 0f), new Vector3(-0.03f, 1.1f, 0.72f)),
                new Chain("BladeR", new Vector3(0f, 1.1f, 0f), new Vector3(0.03f, 1.1f, 0.72f)),
                new Chain("HandleL", new Vector3(0f, 1.1f, 0f), new Vector3(-0.1f, 1.1f, -0.35f)),
                new Chain("HandleR", new Vector3(0f, 1.1f, 0f), new Vector3(0.1f, 1.1f, -0.35f)),
            };
            case "Box": return new[]
            {
                new Chain("Lid", new Vector3(0f, 0.56f, -0.3f), new Vector3(0f, 0.56f, 0.3f)),
            };
            case "Barrel": return new[]
            {
                new Chain("FootL", new Vector3(-0.1f, 0.08f, 0.02f), new Vector3(-0.1f, 0f, 0.1f)),
                new Chain("FootR", new Vector3(0.1f, 0.08f, 0.02f), new Vector3(0.1f, 0f, 0.1f)),
            };
            case "Slug": return new[]
            {
                new Chain("EyeL", new Vector3(-0.05f, 0.25f, 0.3f), new Vector3(-0.05f, 0.33f, 0.3f), new Vector3(-0.05f, 0.41f, 0.3f)),
                new Chain("EyeR", new Vector3(0.05f, 0.25f, 0.3f), new Vector3(0.05f, 0.33f, 0.3f), new Vector3(0.05f, 0.41f, 0.3f)),
            };
            default: return new Chain[0];
        }
    }
}
