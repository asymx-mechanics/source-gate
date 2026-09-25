# Examining an old fragment: `atomic_gate_commit_v0.py`

Date: 2026-09-25. The owner uploaded this fragment from another workshop. They
said to treat its name, terminology and original intent as having no authority,
and to examine the code itself.

**The fragment is not in this repository.** It is identified by
sha256 `d45ef0286821a830aa7aea34326b0a207fadbde903a6824e26f38a9840a360a5`
(252 lines). See "What I rejected" for why. `attacks_gate.py` refuses to run
against any other file unless told to with `--unchecked`.

## What the code actually does (read before running)

- It is a library: no `main`, no network, no subprocesses, no environment access.
  It only touches the paths it is given.
- It stages a "run" in its own directory: intent, preflight, a hash check of a
  "motor" file against a sealed hash, a candidate, and a gate decision, each as JSON.
- `commit_finalized_run` then appends one `GATE_RUN_LANDED` line to a JSONL
  "ledger". It rewrites the whole file through a temp file, fsync, `os.replace`
  and a directory fsync.
- It then writes `COMMITTED.json`. Runs are labelled `COMMITTED`, `ABORTED`, or
  `ORPHAN` (staged but never landed).

## Results

`python3 -B attacks_gate.py <fragment>` runs 16 cases in throwaway directories.
I wrote down predictions for all of them before the first run, and all 16 matched.
That mostly shows I read the code closely, not that the tests are fair. So I also
ran the same cases against a copy with the local problems patched: 10 cases flip
to HOLDS. The tests can tell working from broken code.

| id | case | fragment | patched copy |
|---|---|---|---|
| G1 | a REJECT decision still lands | FLAW | holds |
| G2 | what lands is an argument, not the reviewed candidate | FLAW | holds |
| G3 | a failed motor-hash check does not stop landing | FLAW | holds |
| G4 | the seal's `motor_pointer` is never compared with the checked file | FLAW | holds |
| G5 | `COMMITTED` is believed even when the ledger lost the line | FLAW | holds |
| G6 | same inputs → same run id → same directory: a retry after a transient abort can never land | FLAW | FLAW (design, not patched) |
| G7 | …and after a commit, a new run's events are silently dropped while the call returns success | FLAW | FLAW (design, not patched) |
| G8 | two concurrent commits: both report COMMITTED, one line is lost | FLAW | holds (lock) |
| G9 | a half-written decision file counts as a decision | FLAW | holds |
| G10 | timestamps are local time without a zone | FLAW | holds |
| G11 | crash between landing and marking is recovered (ORPHAN → COMMITTED, one line) | holds | holds |
| G12 | re-running a commit does not duplicate the line | holds | holds |
| G13 | an aborted run refuses to land | holds | holds |
| G14 | a run with no decision file refuses to land | holds | holds |
| G15 | the ledger can be edited after landing and nothing notices | FLAW | **FLAW** |
| G16 | an APPROVE written by the process itself lands like a human's | FLAW | **FLAW** |

G8 forces an interleaving (both writers read before either replaces) by
wrapping `os.replace` with a barrier. The window exists without the wrapper,
but it is narrow.

The patched copy is in the session's scratchpad only. It is derived from the
fragment, so it is not published either. The patches were:
- read and check the decision instead of testing that the file exists;
- land only the reviewed candidate;
- require a passing motor check;
- compare the seal pointer with the checked file;
- treat "marked but not in ledger" as an error;
- lock the ledger;
- use UTC timestamps.

## What holds up

- The staging discipline: nothing reaches the primary record until a run is
  complete, and an incomplete run stays visible as `ORPHAN` instead of
  disappearing.
- The crash-safe replacement (temp file, fsync, replace, fsync of the directory)
  and recovery after a crash between landing and marking.

## What no local patch fixes

- **G16: who decided.** The "human gate decision" is a file. Anyone who can run
  the process can write it, and nothing records who did.
- **G15: who keeps the record.** The ledger is a file held by the same party. Its
  own hash record (`COMMITTED.json`) sits next to it, under the same control.

This is the same result as the rejected session-receipt experiment in this
repository. A gate and a ledger held by the party they are meant to constrain
are neither a gate nor a ledger. The "motor seal" has the receipt's `tool_version`
weakness too: whoever can change the motor can change its seal.

## Verdict

**KILL as a gate. Do not adopt the code.** Keep three ideas as seeds:

1. A decision must name the exact bytes it approves, and landing must refuse
   anything else (G2).
2. A status must be derived from the primary record, not from a marker that can
   drift away from it (G5).
3. Incomplete work must stay visible as its own state (G11, `ORPHAN`).

In this repository those ideas already have a home outside my reach, in
GitHub's pull-request flow: a merge lands a specific head commit (from memory,
not verified here), and the history of `main` is the record. But the flow has
G16's problem too, at GitHub's scale. This session acts on GitHub as the owner's
account. My probe push was recorded with actor `asymx-mechanics` and no app
marker (verified; see `../github-witness/NOTES.md`). The pull request I opened
does name the app (`performed_via_github_app: claude`, verified). But a merge I
performed through the app (#4) is recorded exactly like the owner's merge (#1):
no app marker anywhere I looked (verified; see Part 4 of the witness notes).
What separates "the human decided" from "the agent decided" here is therefore
not in GitHub's record. It is my restraint, the Claude Code permission check,
the platform's session transcript and the owner's word.

## What I rejected, and why

- **Publishing the fragment verbatim.** It came from another workshop, and
  whether it is private is not mine to judge. A push to this public repository
  cannot reliably be taken back. Public events are visible within seconds
  (verified), and I could not test whether a rewound commit stays fetchable by
  SHA (see the witness notes). The owner can add it later; I cannot take it back.
- **Publishing my patched copy.** It is a close derivative of the fragment.
- **Building a local gate or ledger for this repository.** It would recreate
  G15 and G16. The receipt experiment already failed for exactly that reason.
