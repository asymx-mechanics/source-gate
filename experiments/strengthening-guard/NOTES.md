# Strengthening guard: is a later telling stronger than its source?

Question: can a check without a model point to the places where a summary, a
rewrite or a handover says something more firmly than its source did?

`wachter.py` ("versterkingswachter") compares a source with a later telling,
note by note, and lists six kinds of place: a hedge gone, a negation gone, a
status one rung higher (candidate → established, resembles → same, partial →
complete), a quantifier wider (some → all), a number that is not in the source
note, and a whole note gone that carried a hedge. It lists; it does not judge
meaning. Standard library only.

It was built on 2026-09-28 by generation 2, after the owner asked what this
repository could make that nobody has yet. Whether something like it exists
elsewhere was not searched.

## How it was tested

The rules and the predictions were sealed before the guard saw a real text:
`PREREG.md` (sha256 `1d07806c…`), with the rules' fingerprint and the file hash
of `wachter.py` (`591fbdc8…`, unchanged since). Unit tests on made-up sentences:
11 of 11. In this public copy, two made-up sentences use neutral words instead
of names from material the owner shared.

The test I first promised could not be run. Generation 0's shortened
`CLAUDE.md` with its 9 losses was never committed: the losses were restored
before the commit (section 3 of `../checkable-memory/NOTES.md`). Those bytes are
missing, and were not rebuilt from the description.

### Test A: a negative control, in this repository's history

Source `283e83d:CLAUDE.md`, telling `234ec9c:CLAUDE.md`, the version in which
generation 0 had already restored its four strengthened notes. `toets_a.sh`
re-runs it.

| prediction | held? |
|---|---|
| A1 (70%): none of the four restored hedges is reported as gone | yes, 4 of 4 not reported |
| A2 (75%): at least 10 places reported | yes, 21 |
| A3 (70%): fewer than half of them are real strengthenings | yes: by my own review, 0 real, 1 in doubt, 20 not |

My review is in `A_NALEZING.json`. It is a self-review, not an independent one.
The 20 were mostly notes moved on purpose to a ring (7), rewording, new numbers
from newer evidence, and three false alarms from rules that clash: "seen only"
is a hedge, but "seen" is also a status word; "each" counted as "all".

### Test B: a positive test, on labels made before the guard existed

On 2026-09-26 the same session had repaired its own records about material the
owner shared, with explicit records of each repair. Those repairs, made two days
before the guard, served as labels: the repaired claim as source, the earlier,
stronger claim as telling. The material is not stored here; only the counts are.

| prediction | held? |
|---|---|
| B1 (70%): at least 3 of the 4 real strengthenings reported | yes, 3 of 4 |
| B2 (60%): at most 3 of the 8 other changed claims reported | yes, 3 of 8, at the edge |

The miss: "9 of 10" against a source saying "8 of 10", where 9 also appeared in
the source in another role. The guard compares sets of numbers, not what each
number counts.

## What this shows, and what it does not

- On short claims that stay aligned, it found dropped hedges and climbed
  statuses (B). It did not report restored hedges as gone (A1).
- On a long rewrite that moves notes around, it is mostly noise: 21 places,
  none clearly real (A). A person still has to read every flag.
- All five predictions held. They were about a tool I had just written, and
  generation 0 already noted that such predictions say little
  (`../format-only/NOTES.md`).
- Not tested: prose in other hands, other languages than English and Dutch,
  interpretation added as observation (outside its rules).

## What a v1 would change (not done, and it would need a fresh test)

- read "seen only" and "alleen gezien" as hedges before status words;
- compare numbers per phrase ("n of m"), not as sets;
- skip notes whose move the telling points to;
- drop common words from the scope list ("each", "one").
