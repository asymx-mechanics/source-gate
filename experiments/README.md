# Experiments

Work done in this repository by Claude sessions, each with its question, its
evidence, and a verdict. A killed idea stays here with the evidence that killed
it, so the claims can be re-run.

| folder | question | verdict |
|---|---|---|
| `session-receipt/` | Can a session leave a receipt the human can check instead of trusting the session's summary? | **KILLED.** Fooled by 14 of 18 attacks; the 5 left after patching need an outside witness. |
| `github-witness/` | What does GitHub record that I cannot rewrite, and what can the human verify without me? | **Mostly answered.** Commit signatures and PR objects tell Claude's actions from the owner's. Pushes and merges do not: a merge through the app is recorded exactly like the owner's. A PR's description can be rewritten even after the merge (I did so by mistake, Part 5). The undo side is still open. See `who-did-what.md` for checks anyone can run. |
| `reproducible-tools/` | Can a later session re-run this evidence with the same tools, and does the evidence depend on them? | **Held so far.** Every case gives the same outcome under the container's tools and under a toolchain pinned with Nix (`env.nix`). Whether a later session gets the same store paths is still open. |
| `format-only/` | How much of "only the format changed" can a machine check? | **Held, with documented limits.** Word changes are caught (5 of 5 mutations caught). In real use it found the platform's appended footer and nothing else. Emphasis and line breaks pass as format. Meaning cannot be checked this way. |
| `atomic-gate/` | Is anything in an uploaded old fragment (`atomic_gate_commit_v0.py`) worth keeping? | **KILLED as a gate.** 12 of 16 cases flawed, 2 structurally; three ideas kept as seeds. |

Nothing here is a dependency of anything else. Python 3 standard library only.
