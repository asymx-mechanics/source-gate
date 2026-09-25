import hashlib
import pathlib
import tempfile
import unittest

from memory_check import check

_dirs = []


def tearDownModule():
    for d in _dirs:
        d.cleanup()


class Repo:
    def __init__(self, claude_md, files=()):
        self.dir = tempfile.TemporaryDirectory()
        _dirs.append(self.dir)
        self.root = pathlib.Path(self.dir.name)
        for f in files:
            (self.root / f).parent.mkdir(parents=True, exist_ok=True)
            (self.root / f).write_text("evidence\n")
        (self.root / "CLAUDE.md").write_text(claude_md)

    def ring(self, name, text, listed=True, digest=None):
        (self.root / "memory").mkdir(exist_ok=True)
        (self.root / "memory" / name).write_text(text)
        if listed:
            digest = digest or hashlib.sha256(text.encode()).hexdigest()
            with open(self.root / "memory" / "RINGS.sha256", "a") as f:
                f.write(f"{digest}  memory/{name}\n")

    def problems(self):
        return check(self.root / "CLAUDE.md", self.root)[0]


FACTS = "## Facts, verified\n\n"


class FactsMustSayHowTheyAreKnown(unittest.TestCase):
    def test_a_fact_with_no_pointer_is_flagged(self):
        self.assertTrue(Repo(FACTS + "- Pushes appear under the owner's account.\n").problems())

    def test_a_fact_pointing_to_evidence_passes(self):
        repo = Repo(FACTS + "- Pushes appear under the owner. See `ev/notes.md`.\n", ["ev/notes.md"])
        self.assertEqual(repo.problems(), [])

    def test_a_fact_seen_only_in_one_session_passes(self):
        self.assertEqual(Repo(FACTS + "- A force-push was refused (seen only in session 2026-09-25).\n").problems(), [])

    def test_seen_only_at_the_start_of_a_sentence_counts(self):
        self.assertEqual(Repo(FACTS + "- A Routine stored no repository. Seen only in session 2026-09-25.\n").problems(), [])

    def test_a_fact_pointing_to_a_url_passes(self):
        self.assertEqual(Repo(FACTS + "- Auto memory is machine-local (https://code.claude.com/docs/en/memory).\n").problems(), [])

    def test_a_dangling_pointer_is_flagged(self):
        self.assertTrue(Repo(FACTS + "- Signed by `claude`. See `ev/gone.md`.\n").problems())

    def test_a_dangling_pointer_outside_facts_is_flagged(self):
        self.assertTrue(Repo("## Open questions\n\n- Does `ev/gone.nix` still evaluate?\n").problems())

    def test_a_nested_bullet_belongs_to_its_fact(self):
        text = FACTS + "- A merge looks like the owner's. See `ev/n.md`.\n  - `merged_by` the owner;\n\n  So nobody can tell.\n"
        self.assertEqual(Repo(text, ["ev/n.md"]).problems(), [])

    def test_notes_outside_facts_need_no_pointer(self):
        text = "## Open questions\n\n- Is the activity visible when logged out?\n\nLeft out on purpose:\n- approval I received.\n"
        self.assertEqual(Repo(text).problems(), [])

    def test_a_label_line_ends_the_facts_section(self):
        text = FACTS + "- Signed by `claude`. See `ev/n.md`.\n\nLeft out on purpose:\n- approval I received.\n"
        self.assertEqual(Repo(text, ["ev/n.md"]).problems(), [])

    def test_ticked_words_and_absolute_paths_are_not_pointers(self):
        text = "Uses `merged_at`, `/no-such-dir/nix` and `re-tested YYYY-MM-DD: held`.\n"
        self.assertEqual(Repo(text).problems(), [])


class RingsDoNotChange(unittest.TestCase):
    def test_an_unchanged_ring_passes(self):
        repo = Repo("notes\n")
        repo.ring("2026-09-25.md", "what happened\n")
        self.assertEqual(repo.problems(), [])

    def test_an_edited_ring_is_flagged(self):
        repo = Repo("notes\n")
        repo.ring("2026-09-25.md", "what happened\n")
        (repo.root / "memory" / "2026-09-25.md").write_text("what happened, smoothed\n")
        self.assertTrue(repo.problems())

    def test_an_unlisted_ring_is_flagged(self):
        repo = Repo("notes\n")
        repo.ring("2026-09-25.md", "what happened\n", listed=False)
        self.assertTrue(repo.problems())

    def test_a_listed_ring_that_is_gone_is_flagged(self):
        repo = Repo("notes\n")
        repo.ring("2026-09-25.md", "what happened\n")
        (repo.root / "memory" / "2026-09-25.md").unlink()
        self.assertTrue(repo.problems())


if __name__ == "__main__":
    unittest.main()
