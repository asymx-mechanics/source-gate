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
- **Whether a later session really gets the same paths.** That is the actual
  test of continuity through re-creation, and only a later session can run it.
- Stability against changes on GitHub's side or the platform's. Pinning tools
  does not pin the world they observe.
