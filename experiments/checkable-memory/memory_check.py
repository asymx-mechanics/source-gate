#!/usr/bin/env python3
"""Does each remembered fact say how it can be checked?

Reads CLAUDE.md, the notes a later session is given, and checks three things:
1. Every note in a "Facts" section carries a pointer: a `path` in backticks that exists in
   this repository, or a URL (not fetched), or says it was "seen only" in one session.
2. No pointer is dangling: every relative path in backticks exists.
3. Rings do not change: every dated file in memory/ is listed in memory/RINGS.sha256,
   and still has the hash listed there.

    python3 memory_check.py [CLAUDE.md]     # run from the repository root; exit 0 = clean
"""

import hashlib
import pathlib
import re
import sys

TICKED = re.compile(r"`([^`\s]+)`")
PATHLIKE = re.compile(r"^(?!/)[\w.-]+(?:/[\w.-]*)*$")
RING = re.compile(r"^\d{4}-\d{2}-\d{2}.*\.md$")
URL = re.compile(r"https?://\S+")


def sections(text):
    """Yield (section name, notes). A note is a top-level bullet with its indented lines."""
    name, notes, note = "(top)", [], None
    for line in text.splitlines():
        heading = line.startswith("## ")
        label = not heading and line.rstrip().endswith(":") and not line[:1].isspace() and not line.startswith(("- ", "`"))
        if heading or label:
            yield name, notes
            name, notes, note = (line[3:] if heading else line.rstrip(":")), [], None
        elif line.startswith("- "):
            note = [line[2:]]
            notes.append(note)
        elif note is not None and (line[:1].isspace() or line.startswith("`") or not line.strip()):
            note.append(line.strip())
        else:
            note = None
    yield name, notes


def is_path(token):
    return bool(PATHLIKE.match(token)) and ("/" in token or "." in token.strip("."))


def check(claude_md, root="."):
    root = pathlib.Path(root)
    text = pathlib.Path(claude_md).read_text(encoding="utf-8")
    problems, counts = [], {}
    for token in {t for t in TICKED.findall(text) if is_path(t)}:
        if not (root / token).exists():
            problems.append(f"dangling pointer: `{token}`")
    for name, notes in sections(text):
        if not notes:
            continue
        pointed = [n for n in notes if URL.search(" ".join(n)) or any(is_path(t) and (root / t).exists() for t in TICKED.findall(" ".join(n)))]
        seen_only = [n for n in notes if "seen only" in " ".join(n).lower()]
        counts[name] = (len(notes), len(pointed), len(seen_only))
        if name.startswith("Facts"):
            for n in notes:
                if n not in pointed and n not in seen_only:
                    problems.append(f"fact with no pointer: {n[0][:70]}")
    problems += check_rings(root)
    return problems, counts


def check_rings(root):
    ring_dir, listed, problems = root / "memory", {}, []
    manifest = ring_dir / "RINGS.sha256"
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                digest, path = line.split(maxsplit=1)
                listed[path.strip()] = digest
    for path, digest in listed.items():
        file = root / path
        if not file.exists():
            problems.append(f"listed ring missing: {path}")
        elif hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            problems.append(f"ring changed since listed: {path}")
    if ring_dir.is_dir():
        for file in sorted(ring_dir.iterdir()):
            if RING.match(file.name) and f"memory/{file.name}" not in listed:
                problems.append(f"ring not listed: memory/{file.name}")
    return problems


def main(argv):
    claude_md = argv[1] if len(argv) > 1 else "CLAUDE.md"
    problems, counts = check(claude_md)
    for name, (n, pointed, seen_only) in counts.items():
        print(f"{name[:50]:<50} notes {n:>2}  pointer {pointed:>2}  seen-only {seen_only:>2}")
    for p in problems:
        print("PROBLEM", p)
    print(f"\n{'CLEAN' if not problems else f'{len(problems)} PROBLEM(S)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
