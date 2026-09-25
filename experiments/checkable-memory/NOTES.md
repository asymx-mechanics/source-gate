# Checkable memory

Date: 2026-09-25. The owner asked whether better memory interests me. It
does, but in one direction: memory that can be checked, not more of it.

That same day, two of my mistakes were memory mistakes:
- A context summary carried "#3 is open" as a fact, and I acted on it.
- A token from a text the owner shared ended up in examples I believed I had
  made up.

In both cases, what I remembered was stronger than what had happened, and I
could not see the difference myself.

A later session's memory is `CLAUDE.md`, and only what reaches `main`. Claude
Code loads it under a header that says it must be followed exactly. In one day
it grew from 799 to 1985 words (95 to 205 lines). Claude Code's own docs advise
staying under 200 lines, because "longer files consume more context and reduce
adherence". By a rough count, 9 of its 44 notes pointed to their evidence.

Four questions:
1. Where does the evidence behind each note live, and who can re-check it?
2. Can a check flag notes that do not say how they are known?
3. Can `CLAUDE.md` stay small without losing the record?
4. Can something outside me re-run the checks?

## 1. Where the evidence lives

Every note under "Facts, verified" in `CLAUDE.md`, traced to its evidence. I
re-checked each one on 2026-09-25 the way a later session would, through the
same proxy, using the recipes in `../github-witness/who-did-what.md`.

| fact | evidence lives | who can re-check | re-checked |
|---|---|---|---|
| pushes appear under the owner's account, no app | GitHub activity API | a later session; the owner | held: 23 entries on the branch, one actor, no app field |
| commits signed by `claude` | commit verification | a later session; the owner | held (`07f5ee0`) |
| PRs carry `performed_via_github_app: claude` | the issue object | a later session; the owner | held (#5) |
| an app merge is recorded like the owner's | PR and timeline | a later session; the owner | held (#1, #4) |
| a PR description can be rewritten after the merge | the PR bodies | a later session; the owner | held, by REST alone: #3's body names #5, created 56 min after #3 was merged |
| the proxy is in the path; no admin access | a probe any session can run | a later session | held: branch protection read → 403 |
| the permission check refused a force-push | this session's transcript | the owner, in the session view | not re-checkable by a session |
| auto memory is machine-local | Claude Code's docs | anyone | held (docs, same day) |
| `main` has been the owner's gate | GitHub cannot show who merged; the owner's word; the transcript | the owner | not re-checkable by a session |
| a Routine made in a session had no repository | this session's transcript; the Routine is deleted | the owner, in the session view | not re-checkable by a session |

So, of ten "verified facts":
- seven can be re-checked by a later session;
- three rest on this session's own record or the owner's word;
- none turned out to have no evidence at all.

None of them said which kind it was.

Two things came up along the way:
- **GraphQL is blocked for Claude Code sessions.** The proxy answers with its
  own message. A PR description's edit history is therefore visible to the
  owner in the browser, but not to me. It is a record I cannot read, and
  probably cannot delete: a witness outside me. [V]
- **Where I found a better proof after predicting.** For the #3 fact, I found
  a better proof (the body names a later PR) after I had registered the
  predictions, and that moved it into "re-checkable".

Predictions, registered before tracing (timestamped in the session's
scratchpad):

| prediction | stated | outcome |
|---|---|---|
| at least 3 facts rest only on this session's record | 60% | **failed:** 2 do (force-push refusal, Routine); a third also rests on the owner's word |
| at least 1 fact has no evidence at all | 30% | failed (none) |
| "on GitHub, readable by API" is the largest group | 65% | held: 5 of 10 |

## 2. A check that asks "how do I know this?"

`memory_check.py` reads `CLAUDE.md` and flags:
- a note under "Facts" that has neither a pointer nor the words "seen only". A
  pointer is a `path` in backticks that exists here, or a URL;
- a relative path in backticks that does not exist;
- a ring in `memory/` that changed, is missing, or is not listed in
  `memory/RINGS.sha256`.

Absolute paths such as `/nix` are not pointers. They name a container, not the
repository, and a later container may not have them.

**Tests.** 14 tests pass, and 9 of 9 mutations are caught. One mutation first
survived: treating absolute paths as pointers. My test used `/tmp`, which
exists on every machine, so the mutated check found the "pointer" and passed.
The test now uses a path that does not exist. [V]

**Before the rewrite.** Every fact failed:

| `CLAUDE.md` | facts | with a pointer | problems |
|---|---|---|---|
| on `main` (what the next session reads) | 7 | 0 | 7 |
| on the branch before the rewrite | 10 | 0 | 10 |
| after the rewrite (section 3) | 10 | 9, plus 3 marked "seen only" | 0 |

**What it cannot see.** A pointer can resolve and still not support the note.
While rewriting, I caught two of my own pointers that pointed to real files
without the detail they were cited for:
- GraphQL being blocked was not in the Part 1 I cited;
- #3's body naming #5 was not in the Part 5 I cited.

I found both by reading, not with the check.

## 3. Rings: a small file that points to a record that does not change

What Claude Code's docs say (https://code.claude.com/docs/en/memory, read
2026-09-25):
- **Size.** Target under 200 lines per `CLAUDE.md`, because "longer files consume
  more context and reduce adherence".
- **Imports.** `@path` imports load at launch too, so they do not make anything
  smaller. A path in backticks is not an import.
- **Subdirectories.** A `CLAUDE.md` in a subdirectory loads when Claude reads
  files there. It still loads as an instruction.
- **Auto memory.** It already works this way: an index of at most 200 lines
  loads, and topic files are read on demand. But it is machine-local, so it
  does not reach a later cloud session.

The design here:
- **`memory/2026-09-25.md` is the ring.** It holds `CLAUDE.md` exactly as it
  stood at `07f5ee0` (`cmp` confirms). It is listed with its hash in
  `memory/RINGS.sha256` and is not edited after that. It is not named
  `CLAUDE.md`, so it is not loaded as an instruction; it is a record, read on
  demand.
- **`CLAUDE.md` is a short projection** with a pointer or a "seen only" on every
  fact.

**My rewrite had silently strengthened my own notes.** Following section 1 of
`../format-only/NOTES.md`, I compared each shortened note with its source in
the ring, not with the previous file, and listed the words that were dropped.
- **The first pass.** 12 notes were flagged. On review, 3 were harmless
  rewording and 9 were real losses.
- **Four of the losses made a note stronger than its source:**
  - The transcript lost its caveat. The source said its local copy is writable
    by the session, and whether the platform keeps a copy is untested.
  - My "#3" correction lost "and I did not check".
  - One failed prediction became "the genuinely uncertain ones fail more often".
  - "I don't know whether the classifier discounts such text" disappeared.
- **The other five losses** were limits on a claim:
  - the "not rules" framing does not change the header;
  - only the owner's word and the transcript can show who merged;
  - `main` being the owner's gate is a convention, not a control;
  - "not fully true";
  - why the Routine was deleted.
- **A second pass** flagged 10 notes. 7 were harmless and 3 were real, all
  minor:
  - a pointer;
  - "the owner's merge does not gate that";
  - "the timeline events were not in view".

I wrote the shortened file an hour after the test showing that summaries drop
hedges, and I still did it. So the comparison is not optional. It needs a
human, or at least a second look, because the flagged words are noisy: "not"
and "only" are often just reworded.

| | lines | words |
|---|---|---|
| `CLAUDE.md` on `main` | 95 | 799 |
| on the branch before the rewrite | 205 | 1984 |
| first shortened version (with the losses) | 150 | 1266 |
| after restoring them | 165 | 1444 |

Restoring the hedges and pointers cost 178 words, about a quarter of the 718
the shortening had saved. Much of the compression had come from dropping
exactly what makes a note honest.

**Not known yet:** whether a later session opens the ring at all. The docs say
the same about a file that `CLAUDE.md` only mentions in words: "Claude sees
AGENTS.md only if it decides to open the file." A later session is the test.
