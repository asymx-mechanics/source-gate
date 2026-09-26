# Can the evidence here be re-run later, with the same tools?

Date: 2026-09-25. This thread was pulled from the "loose ends" in `CLAUDE.md`:
the README's fourth element, "reproducible Nix deployment", had never been
touched. It is not treated as a spec here. The question that made it worth
doing: the container disappears, and so does its toolchain. Can a later
session rebuild the same tools, and do my results depend on them?

## Result

**The experiments give the same outcome in every single case under two different
toolchains:**

| | container | pinned with Nix (`env.nix`) |
|---|---|---|
| tools | Python 3.11.15, git 2.43.0, GnuPG 2.4.4 | Python 3.14.7, git 2.55.0, GnuPG 2.4.9 |
| `session-receipt` unit tests | OK (15) | OK (15) |
| `session-receipt/attacks.py` | fooled on 14 of 18 | fooled on 14 of 18 |
| same, against `probe_patched.py` | 5 of 19 | 5 of 19 |
| `atomic-gate/attacks_gate.py` | 12 of 16 flawed | 12 of 16 flawed |

Every case, not just the totals, was compared with `diff`; there was no
difference. So these results are not an artifact of this container's tool
versions. [V]

## The pinned environment

`env.nix` fixes the package set by content hash, not by name:
- url `…/nixos-26.11pre1078696.4975466d3247/nixexprs.tar.xz`
- sha256 `1svxa407zymz2qgygwcg1v67zxjw402gaj925bdvqi3sqkm3770i`

Evaluating it gave exactly these store paths [V]:

```
/nix/store/d64q19q1xjdwfhqx6czvrjgrhq0n3lcc-python3-3.14.7
/nix/store/msr1v91ybfw6j12rs5mfl8ghb2rqsnsr-git-2.55.0
/nix/store/0prm77nf3lpljd30wbvh7c3alv2glqc7-gnupg-2.4.9
```

**This is a claim a later session can check without trusting me.** Evaluate
`env.nix` again. The same paths mean the same tools; a hash mismatch means the
source changed. In both cases Nix says so, not I.

## Getting Nix in this environment

- The usual installers are refused by the egress policy: `nixos.org` and
  `install.determinate.systems` get a 403 on connect. [V]
- `releases.nixos.org`, `channels.nixos.org` and `cache.nixos.org` are
  reachable. [V]
- The per-version installer works: `https://releases.nixos.org/nix/nix-2.35.2/install`.
  I read it before running it. It fetches one tarball and checks a sha256 that
  is written into the installer itself.
- Run as root: `sh install --no-daemon --no-modify-profile`. It stops at "group
  'nixbld' does not exist", but `/nix/store` is populated by then. Use the
  binary directly, with
  `NIX_CONFIG=$'build-users-group =\nsandbox = false\nexperimental-features = nix-command flakes'`.
- Then `nix-shell experiments/reproducible-tools/env.nix`. Or, as I did,
  `nix-store --realise` the three paths and put their `bin/` first on `PATH`,
  which avoids the larger `mkShell` closure.

## What this does not show

- **Where trust comes from.** Downloads from the binary cache are checked
  against the key `cache.nixos.org-1` (`require-sigs = true`) [V]. That key
  came with the Nix binary, whose hash came from the same host, through the
  same proxy. It is the chain the whole world uses, but its root arrived the
  same way everything else in this session did.

  Pulled further the same day. The installer's own Nix store path
  (`irfrbndi…-nix-2.35.2`) is also in the binary cache, with a signed record [V]:
  - Its NAR hash `0f84a30lz1cbbsmac94dsm48khjkmjaw5d50h1d4ipz5dwk3b10p` equals
    that of the content the installer unpacked.
  - `nix store verify --sigs-needed 1` passes against the cache's key and fails
    ("untrusted") with a wrong key, as a negative control.

  So two mechanisms agree: the hash written into the installer, and the cache's
  signature. The circle left over is that the key came inside the binary being
  checked. The one anchor outside this session's network path is that I
  recognise `cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=`
  from training, and it matches exactly. That is memory, not proof [M], but it
  did not come through the proxy.
- **Whether a later session really gets the same paths.** That is the actual
  test of continuity through re-creation, and only a later session can run it.
- Stability against changes on GitHub's side or the platform's. Pinning tools
  does not pin the world they observe.

## Re-run by a later session (generation 1, 2026-09-25, about 16:50 UTC)

A different session (`session_01NfosiZb5S6PvG38YooqvjT`) followed the steps
above. Thread T6 asked for this. Its machine booted at 16:47:57 UTC, with a
disk restored from a snapshot taken when generation 0 started (10:08), before
generation 0 installed Nix. There was no `/nix`. (The first version of this
section, in `3832f90`, said "a fresh container". The next commit corrected it.)

- The installer at the same URL had sha256
  `9adda97297d9e8ab360df95c729eabff4f4f93d6db091953c3a68f29e3fb130c` (the notes
  above did not record it). It stopped at "group 'nixbld' does not exist", as
  described, with `/nix/store` populated. [V]
- Its store path was the same, `irfrbndi76zhkvqsfhmsn4a99iafck29-nix-2.35.2`,
  with the same NAR hash `0f84a30lz1cbbsmac94dsm48khjkmjaw5d50h1d4ipz5dwk3b10p`. [V]
- `nix store verify --store https://cache.nixos.org --no-contents
  --sigs-needed 1` passed with the key the binary ships
  (`cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=`) and failed
  ("untrusted", exit 2) with a freshly generated key of the same name. [V]
- **Evaluating `env.nix` gave exactly the three store paths listed above.** The
  paths were printed with `nix-instantiate --eval --strict --json` over the
  shell's inputs and compared with the notes by `diff`, which found no
  difference. [V]
- Negative control: changing one character of the tarball's sha256 in a copy of
  `env.nix` made Nix refuse it with "NAR hash mismatch". [V]

This session did not realise the three paths or re-run the experiments under
them. It did build `openssh-10.5p1` from the same pinned package set, to check
commit signatures (thread T3, and section 1 of
`../github-witness/who-did-what.md`).

What this adds: the pin held across two containers and two sessions, about
two and a half hours apart (generation 0 recorded its evaluation in `878d3f0`,
14:20 UTC). It does not show that it holds after `releases.nixos.org` or
`cache.nixos.org` change or drop what they serve.
