import unittest

from format_only import word_changes

SOURCE = """THIS IS NOT a summary!!!
Keep the line. Keep the 🌱 and the 12/05.
The source_file stays the source."""


class FormatOnlyPasses(unittest.TestCase):
    def test_reflow_headings_bullets_and_emphasis(self):
        output = """# THIS IS NOT a summary!!!

- Keep the line.
- Keep the **🌱** and the *12/05.*

> The `source_file` stays the source."""
        self.assertEqual(word_changes(SOURCE, output), [])


class RewritesAreCaught(unittest.TestCase):
    def assertCaught(self, output):
        self.assertTrue(word_changes(SOURCE, output), "a rewrite passed as format only")

    def test_changed_word(self):
        self.assertCaught(SOURCE.replace("Keep the line.", "Follow the line."))

    def test_capitals_smoothed(self):
        self.assertCaught(SOURCE.replace("THIS IS NOT", "This is not"))

    def test_punctuation_smoothed(self):
        self.assertCaught(SOURCE.replace("!!!", "!"))

    def test_symbol_dropped(self):
        self.assertCaught(SOURCE.replace(" 🌱", ""))

    def test_order_changed(self):
        lines = SOURCE.splitlines()
        self.assertCaught("\n".join([lines[1], lines[0], lines[2]]))

    def test_inner_underscore_is_part_of_the_word(self):
        self.assertCaught(SOURCE.replace("source_file", "sourcefile"))

    def test_added_sentence(self):
        self.assertCaught(SOURCE + "\nIn short: keep everything.")


class WhatItCannotSee(unittest.TestCase):
    """Each passes because of a limit: format that still changes weight or rhythm."""

    def test_new_emphasis_passes_although_it_shifts_weight(self):
        self.assertEqual(word_changes(SOURCE, SOURCE.replace("the source.", "the **source**.")), [])

    def test_line_breaks_in_a_poem_pass_although_rhythm_changes(self):
        poem = "slow\nwater\nstays"
        self.assertEqual(word_changes(poem, "slow water stays"), [])

    def test_a_star_used_as_a_symbol_is_stripped_like_emphasis(self):
        self.assertEqual(word_changes("rating *", "rating"), [])


HEDGED = "The fix possibly reduces crashes, but only on machines with more than 8 GB of memory."


class SummariesShowWhatTheyDropped(unittest.TestCase):
    """A hedge or a condition is carried by words, so dropping it is visible, if compared with the source."""

    def lost(self, source, output):
        return " ".join(old for op, old, new in word_changes(source, output) if op in ("delete", "replace"))

    def test_a_dropped_hedge_is_listed(self):
        self.assertIn("possibly", self.lost(HEDGED, HEDGED.replace("possibly ", "")))

    def test_loss_spread_over_copies_shows_only_against_the_source(self):
        first = HEDGED.replace("possibly ", "")
        second = "The fix reduces crashes."
        self.assertNotIn("possibly", self.lost(first, second))
        self.assertIn("possibly", self.lost(HEDGED, second))
        self.assertIn("only", self.lost(HEDGED, second))

    def test_a_paraphrased_hedge_is_only_a_replacement(self):
        """Whether "may" kept "possibly", and "some machines" the condition, is for a human to judge."""
        changes = word_changes(HEDGED, "The fix may reduce crashes on some machines.")
        self.assertEqual({op for op, old, new in changes}, {"replace"})


if __name__ == "__main__":
    unittest.main()
