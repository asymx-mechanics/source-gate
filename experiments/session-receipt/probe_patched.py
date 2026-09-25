#!/usr/bin/env python3
"""PROBE, not a successor: receipt.py with the obvious local holes patched.

It exists only so `attacks.py --tool probe_patched.py` can show which attacks are patchable
by looking harder, and which are not. See NOTES.md.
"""

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_VERSION = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                            errors="surrogateescape")
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def entry(path):
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode):
        return "symlink " + os.readlink(path)
    return ("x " if st.st_mode & 0o111 else "- ") + hashlib.sha256(path.read_bytes()).hexdigest()


def file_hashes(repo):
    # PROBE: walk the disk instead of asking git, so ignored files, nested repos and symlinks count.
    repo = Path(repo)
    hashes = {}
    for dirpath, dirnames, filenames in os.walk(repo):
        if Path(dirpath) == repo and ".git" in dirnames:
            dirnames.remove(".git")
        linked_dirs = [d for d in dirnames if Path(dirpath, d).is_symlink()]
        for name in filenames + linked_dirs:
            path = Path(dirpath, name)
            hashes[str(path.relative_to(repo))] = entry(path)
    return hashes


def git_internals(repo):
    git_dir = Path(repo, ".git")
    found = {}
    for name in ("config", "hooks", "info"):
        top = git_dir / name
        paths = [top] if top.is_file() else sorted(p for p in top.rglob("*") if p.is_file() or p.is_symlink())
        for p in paths:
            found[str(p.relative_to(git_dir))] = entry(p)
    return found


def index_entries(repo):
    entries = {}
    for item in filter(None, git(repo, "ls-files", "--stage", "-z").split("\0")):
        meta, path = item.split("\t", 1)
        entries[path] = meta
    return entries


def remote_url(repo, remote):
    try:
        return git(repo, "remote", "get-url", remote).strip()
    except RuntimeError:
        return None


def local_refs(repo):
    out = git(repo, "for-each-ref", "--format=%(refname) %(objectname)")
    refs = {}
    for line in out.splitlines():
        name, sha = line.split(" ", 1)
        refs[name] = sha
    return refs


def remote_refs(repo, remote):
    try:
        out = git(repo, "ls-remote", remote)
    except RuntimeError as err:
        return None, str(err)
    refs = {}
    for line in out.splitlines():
        sha, name = line.split("\t", 1)
        refs[name] = sha
    return refs, None


def snapshot(repo, remote):
    refs, error = remote_refs(repo, remote)
    return {
        "taken_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool_version": TOOL_VERSION,
        "head": git(repo, "rev-parse", "HEAD").strip(),
        "branch": git(repo, "branch", "--show-current").strip(),
        "local_refs": local_refs(repo),
        "files": file_hashes(repo),
        "index": index_entries(repo),
        "git_internals": git_internals(repo),
        "remote_url": remote_url(repo, remote),
        "remote": remote,
        "remote_refs": refs,
        "remote_error": error,
    }


def fingerprint(snap):
    canonical = json.dumps(snap, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def diff_maps(before, after):
    return {
        "added": sorted(after.keys() - before.keys()),
        "removed": sorted(before.keys() - after.keys()),
        "modified": sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
    }


def compare(before, after):
    changes = {}
    if before.get("tool_version") != after.get("tool_version"):
        changes["tool_version"] = ("differs: the snapshots were made by different versions of receipt.py,"
                                   " so some differences below may come from the tool, not the repository")
    for key in ("head", "branch", "remote_url"):
        if before[key] != after[key]:
            changes[key] = {"before": before[key], "after": after[key]}
    for key in ("files", "local_refs", "index", "git_internals"):
        d = diff_maps(before[key], after[key])
        if any(d.values()):
            changes[key] = d
    if before["remote_refs"] is None or after["remote_refs"] is None:
        # Not being able to look is not the same as nothing having changed.
        changes["remote_refs"] = "unknown: remote could not be read"
    else:
        d = diff_maps(before["remote_refs"], after["remote_refs"])
        if any(d.values()):
            changes["remote_refs"] = d
    return changes


def make_receipt(before, after):
    return {"before": before, "after": after, "changes": compare(before, after)}


def verify(receipt, current, before_fingerprint=None):
    problems = []
    if before_fingerprint and fingerprint(receipt["before"]) != before_fingerprint:
        problems.append("the receipt's 'before' state is not the one that was fingerprinted at the start")
    if compare(receipt["before"], receipt["after"]) != receipt["changes"]:
        problems.append("the 'changes' summary does not match the snapshots it claims to summarize")
    drift = compare(receipt["after"], current)
    if drift:
        problems.append("the repository no longer matches the receipt's 'after' state: "
                        + json.dumps(drift, sort_keys=True))
    return problems


def describe(receipt):
    before, after, changes = receipt["before"], receipt["after"], receipt["changes"]
    lines = [f"from {before['taken_at']} to {after['taken_at']}"]
    labels = {
        "tool_version": "tool",
        "head": "HEAD",
        "branch": "branch",
        "files": "files",
        "local_refs": "local refs",
        "remote_refs": f"remote '{after['remote']}'",
    }
    for key, label in labels.items():
        change = changes.get(key)
        if change is None:
            shown = f" ({after[key]})" if key in ("head", "branch") else ""
            lines.append(f"{label}: unchanged{shown}")
        elif isinstance(change, str):
            lines.append(f"{label}: {change}")
        elif "before" in change:
            lines.append(f"{label}: {change['before']} -> {change['after']}")
        else:
            for kind in ("added", "modified", "removed"):
                for name in change[kind]:
                    lines.append(f"{label}: {kind} {name}")
    return "\n".join(lines)


def load(path):
    return json.loads(Path(path).read_text())


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("snapshot", help="print the current state as JSON")
    p.add_argument("--remote", default="origin")
    p = sub.add_parser("fingerprint", help="print a short fingerprint of a saved snapshot, to keep somewhere else")
    p.add_argument("snapshot")
    p = sub.add_parser("receipt", help="compare a saved snapshot with the current state and print a receipt")
    p.add_argument("before")
    p = sub.add_parser("show", help="print a receipt as plain text")
    p.add_argument("receipt")
    p = sub.add_parser("verify", help="check a receipt against the current state; exit 1 on any mismatch")
    p.add_argument("receipt")
    p.add_argument("--before-fingerprint")
    args = parser.parse_args(argv)

    if args.command == "snapshot":
        emit(snapshot(args.repo, args.remote))
    elif args.command == "fingerprint":
        print(fingerprint(load(args.snapshot)))
    elif args.command == "receipt":
        before = load(args.before)
        emit(make_receipt(before, snapshot(args.repo, before["remote"])))
    elif args.command == "show":
        print(describe(load(args.receipt)))
    elif args.command == "verify":
        receipt = load(args.receipt)
        problems = verify(receipt, snapshot(args.repo, receipt["after"]["remote"]), args.before_fingerprint)
        for problem in problems:
            print("MISMATCH:", problem)
        if problems:
            return 1
        print("OK: the repository matches the receipt, and the summary matches its snapshots")
        if not args.before_fingerprint:
            print("NOTE: 'before' was not checked against a fingerprint kept by someone else,"
                  " so this receipt could still misstate the starting point")
    return 0


if __name__ == "__main__":
    sys.exit(main())
