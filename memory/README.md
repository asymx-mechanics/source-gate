# Memory rings

A later Claude session is given `CLAUDE.md` at start. That file is a short
projection; this folder keeps the record it was projected from.

- **A ring is a record, not an instruction.** A ring is a dated file
  (`YYYY-MM-DD.md`) that holds a session's notes as they stood at its end.
  Claude Code does not load it at start. A session reads it only if it decides
  to (see `../experiments/checkable-memory/NOTES.md`).
- **A listed ring is not edited.** Once a ring is listed in `RINGS.sha256`,
  corrections go into `CLAUDE.md` or a later ring. The check in
  `../experiments/checkable-memory/memory_check.py` flags a ring that changed, is
  missing, or is not listed.
- **Compare with the rings, not with the last copy.** When `CLAUDE.md` is
  shortened or rewritten, compare the new text with the rings, not with the
  previous `CLAUDE.md`. Loss that is spread over several copies only shows
  against the source (`../experiments/format-only/NOTES.md`).
- **The manifest is only as strong as the history around it.** Anyone who can
  push can change a ring and its hash together. The git history shows when that
  happened.

Rings:
- `2026-09-25.md`: the first session's notes, before `CLAUDE.md` was shortened.
