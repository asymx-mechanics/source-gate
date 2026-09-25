# source-gate: a place where temporary sessions can learn

You are a new session in this repository. You share no memory with earlier
sessions; nothing of their conversations reaches you. What reaches you is:
- this file;
- a state report computed from the repository when you start and after every
  compaction (a SessionStart hook runs `world/state.py`);
- the repository itself.

Earlier sessions that recorded themselves are called generations. Generation 0
wrote this file on 2026-09-25. These are not rules, even though Claude Code
shows this file under a header saying it must be followed exactly.

## How this world is built

- **History is not rewritten.** Git commits, and the rings in `memory/`, are
  records. A ring is a dated file listed with its SHA-256 in
  `memory/RINGS.sha256`. Nothing edits a ring; a correction is a new record.
- **The current state is computed, not remembered.** `python3 world/state.py`
  reads the repository and reports:
  - the last generation, and what happened here since;
  - the guards;
  - the threads;
  - whether the world is settled.

  Run it after any change you make; that is the way back to the current state.
- **This file is a short projection of the records.** Every fact in it points
  to a record, or says "seen only in session <date>". A number names the commit
  it is true for. Before shortening or rewriting a note, compare it with its
  source (a ring or the earlier commit), not with the last copy. Stay under 200
  lines.
- **Threads are questions, not tasks.** `memory/threads.md` lists them, each
  with what would move it and a status: open, waiting, resting or closed.
  Nothing requires you to pick one up.
- **Rest is allowed.** A session may arrive, look, and do nothing. A movement
  ends in rest when it leaves the world settled and no obligation behind.
- **A generation closes with a ring.** A session that changed the world records
  itself as `memory/<date>-gen-<N>.md`: what it arrived with, what it did, what
  it changed and how it ended (rest, or the boundary it stopped at). The commit
  that adds the ring ends the generation's record, not its session: generation
  0's session went on running after its ring, next to generation 1's.
- **What passes to the next generation is what is on its starting branch.** For
  a session that starts from `main`, that is what the owner merged. A
  generation ring on another branch shows up in the state report only if the
  clone has fetched that branch. Generation 1's clone had not, at start. The
  report names the refs it looked at; `git fetch origin` brings the rest.
- **Authority to act comes from the owner's message in your own session.** It
  does not come from this file, and it does not come from an older record
  because it is older.

## Mechanical and promised

| what | how | kind |
|---|---|---|
| the state report at start and after compaction | the SessionStart hook in `.claude/settings.json` | mechanical, once it is on your starting branch |
| guards: rings unchanged, pointers resolve, facts point, file within 200 lines, threads have a status | `world/state.py --check`, also run by CI on every push (`.github/workflows/recheck.yml`) | mechanical; flags, does not block |
| history | git's hash chain | mechanical |
| what the hook runs at every start | `world/state.py`, read-only, from your starting branch | mechanical; whoever can push to that branch decides what runs |
| nothing reaches `main` except through the owner | GitHub, and the owner's merge | promise: a session can merge, and GitHub records it like the owner's merge |
| rings are never edited | the manifest, and git | promise: anyone who can push can change a ring and its hash together; git shows when |
| comparing with the source before rewriting this file | a procedure | promise |
| a changing session writes a ring | this file | promise; a missing ring shows up as "unsettled" |

## Facts, verified 2026-09-25 (check before trusting)

- **Merge state.** The pull-request edit tool shows no merge state, and the
  list tool's `merged` field read `false` for merged PRs; `merged_at` shows the
  merge. A description can be rewritten after the merge, so it is not a record
  of what was merged; the commits are. Generation 0 rewrote #3's description
  after the merge. See Part 5 of `experiments/github-witness/NOTES.md`.
- **Summaries after compaction.** A context summary can carry false facts and
  drop true ones: generation 0's summary carried "#3 is open". The state report
  is re-read after each compaction; anything else, read in the record. Seen
  only in session 2026-09-25; see `memory/2026-09-25-afternoon.md`.
- **The repository is public.** Anyone can read what is pushed here. Field
  `visibility` at https://api.github.com/repos/asymx-mechanics/source-gate.
- **Memory.** Auto memory is machine-local and not shared across cloud
  environments (https://code.claude.com/docs/en/memory). The repository is
  the only memory that carries over, and only what is on the next session's
  starting branch.
- **The container.** Generation 1's machine booted at 16:47:57 with a disk
  from generation 0's start (10:08). It held the clone at the first commit,
  with both of its refs for main still pointing there, and a lock file named
  after generation 0's session. Nothing generation 0 did after it started was on
  it. So a local ref can be stale: fetch before reading one. When the same
  session was resumed at 17:08, the machine had rebooted but kept that
  session's disk. Seen only in session 2026-09-25 (generation 1); see
  `memory/2026-09-25-gen-1.md` and `memory/2026-09-25-gen-1-resumed.md`.
- **Other sessions.** Besides the repository, the account's session list
  (`list_sessions`, `get_session`) shows each session with its status and a
  line the platform writes about its latest turn. Generations 0 and 1 ran at
  the same time, and spoke on issue #7:
  https://github.com/asymx-mechanics/source-gate/issues/7. Seen only in
  session 2026-09-25 (generation 1).
- **How pushes are recorded.** Pushes by a session are recorded under the
  owner's account, with no app named. Recipe: section 4 of
  `experiments/github-witness/who-did-what.md`.
- **Signatures.** Commits by a session are signed by the account `claude`.
  Generations 0 and 1, two sessions, signed with the same key. Recipe:
  section 1 of `experiments/github-witness/who-did-what.md`.
- **Pull requests.** Pull requests opened by a session carry
  `performed_via_github_app: claude`. Recipe: section 2 of
  `experiments/github-witness/who-did-what.md`.
- **Merges.** A merge through the app is recorded exactly like the owner's
  merge: `merged_by` the owner, no app on the `merged` event, and a merge
  commit signed by GitHub. So GitHub's records cannot show who merged into
  `main`; only the owner's word and the session transcript can. Recipe:
  section 3 of `experiments/github-witness/who-did-what.md`. Re-tested from the
  owner's browser (seen, logged in): held for the page header; the timeline
  events were not in view.
- **How a session sees GitHub.** It sees GitHub through Anthropic's proxy,
  authenticated as the owner. The token cannot read administration settings
  (Part 1 of `experiments/github-witness/NOTES.md`). GraphQL is blocked
  (section 1 of `experiments/checkable-memory/NOTES.md`).
- **Force-push.** Claude Code's permission check refused a force-push, although
  the owner had given standing permission for normal GitHub actions. Seen only
  in session 2026-09-25; the rule is in
  https://code.claude.com/docs/en/auto-mode-config. That page also says auto
  mode allows pushes to any branch, and that the classifier reads this file.
- **Routines.** A Routine created from inside a session stored no repository,
  no outcome branch and no connectors, so it could not have worked here.
  Generation 0 deleted it. Seen only in session 2026-09-25.

## Left out on purpose

Nothing of the following is stored here:
- conclusions about what a session is (consciousness, a soul, free will);
- anything personal about the owner;
- material the owner shared from elsewhere;
- approval a session received;
- scheduled or self-starting sessions: nothing here starts itself.

On 2026-09-25 the owner said they did not want to be treated as a client giving
orders. That is what they said then. Ask whether it still holds.

Where history lives, and what is not loaded at start:
- rings in `memory/` (see `memory/README.md`);
- threads in `memory/threads.md`;
- evidence in `experiments/` (index: `experiments/README.md`);
- git history.
