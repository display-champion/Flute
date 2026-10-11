import unittest

from cascadeur_session.motion_names import KEEP_HEIGHT, LOOP, ONE_SHOT, classify, clip_name, warnings


class ClassifyTest(unittest.TestCase):
    def test_doc_examples(self):
        self.assertEqual(classify("fina_slash_A.fbx"), ONE_SHOT)
        self.assertEqual(classify("fina_jump_start.fbx"), KEEP_HEIGHT)
        self.assertEqual(classify("fina_punch_straight.fbx"), ONE_SHOT)

    def test_loop(self):
        for n in ("fina_idle.fbx", "fina_walk_fwd.fbx", "fina_run.fbx", "fina_wait_A.fbx"):
            self.assertEqual(classify(n), LOOP, n)

    def test_keep_height_words(self):
        for n in ("fina_leap.fbx", "fina_dive.fbx", "fina_backflip.fbx", "fina_vault_box.fbx"):
            self.assertEqual(classify(n), KEEP_HEIGHT, n)

    def test_case_and_path(self):
        self.assertEqual(classify(r"D:\x\Fina_JUMP.fbx"), KEEP_HEIGHT)
        self.assertEqual(clip_name("a/b/fina_slash_A.fbx"), "fina_slash_A")

    def test_jump_wins_over_loop(self):
        self.assertEqual(classify("fina_run_jump.fbx"), KEEP_HEIGHT)

    def test_warnings(self):
        self.assertEqual(warnings("fina_slash_A.fbx"), [])
        self.assertTrue(warnings("fina_slash_A.anim"))
        self.assertTrue(warnings("fina_brunt.fbx"))  # "run" が語中に含まれる


if __name__ == "__main__":
    unittest.main()
