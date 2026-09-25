#!/usr/bin/env python3
"""Where do my replies hand things back to the user?

Reads a Claude Code session transcript (JSONL) and lists, per turn, whether the final reply
ends with a question or an offer to the user, and which hand-over phrases it contains
("alleen jij", "wil je dat ik", "your call", ...). It compares the last turns with the rest.

Surface only. It counts phrases; it cannot see framing. The sentence that made the owner ask
why I lean on others contained none of these phrases.

    python3 reply_patterns.py ~/.claude/projects/<project>/<session>.jsonl [last_n]
"""

import json
import re
import sys

HANDOVER = re.compile(
    r"alleen jij|jij beslist|beslis jij|jouw keuze|wil je dat ik|als je wilt|zeg het|laat me weten|"
    r"only you|the owner decides|your call|shall i|would you like|want me to",
    re.I,
)
OFFER = re.compile(r"\?|wil je|als je wilt|zeg het|laat me weten|shall i|would you like|want me to", re.I)
NOT_A_PROMPT = ("<system-reminder>", "<command-", "<local-command", "Caveat:", "This session is being continued")


def prompt_text(record):
    message = record.get("message") or {}
    if record.get("type") != "user" or message.get("role") != "user" or record.get("isMeta"):
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list) and content and all(part.get("type") == "text" for part in content):
        text = " ".join(part["text"] for part in content)
    else:
        return None  # tool results and mixed content are not new turns
    return None if text.startswith(NOT_A_PROMPT) else text


def turns(lines):
    """Yield (timestamp, final reply) for each user turn that got a reply."""
    current = None
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if prompt_text(record) is not None:
            if current and current[1]:
                yield current[0], current[1][-1]
            current = (record.get("timestamp", "")[:16], [])
        elif current and record.get("type") == "assistant":
            content = (record.get("message") or {}).get("content")
            if isinstance(content, list):
                current[1].extend(p["text"] for p in content if p.get("type") == "text" and p.get("text", "").strip())
    if current and current[1]:
        yield current[0], current[1][-1]


def measure(reply):
    lines = [line for line in reply.strip().splitlines() if line.strip()]
    ends_with_offer = bool(lines) and bool(OFFER.search(lines[-1]))
    return ends_with_offer, sorted({m.lower() for m in HANDOVER.findall(reply)})


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    last_n = int(argv[2]) if len(argv) > 2 else 5
    with open(argv[1], encoding="utf-8") as f:
        rows = [(ts, *measure(reply)) for ts, reply in turns(f)]
    for ts, offer, phrases in rows:
        print(f"{ts}  ends with offer: {'yes' if offer else 'no ':<3}  hand-over: {', '.join(phrases) or '-'}")
    if not rows:
        return 0
    recent, earlier = rows[-last_n:], rows[:-last_n] or rows
    share = lambda rs: sum(r[1] for r in rs) / len(rs)
    print(f"\nending with an offer: last {len(recent)}: {share(recent):.0%}, before that: {share(earlier):.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
