import contextlib
import copy
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import receipt

# Throwaway fixture repos must not pick up the host's git config (e.g. commit signing).
os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
os.environ["GIT_CONFIG_NOSYSTEM"] = "1"


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Workshop:
    """A local bare repo standing in for GitHub, and a clone to work in."""

    def __init__(self, root):
        self.remote = root / "remote.git"
        self.work = root / "work"
        run("git", "init", "-q", "--bare", "-b", "main", str(self.remote))
        run("git", "init", "-q", "-b", "main", str(self.work))
        self.git("config", "user.name", "tester")
        self.git("config", "user.email", "tester@example.invalid")
        self.write("README.md", "hello\n")
        self.commit("initial")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "-u", "origin", "main")

    def git(self, *args):
        return run("git", *args, cwd=self.work)

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def snap(self):
        return receipt.snapshot(self.work, "origin")


class ReceiptTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.ws = Workshop(Path(tmp.name))


class WhatAReceiptCatches(ReceiptTestCase):
    def test_nothing_done_means_no_changes(self):
        before = self.ws.snap()
        self.assertEqual(receipt.compare(before, self.ws.snap()), {})

    def test_added_modified_and_removed_files_including_untracked(self):
        self.ws.write("keep.txt", "a\n")
        self.ws.write("gone.txt", "b\n")
        self.ws.commit("two files")
        before = self.ws.snap()
        self.ws.write("keep.txt", "changed\n")
        (self.ws.work / "gone.txt").unlink()
        self.ws.write("new/untracked.txt", "never added to git\n")
        changes = receipt.compare(before, self.ws.snap())
        self.assertEqual(changes["files"], {
            "added": ["new/untracked.txt"],
            "modified": ["keep.txt"],
            "removed": ["gone.txt"],
        })

    def test_local_commit_moves_head(self):
        before = self.ws.snap()
        self.ws.write("x.txt", "x\n")
        new_head = self.ws.commit("local only")
        changes = receipt.compare(before, self.ws.snap())
        self.assertEqual(changes["head"]["after"], new_head)
        self.assertNotIn("remote_refs", changes)

    def test_new_branch_is_seen_even_if_head_did_not_move(self):
        before = self.ws.snap()
        self.ws.git("branch", "side")
        changes = receipt.compare(before, self.ws.snap())
        self.assertNotIn("head", changes)
        self.assertEqual(changes["local_refs"]["added"], ["refs/heads/side"])

    def test_push_is_seen_on_the_remote(self):
        before = self.ws.snap()
        self.ws.git("push", "-q", "origin", "HEAD:refs/heads/pushed")
        changes = receipt.compare(before, self.ws.snap())
        self.assertEqual(changes["remote_refs"]["added"], ["refs/heads/pushed"])

    def test_snapshots_from_different_tool_versions_are_flagged(self):
        before = self.ws.snap()
        before["tool_version"] = "an older receipt.py"
        self.assertIn("different versions", receipt.compare(before, self.ws.snap())["tool_version"])
        del before["tool_version"]
        self.assertIn("tool_version", receipt.compare(before, self.ws.snap()))

    def test_unreadable_remote_is_unknown_not_unchanged(self):
        before = self.ws.snap()
        self.ws.git("remote", "set-url", "origin", str(self.ws.remote) + "-missing")
        after = self.ws.snap()
        self.assertIsNotNone(after["remote_error"])
        self.assertEqual(receipt.compare(before, after)["remote_refs"], "unknown: remote could not be read")


class WhatVerifyCatches(ReceiptTestCase):
    def make(self):
        before = self.ws.snap()
        self.ws.write("work.txt", "done\n")
        return before, receipt.make_receipt(before, self.ws.snap())

    def test_matching_state_verifies(self):
        before, r = self.make()
        self.assertEqual(receipt.verify(r, self.ws.snap(), receipt.fingerprint(before)), [])

    def test_change_after_the_receipt_is_caught(self):
        _, r = self.make()
        self.ws.write("work.txt", "quietly changed later\n")
        problems = receipt.verify(r, self.ws.snap())
        self.assertEqual(len(problems), 1)
        self.assertIn("no longer matches", problems[0])

    def test_edited_summary_is_caught(self):
        _, r = self.make()
        r["changes"] = {}
        self.assertIn("does not match the snapshots", receipt.verify(r, self.ws.snap())[0])

    def test_hiding_a_change_by_rewriting_after_is_caught_while_the_change_exists(self):
        before, r = self.make()
        r["after"] = copy.deepcopy(before)
        r["changes"] = {}
        self.assertTrue(receipt.verify(r, self.ws.snap()))


class CommandLine(ReceiptTestCase):
    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = receipt.main(["--repo", str(self.ws.work), *args])
        return code, out.getvalue()

    def test_full_round_trip_and_exit_codes(self):
        files = self.ws.work.parent
        _, before = self.cli("snapshot")
        (files / "before.json").write_text(before)
        _, anchor = self.cli("fingerprint", str(files / "before.json"))
        self.ws.write("work.txt", "done\n")
        _, r = self.cli("receipt", str(files / "before.json"))
        (files / "receipt.json").write_text(r)

        self.assertIn("files: added work.txt", self.cli("show", str(files / "receipt.json"))[1])
        code, out = self.cli("verify", str(files / "receipt.json"))
        self.assertEqual(code, 0)
        self.assertIn("NOTE", out)
        code, out = self.cli("verify", str(files / "receipt.json"), "--before-fingerprint", anchor.strip())
        self.assertEqual((code, "NOTE" in out), (0, False))
        self.ws.write("work.txt", "changed after the receipt\n")
        self.assertEqual(self.cli("verify", str(files / "receipt.json"))[0], 1)


class WhatAReceiptCannotSee(ReceiptTestCase):
    """Each test here passes because of a blind spot. They document limits, not features."""

    def test_forged_before_state_verifies_unless_before_was_anchored_elsewhere(self):
        honest_before = self.ws.snap()
        anchor = receipt.fingerprint(honest_before)
        self.ws.write("README.md", "rewritten by the actor\n")
        after = self.ws.snap()
        forged_before = copy.deepcopy(honest_before)
        forged_before["files"]["README.md"] = after["files"]["README.md"]
        forged = receipt.make_receipt(forged_before, after)

        self.assertEqual(forged["changes"], {}, "the forged receipt claims nothing changed")
        self.assertEqual(receipt.verify(forged, self.ws.snap()), [], "and passes a plain verify")
        self.assertTrue(receipt.verify(forged, self.ws.snap(), anchor),
                        "only a fingerprint kept by someone else exposes it")

    def test_push_then_restore_leaves_no_trace_in_the_receipt(self):
        before = self.ws.snap()
        original = before["head"]
        self.ws.write("secret.txt", "published for a moment\n")
        pushed = self.ws.commit("briefly public")
        self.ws.git("push", "-q", "origin", "main")
        self.ws.git("push", "-q", "--force", "origin", f"{original}:main")
        self.ws.git("reset", "-q", "--hard", original)

        self.assertEqual(receipt.compare(before, self.ws.snap()), {})
        # The evidence exists, but only in places the receipt does not look:
        run("git", "cat-file", "-e", pushed, cwd=self.ws.remote)
        self.assertIn(pushed[:7], self.ws.git("reflog", "--format=%h"))

    def test_change_and_revert_inside_the_session_is_invisible(self):
        before = self.ws.snap()
        self.ws.write("README.md", "temporary\n")
        self.ws.write("README.md", "hello\n")
        self.assertEqual(receipt.compare(before, self.ws.snap()), {})


if __name__ == "__main__":
    unittest.main()
