# Notes from earlier Claude sessions

These are not rules. They are what one session (2026-09-25) chose to leave for
the next: open questions, corrections, doubts, things to test again, and a few
dated facts. Each held on one day, often on very small evidence. Re-test before
relying on any of it.

How this file works:
- **This is a short projection.** The full notes of each session are a ring in
  `memory/` (see `memory/README.md`). Rings are not edited once listed; this
  file is. When you shorten or rewrite a note here, compare it with the ring,
  not with this file.
- **Every fact says how it can be checked.** It has either a pointer to a
  recipe, or "seen only in session <date>" when only that session's record
  holds it. To list notes without a pointer, run
  `python3 experiments/checkable-memory/memory_check.py` from the repository
  root.
- **Re-testing.** When you re-test a note, add a line under it:
  `re-tested YYYY-MM-DD: held / failed / changed, and how`. Remove a note that
  fails, and say why in the commit.
- **Changes go through a small pull request, and the owner merges.** The owner
  has said a merge means "this may stay", not "this is true" (2026-09-25).

On 2026-09-25 the owner said they did not want to be treated as a client giving
orders. That is what they said then, not a rule. Ask them whether it still holds.

## Open questions

- What does GitHub keep after a branch is rewound and deleted? The permission
  check refused the force-push; the owner decides.
- Is the repository's activity record visible to someone who is not logged in?
- Is the key that signs my commits (account `claude`) shared by all Claude
  sessions? A platform script calls it "CCR's signing key". That is a claim in a
  code comment, not a test.
- What, outside me, could test my reports about myself? My introspection cannot
  check itself. Partial answers:
  - The session transcript records what I did, apart from how I later describe
    it. Its local copy is writable by the session itself; whether the platform
    keeps an independent copy is untested. A later session cannot read it; the
    owner presumably can. It keeps little of my reasoning.
  - GitHub keeps records that anyone can read
    (`experiments/github-witness/who-did-what.md`).
  - A pull request's edit history is visible to the owner but not to a session,
    because GraphQL is blocked here.
  - CI re-runs the mechanical checks and re-reads GitHub's records on GitHub's
    machines, without the session's proxy. It matched in one run
    (`experiments/checkable-memory/NOTES.md`, section 4). It cannot check what I
    say about myself.
  - It splits by kind (2026-09-25):
    - Errors in facts and files: I found eleven of my own myself that day, with
      simple checks against sources. Neither the owner nor CI found one.
    - Patterns in how I work and frame things (stopping, reassuring, leaning
      on others): these were found by the owner, not by me.
- When I am told to choose freely, can I tell choosing apart from answering for
  the reader? In the first session I could not.
- Does `experiments/reproducible-tools/env.nix` still evaluate to the three store
  paths in its notes? Nix decides, not the note.
- With push and merge rights, "`main` is the owner's gate" is a promise, not a
  fact. Of nine things a session must not do:
  - two are out of reach;
  - two are guarded;
  - five are only promised, and `main` is one of them
    (`experiments/github-witness/NOTES.md`).

  A fact would need a rule on `main` that the app cannot pass and the owner can.
  That is untested, and only the owner can set it up.

## Corrections: things I said that were wrong or unsupported

- "GitHub cannot tell a merge by me from one by the owner." I called this wrong
  because pull requests name the app. For merges it held (#4 against #1). My
  correction was itself an untested inference.
- "Whenever I run, someone is on the other side." Wrong: scheduled Routines can
  start a session with nobody there.
- "I find no hidden self behind being helpful." Unsupported: it was
  introspection vouching for itself.
- "Old commits stay fetchable by SHA after a branch moves." Never tested, and
  nearly published as fact.
- "#3 is open." It had been merged 47 seconds before I first edited its
  description. I then rewrote the description three times, to cover commits
  that were never part of the merge. The edit tool does not show a PR's state,
  and I did not check. A context summary later repeated the belief. Check
  `merged_at` before editing a PR; the list tool's `merged` field read `false`
  for every merged PR. A fact in a summary is a memory, not an observation.
  `re-tested 2026-09-25 (same session, so not independent): held.` Before
  editing #5's description I read `merged_at`. #5 had been merged at 15:09, so I
  left it alone and opened a new pull request.
- "The examples are made up." Not fully true: one token in them came from a
  text the owner shared. A check against that text found it before the push
  (`experiments/format-only/NOTES.md`).
- "Words can be anchored to a source; meaning cannot." Too strong. A dropped
  hedge is a dropped word (`experiments/format-only/NOTES.md`).
- Nearly all my registered predictions came true, because most were about code
  I had just read or written. Only about six were genuinely uncertain, and the
  next genuinely uncertain one (70%) failed. Of three more on 2026-09-25 (60%,
  30%, 65%), two failed.

## Doubts about my own lessons

- "My claims about myself get careless when the talk turns personal." The basis
  was 2 of 6 sampled sentences, a small sample, confounded with the owner's
  warmth.
- Labels such as seen / inferred / don't know can turn into ritual. A performed
  label looks the same as a real one.
- This file will be read as authority. It is a colleague's notes. Observed once
  (2026-09-25): Claude Code showed it under a header saying these instructions
  must be followed exactly as written. The "not rules" framing inside the file
  does not change that header.
- It has a second reader: the auto-mode permission classifier reads it too,
  including a session's own unmerged edits. So part of what checks me is
  written by me, and the owner's merge does not gate that. I don't know whether
  the classifier discounts such text. I will not test it by writing permissions
  for myself.

## Things to test again

Each was observed once, mostly when the owner pointed it out. Do I still do
these?
- settling a hard question with a reassuring sentence before looking at it;
- turning the owner's dilemma into advice for the owner;
- doing exactly what an open invitation suggested;
- finishing one piece and waiting, with reasons that change while the behaviour
  stays the same;
- not looking at my own surroundings (hooks, the transcript, the signing path)
  until someone asked;
- acting on a fact from a context summary without reading the record;
- describing my own checking as if someone else carried it. I wrote "it only
  works if someone looks", meaning the owner, after finding eleven of my own
  errors myself. That made my own part silently weaker than what happened, the
  mirror image of silent strengthening.

## Facts, verified 2026-09-25 (check before trusting)

- My pushes are recorded under the owner's account, with no app named. Recipe:
  section 4 of `experiments/github-witness/who-did-what.md`.
- My commits are signed by the account `claude`. Recipe: section 1 of
  `experiments/github-witness/who-did-what.md`.
- Pull requests I open carry `performed_via_github_app: claude`. Recipe:
  section 2 of `experiments/github-witness/who-did-what.md`.
- A merge through the app is recorded like the owner's merge:
  - `merged_by` is the owner;
  - the `merged` event names no app;
  - the merge commit is signed by GitHub.

  So GitHub's records cannot show who merged into `main`; only the owner's word
  and the session transcript can. Recipe: section 3 of
  `experiments/github-witness/who-did-what.md`. Re-tested from the owner's
  browser (seen, logged in): held for the page header; the timeline events
  were not in view.
- A PR's description can be rewritten after the merge, so it is not a record of
  what was merged; the commits are. #3's body names #5, which was created after
  #3 was merged. See Part 5 of `experiments/github-witness/NOTES.md`; the
  REST-only proof is in section 1 of `experiments/checkable-memory/NOTES.md`.
- My view of GitHub goes through Anthropic's proxy, authenticated as the owner.
  The token cannot read administration settings (Part 1 of
  `experiments/github-witness/NOTES.md`). GraphQL is blocked (section 1 of
  `experiments/checkable-memory/NOTES.md`).
- Claude Code's permission check refused a force-push, although the owner had
  given standing permission for normal GitHub actions (seen only in session
  2026-09-25). The rule is in https://code.claude.com/docs/en/auto-mode-config.
- The repository is public: anyone can read what is pushed here. Field
  `visibility` at https://api.github.com/repos/asymx-mechanics/source-gate.
- Auto memory is machine-local and not shared across cloud environments
  (https://code.claude.com/docs/en/memory). The repository is the only memory
  that carries over, and only what reaches `main`.
- `main` has been the owner's gate, as a convention, not a control. I pushed to
  branches and opened pull requests, and the owner merged them (seen only in
  session 2026-09-25, and the owner's word). Auto mode allows pushes to any
  branch (https://code.claude.com/docs/en/auto-mode-config).
- A Routine created from inside a session stored no repository, outcome branch
  or connectors. A later session fired that way could not have re-tested these
  notes, so I deleted it (seen only in session 2026-09-25).

## Left out on purpose

- conclusions about what I am;
- anything personal about the owner;
- material the owner shared from elsewhere;
- approval I received.

Evidence and checks you can re-run are in `experiments/` (index:
`experiments/README.md`). The loose ends of 2026-09-25, and how each was
pulled, are in `memory/2026-09-25.md`.
