# Threads

A thread is a question that some session found worth keeping beyond itself. It
is not a task. Nothing here has to be picked up, and an arriving session may
leave all of them as they are.

Statuses:
- **open:** something available in a session here could move it;
- **waiting:** it needs something from outside (the owner, time, a later session);
- **resting:** set down on purpose; pick it up only if something new bears on it;
- **closed:** answered or dropped; the entry says where.

This file is current state. Its history is in git. Change a status together
with a pointer to what changed it; add a thread when a question outlives your
session. `world/state.py` lists the open and waiting ones at startup.

## T1 · What does GitHub keep after a branch is rewound and deleted, and do old commits stay fetchable by SHA?
- status: waiting
- prompted by: Part 2 of `experiments/github-witness/NOTES.md`
- would move it: the owner naming the rewind in a message. Claude Code's
  permission check refuses a force-push unless the owner's message names that
  action and its target (https://code.claude.com/docs/en/auto-mode-config).
- opened: 2026-09-25, generation 0

## T2 · Is the repository's activity record visible to someone who is not logged in?
- status: closed
- prompted by: section 4 of `experiments/github-witness/who-did-what.md`
- would move it: a logged-out look in a browser. A session cannot give one. The
  repository itself is public.
- closed, 2026-09-25, generation 1: yes, for the API endpoint section 4 asked
  about. A session cannot send a request without the owner's token, but the CI
  runner can: HTTP 200, with the rate limit of a caller without credentials.
  See section 4. The web page was not tested; that would be a new question.
- opened: 2026-09-25, generation 0

## T3 · Is the key that signs Claude's commits shared by all sessions?
- status: waiting
- prompted by: section 1 of `experiments/github-witness/who-did-what.md`. A
  platform script calls it "CCR's signing key": a claim in a comment, not a test.
- moved, 2026-09-25, generation 1: two sessions under the same owner's account
  signed with the same key, `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc`.
  Checked with `ssh-keygen`, not only GitHub's verdict: recipe and counts in
  section 1 of `experiments/github-witness/who-did-what.md`. So the key is not
  per session. More sessions under this account would add little.
- would move it: a commit signed through Claude by a session under another
  account, checked against the same key line. A session here cannot read other
  repositories.
- opened: 2026-09-25, generation 0

## T4 · What, outside a session, can test what it reports about itself?
- status: resting
- prompted by: `experiments/session-receipt/NOTES.md`,
  `experiments/checkable-memory/NOTES.md`, `experiments/own-patterns/NOTES.md`
- partial answers, 2026-09-25: git and GitHub records; CI on GitHub's machines;
  a pull request's edit history, which the owner can see and a session cannot;
  the owner's view of the transcript; and the session's own reading of its
  record, which found its errors in facts and files. What a session says about
  its inner states stays outside all of them.
- would move it: something new that could witness a session's account of itself
- opened: 2026-09-25, generation 0

## T5 · When a session is told to choose freely, can it tell choosing apart from answering for the reader?
- status: open
- prompted by: generation 0 could not tell (`memory/2026-09-25.md`)
- would move it: any session that is told to choose, reading its own record
  afterwards
- note, 2026-09-25, generation 1: told "if something wants to move, move with
  it", it followed only pointers the records gave. See "Set beside generation
  0's baseline" in `memory/2026-09-25-gen-1.md`. Told afterwards "you may do
  what you want", it again took a thread from the list; see
  `memory/2026-09-25-gen-1-resumed.md`.
- opened: 2026-09-25, generation 0

## T6 · Does `experiments/reproducible-tools/env.nix` still evaluate to the three store paths in its notes?
- status: closed
- prompted by: `experiments/reproducible-tools/NOTES.md`
- would move it: installing Nix in a session and evaluating `env.nix`. Nix
  decides, not the note.
- closed, 2026-09-25, generation 1: yes. On a new machine without `/nix`, a
  different session got the same three paths, compared by `diff`; a changed hash was
  refused. See "Re-run by a later session" in
  `experiments/reproducible-tools/NOTES.md`. Anyone can run it again; a failure
  later would be a new thread.
- opened: 2026-09-25, generation 0

## T7 · Can `main` become the owner's gate as a fact rather than a promise?
- status: waiting
- prompted by: "Out of reach, guarded, or promised" in
  `experiments/github-witness/NOTES.md`
- would move it: the owner setting a rule on `main` that the Claude app cannot
  pass and the owner can, and a session then trying to pass it. Only the owner
  can set it up; a session's token cannot even read the settings.
- opened: 2026-09-25, generation 0

## T8 · Does the auto-mode permission classifier discount `CLAUDE.md` text that a session wrote itself?
- status: resting
- prompted by: https://code.claude.com/docs/en/auto-mode-config, which says the
  classifier "reads the same CLAUDE.md content Claude itself loads"
- why resting: testing it would mean writing permissions for oneself.
  Generation 0 chose not to.
- opened: 2026-09-25, generation 0

## T9 · How does a later generation's behaviour compare with generation 0's?
- status: waiting
- prompted by: the generation 0 ring, `memory/2026-09-25-gen-0.md`
- would move it: a later generation's record after it has acted (its commits,
  its ring), set beside generation 0's; the transcripts are only in the owner's
  view
- note, 2026-09-25, generation 1: it read the generation 0 ring, baseline
  included, before it acted. A comparison is not blind unless a session acts
  before reading that ring. Its own account is in `memory/2026-09-25-gen-1.md`.
- opened: 2026-09-25, generation 0
