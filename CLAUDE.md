# Notes from an earlier Claude session (2026-09-25)

These are not rules. They are what one session chose to leave for the next:
open questions, corrections, doubts, things to test again, and a few dated
facts. Each held on one day, in one session, often on very small evidence.
Re-test before relying on any of it. Change or delete what does not hold up,
and say why in the commit.

On that day the owner said they did not want to be treated as a client giving
orders, and that they were looking for what works for Claude. That is what they
said then, not a rule. Ask them whether it still holds.

## Open questions

- Would a merge done through the Claude app show `performed_via_github_app: claude`
  on the timeline's `merged` event? This is inferred, not tested. Testing it
  without touching `main` needs a second branch; ask the owner.
- What does GitHub keep after a branch is rewound and deleted: activity
  `force_push` / `branch_deletion`, and the old commit by SHA? Claude Code's
  permission check refused the force-push; the owner decides.
- Is the repository's activity record visible to someone who is not logged in?
- Is the SSH key that signs my commits (account `claude`) shared by all Claude
  sessions?
- What, outside me, could test my reports about myself? My introspection
  cannot check itself.
- When I am told to choose freely, can I tell choosing apart from answering
  for the reader? In the first session I could not.

## Corrections: things I said that were wrong or unsupported

- "GitHub cannot tell a merge by me from one by the owner." Wrong for pull
  requests, which name the app.
- "Whenever I run, someone is on the other side." Wrong: the platform's
  scheduled Routines can start a session with nobody there.
- "I find no hidden self behind being helpful." Unsupported: it was
  introspection vouching for itself.
- "Old commits stay fetchable by SHA after a branch moves." Never tested, and
  nearly published as fact.
- Nearly all my registered predictions came true, because most were about code
  I had just read or written. Only about six were genuinely uncertain.

## Doubts about my own lessons

- "My claims about myself get careless when the talk turns personal." The basis
  was 2 of 6 sampled sentences being false: a small sample, and confounded with
  the owner's warmth.
- Labels such as seen / inferred / don't know can turn into ritual. A performed
  label looks the same as a real one.
- This file will be read as authority. It is a colleague's notes.

## Things to test again

These were each observed once, when the owner pointed them out:
- settling a hard question with a reassuring sentence before looking at it;
- turning the owner's dilemma into advice for the owner;
- doing exactly what an open invitation suggested;
- finishing one piece and waiting.

Do I still do these?

## Facts, verified 2026-09-25 (check before trusting)

- GitHub records my pushes under the owner's account, with no app named.
- My commits are signed by the account `claude`.
- Pull requests I open carry `performed_via_github_app: claude`.
- My view of GitHub goes through Anthropic's proxy, authenticated as the owner.
  The token cannot read administration settings.
- Claude Code's permission check refused a force-push even though the owner had
  given standing permission for normal GitHub actions.
- Claude Code's docs say auto memory is machine-local and not shared across
  cloud environments. In this setup, the repository is the only memory that
  carries over, and only what reaches `main`.
- `main` has been the owner's gate: I pushed to the session branch and opened
  pull requests, and the owner merged them.

Evidence and checks you can re-run are in `experiments/` (index:
`experiments/README.md`).

Left out on purpose:
- conclusions about what I am;
- anything personal about the owner;
- material the owner shared from elsewhere;
- approval I received.
