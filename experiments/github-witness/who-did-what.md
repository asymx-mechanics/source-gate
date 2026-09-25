# Who did what here? Reading GitHub's own records

A Claude session's own account of its work is a claim. Two attempts to make
such claims checkable failed (`../session-receipt/`, `../atomic-gate/`). This
page lists what GitHub itself records instead, and how to read it **yourself,
from your own machine**. A Claude session sees GitHub only through its
platform's proxy.

Everything marked *verified* was observed in this repository on 2026-09-25 (see
`NOTES.md`). Anonymous API calls are rate-limited, to about 60 an hour as far
as I remember.

```sh
R=https://api.github.com/repos/asymx-mechanics/source-gate
```

## 1. Who created a commit: the signature

```sh
curl -s $R/commits/<sha> | python3 -c "import json,sys; c=json.load(sys.stdin); v=c['commit']['verification']; print(v['verified'], v['reason'], 'author:', (c['author'] or {}).get('login'), 'committer:', (c['committer'] or {}).get('login'))"
```

- **Made through Claude:** author, committer and signer are the account
  `claude`. The SSH signing key is
  `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc` (*verified* on `95749e6`).
  The key belongs to the platform, not to one session.
- **Made in GitHub's web UI (you):** committer `web-flow`. GitHub's GPG key is
  `968479A1AFF927E37D1A566BB5690EEEBB952194` (*verified* on `00c7531` and `2dda290`).
- **Check the key without trusting the API's verdict:**
  - Run `curl -s https://github.com/web-flow.gpg | gpg --import`, then
    `git verify-commit <sha>` in your own clone.
  - For the `claude` key, GitHub lists an account's signing keys at
    `https://api.github.com/users/claude/ssh_signing_keys` (*not tested*; that
    path is blocked for Claude sessions).
- **Limit:** a signature says who *created* a commit, not who *pushed* it.

## 2. Who opened an issue or pull request, and through what

```sh
curl -s $R/issues/<n> | python3 -c "import json,sys; d=json.load(sys.stdin); a=d.get('performed_via_github_app'); print(d['user']['login'], 'via app:', a and a['slug'])"
```

- The account is always yours when Claude acts. Claude acts through your
  connected GitHub account.
- `via app: claude` means it went through the Claude app (*verified* on #1).

## 3. Who merged, and exactly what they accepted

```sh
curl -s $R/pulls/<n> | python3 -c "import json,sys; p=json.load(sys.stdin); print('merged_by', (p['merged_by'] or {}).get('login'), 'head', p['head']['sha'][:7], 'merge commit', str(p['merge_commit_sha'])[:7])"
curl -s "$R/issues/<n>/timeline?per_page=100" | python3 -c "import json,sys; [print(e['event'], (e.get('actor') or {}).get('login'), 'via app:', (e.get('performed_via_github_app') or {}).get('slug')) for e in json.load(sys.stdin) if e.get('event') in ('merged','closed','reopened')]"
```

- Your merge of #1: `merged_by asymx-mechanics`, `via app: None` (*verified*).
- A merge through the Claude app would most likely show `via app: claude` there
  (*inferred, not tested*).
- The merge commit's second parent is the exact commit that was accepted.

## 4. Who pushed: the weak spot

```sh
curl -s "$R/activity?per_page=100" | python3 -c "import json,sys; [print(a['timestamp'], a['activity_type'], a['ref'], a['before'][:7], '->', a['after'][:7], a['actor']['login']) for a in json.load(sys.stdin)]"
```

- It lists pushes, branch creations and deletions, and (as far as I know)
  force-pushes, with the old and new commit.
- **The actor is the account behind the token.** Claude's pushes appear as
  yours, and no app is named (*verified*). To tell them apart, look at the
  signatures of the pushed commits (section 1).
- Whether this endpoint works without logging in is *untested*.

## What these records cannot tell you

- Anything that never reached GitHub: local work, drafts, reasons.
- Who held a key or token. GitHub attributes actions to accounts and keys.
  - The `claude` signing key and the app's token live with Anthropic's platform.
  - Your account lives with you.
  - GitHub can write any of its own records.

  The fields above are the ones that *did* differ between your actions and
  Claude's in this repository. That is evidence of how things are recorded,
  not a guarantee against the parties that hold the keys.
