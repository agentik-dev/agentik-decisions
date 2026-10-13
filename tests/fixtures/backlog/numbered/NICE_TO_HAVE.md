# what a review or a packet left open, none of it blocking

## The mirror

- tmux is not in the Brewfile. The owner will install it. (owner ruling 2026-09-22)
- `freeze` never discovers new files. A `discover` mode that offers candidates under `dotfiles/home/` is the follow-up.
- S1: the plist `launchd/com.example.serve.plist` loads a stale binary.
- S3: `scripts/corpus-budget` drops a glob match that is not a file.
- S3, the LaunchAgent: `launchd/com.example.serve.plist:3` names the old path.
- S2: the brew bundle check reads the Brewfile twice.

## The records

- `HANDOFF.md` reads "State as of 2026-09-03". Re-date it. (doclint WARN)
- S4: `docs/history/handoff-archive.md` holds the long form.
- S4: `example-site-a` and `example-site-b` overlap.
