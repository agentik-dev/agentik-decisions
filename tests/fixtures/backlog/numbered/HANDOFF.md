# handoff

## Where things stand

- The repo tracks 13 dotfiles.

## Open work, highest value first

The long form of each item is in `docs/history/handoff-archive.md`.

1. **OWNER-DECISION: two repos the portfolio depends on have an unreachable remote.**
   Two plugin repos sit on another org and this Mac cannot read either.
2. **`example-site-a` and `example-site-b` both claim to be the front door.** One of them
   has to stop.
3. **Reconcile the Brewfile**: done 2026-09-28 (the owner installed `mas`). The brew bundle FAIL left is outdated formulae.
4. **Install the LaunchAgent from the repo copy** (`make launchd` copies, it does
   not `launchctl`); the plist is `launchd/com.example.serve.plist`.
5. **DECIDED 2026-09-22: the two self-churning files are filtered.** `scripts/dotfiles` ignores `lastUpdated`.
6. **Known gap: `freeze` never discovers new files**: it only compares what is listed under `dotfiles/home/`.
7. **Take `corpus-budget` from the other repo**: done 2026-10-02 (19fff99). `make verify` gained a row from `scripts/corpus-budget`.

## The next design, when you want it

1. **Whole-machine backup.** Not a step.
