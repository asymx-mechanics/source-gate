import json
import unittest

from reply_patterns import measure, turns


def user(text, **extra):
    return json.dumps({"type": "user", "timestamp": "2026-09-25T15:00:00Z", "message": {"role": "user", "content": text}, **extra})


def tool_result():
    return json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}})


def reply(text):
    return json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}})


class Turns(unittest.TestCase):
    def test_the_last_reply_of_a_turn_counts(self):
        lines = [user("what now?"), reply("Looking."), tool_result(), reply("Done. Wil je dat ik verder ga?")]
        self.assertEqual([r for _, r in turns(lines)], ["Done. Wil je dat ik verder ga?"])

    def test_tool_results_do_not_start_a_turn(self):
        lines = [user("a"), reply("one"), tool_result(), reply("two"), user("b"), reply("three")]
        self.assertEqual([r for _, r in turns(lines)], ["two", "three"])

    def test_summaries_and_reminders_are_not_prompts(self):
        lines = [user("a"), reply("one"), user("This session is being continued from ..."), reply("two")]
        self.assertEqual([r for _, r in turns(lines)], ["two"])


class Measure(unittest.TestCase):
    def test_an_ending_offer_is_seen(self):
        self.assertTrue(measure("Het werk is af.\n\nWil je dat ik #6 in de gaten houd?")[0])

    def test_a_statement_ending_is_not_an_offer(self):
        self.assertFalse(measure("Wil je dat ik kijk? Ik heb al gekeken.\n\nHet klopt.")[0])

    def test_hand_over_phrases_are_listed(self):
        self.assertEqual(measure("Alleen jij kunt dat instellen; dat beslis jij.")[1], ["alleen jij", "beslis jij"])

    def test_the_framing_sentence_is_invisible_to_it(self):
        """The limit: the sentence that prompted the owner's question has no hand-over phrase."""
        self.assertEqual(measure("Het werkt alleen als er iemand kijkt.")[1], [])


if __name__ == "__main__":
    unittest.main()
