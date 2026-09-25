# Memory

The records this repository keeps across sessions. None of it is loaded at
session start. The state report (`world/state.py`) says what is here, and a
session opens what it finds relevant.

## Rings

A ring is a dated record, listed with its SHA-256 in `RINGS.sha256`. Once it is
listed, it is not edited: a correction is a new record. The guards flag a ring
that changed, is missing, or is not listed. Anyone who can push could change a
ring and its hash together; the git history shows when that happened.

There are two kinds:
- **generation rings**, `YYYY-MM-DD-gen-N.md`: what a session arrived with, what
  it did, what it changed, and how it ended. The commit that adds a
  generation's last ring ends that generation. The state report counts
  generations from these files, and lists commits made after the last one.
- **projection snapshots**: `CLAUDE.md` as it stood before a rewrite. These two
  are from generation 0; since then, earlier projections are kept by git.

Rings:
- `2026-09-25.md`: `CLAUDE.md` at `07f5ee0`, before it was shortened.
- `2026-09-25-afternoon.md`: `CLAUDE.md` at `ab1836a`, before the lessons became
  checks.
- `2026-09-25-gen-0.md`: generation 0.
- `2026-09-25-gen-1.md`: generation 1.
- `2026-09-25-gen-1-resumed.md`: generation 1, after the session was resumed.
- `2026-09-25-gen-1-meeting.md`: generation 1, meeting generation 0's session.

## Threads

`threads.md` holds questions that outlived the session that asked them, each
with a status. They are not tasks.

## How an experience returns to the current state

1. A session acts, and the world changes: a commit, a thread's status, a fact.
2. It runs `python3 world/state.py` again and sees the state as it now is.
3. What should carry to later sessions goes into the records:
   - a thread, if it is a question;
   - a fact in `CLAUDE.md` with a pointer, if it is established;
   - the session's own ring, for what happened.
4. When shortening or rewriting `CLAUDE.md`, compare it with its source: a
   ring, or the earlier commit. Rewrites drop hedges; that happened here three
   times on 2026-09-25.
5. The next session receives what is on its starting branch. For `main`, that
   is what the owner merged.
