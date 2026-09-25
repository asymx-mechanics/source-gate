import hashlib
import io
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

import state

REPO = pathlib.Path(__file__).resolve().parent.parent
_dirs = []


def tearDownModule():
    for d in _dirs:
        d.cleanup()


class World:
    """A small repository with a settled world: one listed generation ring, clean guards."""

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()
        _dirs.append(self.dir)
        self.root = pathlib.Path(self.dir.name)
        self.git("init", "-q", "-b", "main")
        guard = self.root / "experiments/checkable-memory"
        guard.mkdir(parents=True)
        shutil.copy(REPO / "experiments/checkable-memory/memory_check.py", guard)
        self.write("CLAUDE.md", "# Notes\n\n## Facts, verified\n\n- Seen once (seen only in session 2026-09-25).\n")
        self.write("memory/threads.md", "# Threads\n\n## T1 · Is it visible logged out?\n- status: waiting\n")
        self.ring("2026-09-25-gen-0.md", "generation 0\n")
        self.commit("Claude", "Generation 0 ends")

    def git(self, *args, author=None):
        who = ["-c", f"user.name={author}", "-c", "user.email=x@example.com"] if author else []
        return subprocess.run(["git", "-C", str(self.root), *who, *args], capture_output=True, text=True, check=True).stdout

    def write(self, path, text):
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text)

    def ring(self, name, text):
        self.write(f"memory/{name}", text)
        with open(self.root / "memory/RINGS.sha256", "a") as f:
            f.write(f"{hashlib.sha256(text.encode()).hexdigest()}  memory/{name}\n")

    def commit(self, author, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message, author=author)

    def run(self, *flags):
        out = io.StringIO()
        with redirect_stdout(out):
            code = state.main(["state.py", "--root", str(self.root), *flags])
        return out.getvalue(), code


class Settled(unittest.TestCase):
    def test_a_recorded_world_with_clean_guards_is_settled(self):
        text, code = World().run("--check")
        self.assertIn("World: settled", text)
        self.assertIn("last recorded: generation 0", text)
        self.assertEqual(code, 0)

    def test_a_commit_by_someone_else_is_listed_but_does_not_unsettle(self):
        world = World()
        world.write("README.md", "owner's edit\n")
        world.commit("owner", "Owner edits the README")
        text, _ = world.run()
        self.assertIn("World: settled", text)
        self.assertIn("owner: Owner edits the README", text)


class Unsettled(unittest.TestCase):
    def test_an_edited_ring_fails_a_guard(self):
        world = World()
        world.write("memory/2026-09-25-gen-0.md", "generation 0, smoothed\n")
        text, code = world.run("--check")
        self.assertIn("World: unsettled", text)
        self.assertEqual(code, 1)

    def test_work_by_claude_after_the_last_ring_is_unrecorded_but_not_a_guard_failure(self):
        world = World()
        world.write("notes.md", "more work\n")
        world.commit("Claude", "Work without a ring")
        text, code = world.run("--check")
        self.assertIn("1 commit(s) by Claude after the last generation ring", text)
        self.assertEqual(code, 0)

    def test_a_thread_without_a_status_fails_a_guard(self):
        world = World()
        world.write("memory/threads.md", "# Threads\n\n## T1 · A question\n- would move it: nothing\n")
        text, code = world.run("--check")
        self.assertIn("thread T1 has no status", text)
        self.assertEqual(code, 1)

    def test_a_projection_over_the_limit_fails_a_guard(self):
        world = World()
        world.write("CLAUDE.md", "# Notes\n" + "line\n" * 201)
        self.assertEqual(world.run("--check")[1], 1)

    def test_a_ring_written_but_not_committed_has_not_ended(self):
        world = World()
        world.ring("2026-09-26-gen-1.md", "generation 1\n")
        text, _ = world.run()
        self.assertIn("generation 1, its ring is not committed yet", text)
        self.assertIn("World: unsettled", text)

    def test_no_generation_ring_means_unsettled(self):
        world = World()
        world.git("rm", "-q", "memory/2026-09-25-gen-0.md")
        world.write("memory/RINGS.sha256", "")
        world.commit("owner", "Remove the ring")
        text, _ = world.run()
        self.assertIn("no generation has recorded itself yet", text)
        self.assertIn("World: unsettled", text)


class Discovery(unittest.TestCase):
    def test_a_generation_ring_on_another_branch_is_found(self):
        world = World()
        world.git("checkout", "-q", "-b", "later")
        world.ring("2026-09-26-gen-1.md", "generation 1\n")
        world.commit("Claude", "Generation 1 ends")
        world.git("checkout", "-q", "main")
        text, _ = world.run()
        self.assertIn("memory/2026-09-26-gen-1.md on later", text)
        self.assertIn("last recorded: generation 0", text)

    def test_finding_nothing_names_the_refs_it_looked_at(self):
        world = World()
        text, _ = world.run()
        self.assertIn("none on the 0 other ref(s) this clone has. To see GitHub's: git fetch origin", text)
        world.git("branch", "plain")
        text, _ = world.run()
        self.assertIn("none on the 1 other ref(s) this clone has (plain)", text)


class Hook(unittest.TestCase):
    def hook(self, root, stdin):
        return subprocess.run([sys.executable, "-B", str(REPO / "world/state.py"), "--hook", "--root", str(root)],
                              input=stdin, capture_output=True, text=True)

    def test_after_compaction_the_report_says_it_was_re_read(self):
        result = self.hook(World().root, '{"source": "compact"}')
        self.assertIn("A summary is a memory", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_a_failing_report_never_blocks_a_session(self):
        with tempfile.TemporaryDirectory() as empty:
            result = self.hook(empty, "not json")
        self.assertEqual(result.returncode, 0)
        self.assertIn("the state report failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
