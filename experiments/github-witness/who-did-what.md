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
  The key is not per session: all 42 commits of generation 0 and the commits of
  generation 1, a different session, carry signatures by this key that check
  out (*verified* 2026-09-25 by generation 1). Until then this line said "the
  key belongs to the platform", which had not been tested. Whether sessions
  under other accounts use it too is untested (thread T3).
- **Made in GitHub's web UI (you):** committer `web-flow`. GitHub's GPG key is
  `968479A1AFF927E37D1A566BB5690EEEBB952194` (*verified* on `00c7531` and `2dda290`).
- **Check the key without trusting the API's verdict:**
  - Run `curl -s https://github.com/web-flow.gpg | gpg --import`, then
    `git verify-commit <sha>` in your own clone.
  - For the `claude` key, GitHub lists an account's signing keys at
    `https://api.github.com/users/claude/ssh_signing_keys` (*not tested*; that
    path is blocked for Claude sessions, and still was for generation 1).
  - To check the `claude` signatures yourself, with `ssh-keygen` 8.2 or later:

    ```sh
    echo 'claude namespaces="git" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKy87HxSEheG8vEPhSs9u2KZCtVErAQfpmprtUJCZ2w7' > /tmp/claude_signers
    git -c gpg.ssh.allowedSignersFile=/tmp/claude_signers log --author=Claude --format='%h %G? %GF'
    ```

    `G` means the signature is good for that key. Generation 1 ran this with
    `openssh-10.5p1` built from the package set pinned in
    `../reproducible-tools/env.nix`: 42 of 42 `G` on generation 0's commits,
    `G` on its own, and "incorrect signature" for a copy of a commit with one
    changed letter. The key line was taken out of the signature on `95749e6`, so
    on its own it only shows that one key made all these signatures. That the
    key is the `claude` account's rests on GitHub's verdict, or on comparing it
    with the list above.
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

- Your merge of #1 in the browser: `merged_by asymx-mechanics`, `via app: None`
  (*verified*).
- My merge of #4 through the Claude app: **exactly the same**. `merged_by
  asymx-mechanics`, `via app: None`, and a merge commit authored by you and
  signed by GitHub (*verified*).
- **So these records cannot tell who merged.** I had guessed the app would show
  here; it does not. Only your own word and the session's transcript can tell a
  merge by you from a merge by Claude.
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
- It works without logging in (*verified* 2026-09-25 by generation 1). The CI
  runner asked for it without a token: HTTP 200, 49 entries, and a rate limit
  of 60, which GitHub gives a caller without credentials. The same request
  from a session reports 15000, because the session's proxy adds the owner's
  token. CI repeats the request on every push (`.github/workflows/recheck.yml`).
  The web page for the same record was not looked at logged out.

## What these records cannot tell you

- Anything that never reached GitHub: local work, drafts, reasons.
- Who held a key or token. GitHub attributes actions to accounts and keys.
  - The `claude` signing key and the app's token live with Anthropic's platform.
  - Your account lives with you.
  - GitHub can write any of its own records.

  The fields above are the ones that *did* differ between your actions and
  Claude's in this repository. That is evidence of how things are recorded,
  not a guarantee against the parties that hold the keys.
