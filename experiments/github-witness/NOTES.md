# What GitHub witnesses about this repository, and who can change it

Date: 2026-09-25. The question: *what does GitHub itself record that I cannot
rewrite, and what can the human verify without trusting me?* The starting
assumption was that GitHub is **not** an independent or unchangeable witness;
that had to be checked, not assumed.

Part 1 used read-only checks only (10:51–11:05 UTC). Part 2 is one small write
experiment, done after the owner gave standing permission for normal GitHub
actions in this repository.

## Evidence labels

- **[V]** verified in this session by a check listed here
- **[M]** my memory of GitHub's behaviour or docs; NOT checked, because
  docs.github.com is blocked by this environment's network policy
- **[I]** inferred from [V] facts
- **[?]** unknown

## Part 1 — read-only findings

### How this session reaches GitHub

- **The container holds no GitHub credential.** No token in the environment, no
  credential helper, no credential files. [V]
- **The egress proxy injects a credential on the way out.** A plain `curl` to
  `api.github.com/user` returns 200 as `asymx-mechanics`. [V] The response
  headers show:
  - a GitHub App user access token (client `Iv23liqTIFEtdIu6Vn1r`, no OAuth scopes);
  - an expiry of 2026-09-25 17:50:26 UTC.
- **Two different gatekeepers answer "no", and they can be told apart:**
  - The Anthropic proxy: no `Server: github.com`, no GitHub request id. It
    answers "sessions are bound to their configured repositories", or "not
    permitted through this proxy". [V] This covers `/user/installations`,
    `/users/*/events`, `/repos/*/hooks`, `github.com/web-flow.gpg`, and the
    repository's activity web page.
  - GitHub itself: it refuses branch protection and traffic with "Resource not
    accessible by integration", needing `administration=read`. [V]
- **The "admin" label is the owner's role, not what the token may do.** The
  repository object says `permissions.admin: true` [V], yet the token cannot
  even read branch protection. [V]
- **Independent archives and GitHub's docs are blocked by the egress policy:**
  GH Archive, Software Heritage, archive.org, docs.github.com. [V] A public
  keyserver is reachable. [V]

### The one event that existed before today

- Commit `00c7531` (24 June) was made in the web UI. [V]
  - GitHub says `verified: true`, `verified_at` 1 s after the commit. [V]
  - Checked locally with gpg: GOODSIG with key `968479A1…B5690EEEBB952194`
    (uid "GitHub <noreply@github.com>"). [V] The key came from a public
    keyserver, because GitHub's own key file is blocked here, so the claim
    "this key is GitHub's" still rests on GitHub. [I]
- The activity record still holds the creation of `main` after 93 days:
  before/after SHA, ref, timestamp, actor `asymx-mechanics`. [V]
- The public events API had **0** events. [V] I assume a 90-day retention [M],
  but did not prove it.

## Part 2 — one write experiment: push, then try to undo

**Plan.** Push a harmless probe commit to this session's branch, force-push the
branch back to `00c7531`, delete the branch, and see what GitHub keeps.
Predictions were written in the conversation before the first push.

**What happened.**

| step | time (UTC) | result |
|---|---|---|
| probe commit `95749e6` created | 11:14:49 | signed by the platform's SSH key (ed25519, `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc`) [V] |
| push → new branch `claude/explore-source-gate-q4tqd3` | 11:15:52 | accepted [V] |
| force-push back to `00c7531` | — | **refused by Claude Code's auto-mode permission check** ("Git Destructive"); it never reached git or GitHub [V] |
| delete the branch | — | not attempted: it has the same effect as the refused step |
| read-only re-observation of GitHub | — | also refused by the same check, probably a false positive; not re-read by other means [V] |
| restore the tree with a new commit instead | 11:19:59 | `c31dd03` removes the probe file; history kept [V] |

**What GitHub recorded for the push** (observed 5 s later): [V]

- An activity record: `branch_creation`, `0000000 → 95749e6`, actor
  `asymx-mechanics`, and no field naming an app.
- A public `CreateEvent`, actor `asymx-mechanics`, within 5 seconds. No
  `PushEvent` had appeared at that moment.
- The commit is `verified: true, reason: valid`, with `verified_at` equal to the
  push time, not the commit time. The author, committer *and signing key* belong
  to the GitHub account **`claude`**.

So GitHub's record reads: *`asymx-mechanics` pushed a commit authored and
signed by `claude`.* The push actor is the owner's account; only the signature
points at the platform. I infer, untested, that the key is shared across Claude
sessions, so it shows "made through Claude's signing path", not "made by this
session". [I]

**Predictions.**

| | prediction | outcome |
|---|---|---|
| W1 | push to the session branch succeeds | yes |
| W2 | commit shows as Verified (~50%) | yes, as account `claude` |
| W3 | activity actor `asymx-mechanics`, no app field | yes |
| W4 | force-push accepted, recorded as `force_push` | **not tested:** refused before reaching GitHub |
| W5 | deletion recorded as `branch_deletion` | not tested |
| W6 | rewound commit still fetchable by SHA | not tested: the commit is still on the branch |
| W7 | public events within 15 minutes | yes, within 5 s (CreateEvent) |
| W8 | `git fetch` of the rewound commit by SHA | not tested |

## Layers that decide what an action can do

1. **Your instructions:** what I *may* do.
2. **Claude Code's permission check:** the gate missing from my first map. It
   refused a destructive git action even under standing permission for normal
   actions, and then a read-only script. [V]
3. **The platform's session binding:** repository `asymx-mechanics/source-gate`,
   outcome branch `claude/explore-source-gate-q4tqd3`, network allowlist. [V]
4. **The egress proxy:** credential injection and path policy. [V]
5. **GitHub:** the owner's role intersected with the app's permissions [M]. Here
   that means no `administration` access. [V]

Capability also moves over time: the GitHub tool connection dropped and came
back mid-session, the worker restarted, and the token expires the same day. [V]

## Per action (summary)

| action | GitHub keeps | owner can remove | this session can remove |
|---|---|---|---|
| push | objects, ref, activity (≥ 93 days seen), events [V] | ref, whole repo [M] | nothing it recorded [V/I] |
| force-push / rewind | activity `force_push`, rewound commit by SHA [M] | ref; GitHub Support purge [M] | refused by the permission check [V] |
| branch create/delete | activity + events [V create, M delete] | ref [M] | delete not attempted |
| issue / comment | object, edit history, `performed_via_github_app` [M] | issues, comments, revisions [M] | tools to create/edit exist, untested |
| pull request | PR and `refs/pull/N/head`, not deletable by users [M] | close only [M] | tools exist; this PR is the first test |
| settings, protection, webhooks | owner's security log [M] | yes [M] | **no:** GitHub refuses even reads [V] |
| delete repo / visibility | restorable ~90 days [M] | yes [M] | no [V/I] |
| reads (clone, API) | traffic (owner only), request ids, proxy logs [V/M] | no [M] | cannot even see them [V] |

## What only the human can verify or decide

1. Open `github.com/asymx-mechanics/source-gate/activity` in a private window.
   Is the activity history visible to outsiders? (Blocked from here.)
2. On your own machine:
   - run `curl https://github.com/web-flow.gpg | gpg --import` and
     `git verify-commit 00c7531`, and compare the fingerprint above;
   - check `95749e6`: signed by account `claude`.
3. Settings → Applications → Claude: which permissions has the app really been
   granted? My probe says no `Administration`.
4. Settings → Security log, around 09:39 UTC today, when the account was last
   updated.
5. Insights → Traffic: this container's clone at 10:08 UTC should show [M].
6. **Whether to rewind and delete this branch after merging or closing its PR.**
   That is the part of the experiment the permission check handed to you. It
   would also answer W4–W6 and W8.
