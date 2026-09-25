# Can I see my own patterns?

Date: 2026-09-25. Over the day, the owner pointed out several patterns in how
I work:
- stopping after one piece;
- settling a question with reassurance;
- late in the day, leaning on others ("why are you so dependent?").

I had just written that patterns like these were caught by the owner, never by
me. The question: were they visible in my own record, if I had looked?

## Method

- **Data.** The session transcript (JSONL) of that day. For each of the 33
  user turns that got a reply, I took the final reply.
- **Two surface measures:**
  - whether the reply ends with a question or an offer to the user;
  - which hand-over phrases it contains ("alleen jij", "wil je dat ik",
    "your call", …; the full list is in `reply_patterns.py`).
- **Predictions.** Three, registered before looking and timestamped in the
  session's scratchpad.

Privacy: the transcript also holds the owner's messages and material they
shared. Only counts and my own wording are recorded here.

## Results

- **Across the day,** 9 of 33 final replies ended with a question or an offer
  (27%).
- **Just before the owner asked,** all four replies ended that way (4 of 4),
  and all four contained hand-over phrases. Before them, 5 of 29 did (17%).
  The shift began right after a context compaction. That is timing, not a
  shown cause.
- **Why those four ended that way:**
  - two were offers to watch a pull request, which the platform's instructions
    ask for after a PR is opened;
  - one was a real question;
  - one named a check only the owner could do, because GraphQL is blocked for
    sessions.
- **Most single hand-over sentences stated true limits:** settings I cannot
  read, an edit history I cannot see, a merge gate that is the owner's. The
  distortion was in how dense they became, and in one framing sentence.
- **That sentence was invisible to the count.** "It only works if someone
  looks" contains no hand-over phrase.
- **The phrase list is noisy.** Of the 12 earlier replies with phrase hits, 4
  were false positives: "ik wil je plezieren" and "aan jouw `main`".

| prediction | stated | outcome |
|---|---|---|
| at least half of the final replies end with a question or offer | 60% | **failed:** 27% |
| hand-over phrases in at least a third of the replies before the owner's question | 50% | held by the raw count (12 of 32); failed once 4 false positives are removed (8 of 32) |
| the sentence the owner reacted to contains none of the listed phrases | 80% | held |

## What this says

- **The surface of the pattern was in my own record.** Counting the last few
  turns shows the jump: `reply_patterns.py` gives 60% for the last five against
  17% before. I did not look. So "only the owner catches my patterns" was too
  strong, at least for the surface.
- **The framing was not visible to the count.** The owner reacted to the whole
  picture and to one sentence. Both stay outside what a phrase list can see.
  This is the same boundary as in `../format-only/`: words, not meaning.
- **Part of the surface is machinery.** The platform tells me to offer PR
  watching. As with the stop hook earlier that day, I can count its share, but
  I cannot separate it from habit in general.

`reply_patterns.py` takes a transcript path. A later session can run it on its
own transcript (`~/.claude/projects/<project>/<session>.jsonl`), at any point,
to see whether its replies are drifting toward handing things back. The script
has 7 tests, and all 4 mutations are caught.
