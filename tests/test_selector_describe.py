"""The recommended option's description reads as two sentences, not one run-on."""
import unittest

from decisions import selector


class Describe(unittest.TestCase):
    def test_effect_is_closed_before_the_recommendation(self):
        self.assertEqual(
            selector.describe("clones get smaller", "Move it, since clones stay small."),
            "clones get smaller. Move it, since clones stay small.")

    def test_a_closed_effect_is_left_alone(self):
        self.assertEqual(selector.describe("nothing changes.", "Keep it."),
                         "nothing changes. Keep it.")

    def test_no_recommendation_leaves_the_effect_as_written(self):
        self.assertEqual(selector.describe("the lane passes on", ""), "the lane passes on")

    def test_a_restated_effect_appears_once(self):
        """d-n2 item 10 (L39): a recommendation that restates the effect is the whole
        description; whole words count, so `pins` is not in `Spins`."""
        self.assertEqual(selector.describe("Keeps one interpreter", "Keeps one interpreter."),
                         "Keeps one interpreter.")
        self.assertEqual(selector.describe("clones get smaller.", "Move it: clones get smaller."),
                         "Move it: clones get smaller.")
        self.assertEqual(selector.describe("pins", "Spins it."), "pins. Spins it.")


if __name__ == "__main__":
    unittest.main()
