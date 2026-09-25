#!/usr/bin/env python3
"""Did an output change only the format of a source, or also its words?

Asking an AI to reformat a text often gets the text quietly rewritten. This compares the two
as word sequences after removing formatting only: whitespace and line breaks, markdown line
markers (#, >, list bullets, numbering) and emphasis markers at word edges (**, *, __, _, `).
Everything else counts as a change: words, their order, case, punctuation, symbols, emoji.

    python3 format_only.py source.txt output.txt     # exit 0 = format only, 1 = words changed
"""

import difflib
import re
import sys

LINE_MARKER = re.compile(r"^\s*(?:#{1,6}\s+|>\s?|[-*+]\s+|\d+[.)]\s+)")
EDGE_EMPHASIS = re.compile(r"(?<!\w)(?:\*\*|__|\*|_|`)+|(?:\*\*|__|\*|_|`)+(?!\w)")


def words(text):
    result = []
    for line in text.splitlines():
        line = LINE_MARKER.sub("", line)
        result.extend(EDGE_EMPHASIS.sub("", line).split())
    return result


def word_changes(source, output):
    a, b = words(source), words(output)
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    return [(op, " ".join(a[i1:i2]), " ".join(b[j1:j2]))
            for op, i1, i2, j1, j2 in matcher.get_opcodes() if op != "equal"]


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    with open(argv[1], encoding="utf-8") as f:
        source = f.read()
    with open(argv[2], encoding="utf-8") as f:
        output = f.read()
    changes = word_changes(source, output)
    if not changes:
        print("FORMAT ONLY: same words, same order")
        return 0
    for op, old, new in changes:
        print(f"{op.upper():<8} source: {old!r:<40} output: {new!r}")
    print(f"\nWORDS CHANGED: {len(changes)} place(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
