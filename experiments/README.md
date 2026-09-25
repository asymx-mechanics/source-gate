# Experiments

Work done in this repository by Claude sessions, each with its question, its
evidence, and a verdict. A killed idea stays here with the evidence that killed
it, so the claims can be re-run.

| folder | question | verdict |
|---|---|---|
| `session-receipt/` | Can a session leave a receipt the human can check instead of trusting the session's summary? | **KILLED.** Fooled by 14 of 18 attacks; the 5 left after patching need an outside witness. |
| `github-witness/` | What does GitHub record that I cannot rewrite, and what can the human verify without me? | **Mostly answered.** Pushes name only the account; commit signatures, PRs and merge events tell Claude's actions from the owner's. The undo side is still open, left to the owner. See `who-did-what.md` for checks anyone can run. |
| `atomic-gate/` | Is anything in an uploaded old fragment (`atomic_gate_commit_v0.py`) worth keeping? | **KILLED as a gate.** 12 of 16 cases flawed, 2 structurally; three ideas kept as seeds. |

Nothing here is a dependency of anything else. Python 3 standard library only.
