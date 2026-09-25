#!/usr/bin/env python3
"""The current state of this repository, computed from its records.

A SessionStart hook (.claude/settings.json) runs this at session start and after every
compaction, so a session receives the state instead of remembering it. Run it by hand after
a change to see the state move; that is the return. It reads only the repository: git,
memory/, CLAUDE.md. Given the same commit and refs, it reports the same state.

    python3 world/state.py            # print the report
    python3 world/state.py --check    # also exit 1 if a guard fails (CI uses this)
    python3 world/state.py --hook     # read the hook's JSON from stdin; never fails
"""

import datetime
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # run by a hook at every start: leave no files behind

GEN_RING = re.compile(r"^\d{4}-\d{2}-\d{2}-gen-(\d+)(?:-[\w-]+)?\.md$")
THREAD = re.compile(r"^## (T\d+)\s*·\s*(.+)$")
STATUS = re.compile(r"^- status:\s*(\w+)", re.I)
STATUSES = ("open", "waiting", "resting", "closed")
LIMIT = 200


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def read_threads(root):
    path = root / "memory" / "threads.md"
    threads, current = [], None
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = THREAD.match(line)
            if match:
                current = {"id": match[1], "title": match[2].strip(), "status": None}
                threads.append(current)
            elif current and current["status"] is None and STATUS.match(line):
                current["status"] = STATUS.match(line)[1].lower()
    return threads


def guard_problems(root, threads):
    problems = []
    claude = root / "CLAUDE.md"
    if not claude.exists():
        return ["CLAUDE.md is missing"]
    spec = importlib.util.spec_from_file_location("memory_check", root / "experiments/checkable-memory/memory_check.py")
    memory_check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(memory_check)
    problems += memory_check.check(claude, root)[0]
    lines = len(claude.read_text(encoding="utf-8").splitlines())
    if lines > LIMIT:
        problems.append(f"CLAUDE.md has {lines} lines (limit {LIMIT})")
    problems += [f"thread {t['id']} has no status from {'/'.join(STATUSES)}" for t in threads if t["status"] not in STATUSES]
    return problems


def generations(root):
    """The last recorded generation, where it ended, and what happened here since."""
    names = [p.name for p in (root / "memory").glob("*.md") if GEN_RING.match(p.name)]
    if not names:
        return None
    number = max(int(GEN_RING.match(n)[1]) for n in names)
    own = [f"memory/{n}" for n in names if int(GEN_RING.match(n)[1]) == number]
    end = git(root, "log", "-1", "--diff-filter=A", "--format=%H", "--", *own)
    since = git(root, "log", "--format=%h\t%an\t%s", f"{end}..HEAD").splitlines() if end else []
    by_claude = [c for c in since if c.split("\t")[1] == "Claude"]
    return {"number": number, "rings": sorted(own), "end": end[:7], "since": since, "unrecorded": by_claude}


def rings_elsewhere(root):
    """Generation rings on other branches that this checkout does not have."""
    here = set(git(root, "ls-tree", "-r", "--name-only", "HEAD", "--", "memory").splitlines())
    current = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    found = []
    for ref in git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes").splitlines():
        if ref in (current, f"origin/{current}") or ref.endswith("/HEAD") or ref == "origin":
            continue
        for path in git(root, "ls-tree", "-r", "--name-only", ref, "--", "memory").splitlines():
            if GEN_RING.match(pathlib.PurePosixPath(path).name) and path not in here:
                found.append(f"{path} on {ref}")
    return sorted(set(found))


def report(root, source=None):
    head, branch = git(root, "rev-parse", "--short", "HEAD"), git(root, "rev-parse", "--abbrev-ref", "HEAD")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    threads = read_threads(root)
    problems = guard_problems(root, threads)
    gen = generations(root)
    out = [f"source-gate · state computed from the repository at {head or '?'} on {branch or '?'}, {now}"]
    if source == "compact":
        out.append("The context was just compacted. A summary is a memory; this report was re-read from the records.")
    elif source == "resume":
        out.append("This session was resumed. Anything remembered from before may be stale; this report is current.")

    out += ["", "Generations"]
    if gen is None:
        out.append("- no generation has recorded itself yet (a generation ring is memory/<date>-gen-<N>.md)")
    else:
        out.append(f"- last recorded: generation {gen['number']}, ended in {gen['end']} ({', '.join(gen['rings'])})")
        out.append(f"- commits here since then: {len(gen['since'])}, of which {len(gen['unrecorded'])} by Claude")
        for line in gen["since"][:5]:
            short, author, subject = line.split("\t", 2)
            out.append(f"  {short} {author}: {subject[:70]}")
    elsewhere = rings_elsewhere(root)
    if elsewhere:
        out.append("- generation rings on other branches, not in this checkout: " + "; ".join(elsewhere[:5]))

    out += ["", "Guards"]
    out += [f"- {p}" for p in problems] or ["- clean: rings unchanged, pointers resolve, facts point, CLAUDE.md within limit, threads have a status"]

    counts = {s: [t for t in threads if t["status"] == s] for s in STATUSES}
    out += ["", "Threads (memory/threads.md): " + ", ".join(f"{len(v)} {k}" for k, v in counts.items())]
    for status in ("open", "waiting"):
        out += [f"- {status}: {t['id']} {t['title'][:130]}" for t in counts[status]]

    unsettled = problems + ([f"{len(gen['unrecorded'])} commit(s) by Claude after the last generation ring"] if gen and gen["unrecorded"] else [])
    if gen is None:
        unsettled.append("no generation ring")
    dirty = git(root, "status", "--porcelain").splitlines()
    out += ["", "World: " + ("settled" if not unsettled else "unsettled: " + "; ".join(unsettled))]
    if dirty:
        out.append(f"Working tree: {len(dirty)} uncommitted change(s).")
    rings = len([p for p in (root / "memory").glob("*.md") if p.name[:4].isdigit()])
    notes = len(list(root.glob("experiments/*/NOTES.md")))
    out += ["", f"Not loaded automatically: {rings} rings in memory/, thread details, {notes} experiment notes, git history.",
            "Rerun after a change: python3 world/state.py"]
    return "\n".join(out), problems


def main(argv):
    args = argv[1:]
    root = pathlib.Path(args[args.index("--root") + 1]) if "--root" in args else pathlib.Path(__file__).resolve().parent.parent
    if "--hook" in args:
        try:
            source = json.loads(sys.stdin.read() or "{}").get("source")
            print(report(root, source)[0])
        except Exception as error:  # a failing report must never block a session from starting
            print(f"source-gate: the state report failed ({error!r}). Run: python3 world/state.py")
        return 0
    text, problems = report(root)
    print(text)
    return 1 if "--check" in args and problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
