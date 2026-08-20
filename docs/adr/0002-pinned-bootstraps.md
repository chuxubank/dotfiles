# Pin bootstrap installers and split plan from apply

`install.sh` and the bun/uv/sdkman/Homebrew setup scripts downloaded vendor installers and executed them immediately. That is convenient and also a supply-chain footgun: HEAD contents change, and a dry-run was not a first-class entry.

Bootstraps are pinned in `installers.yaml` (version plus SHA256). `install.sh` fetches the chezmoi release tarball and checks the archive hash instead of piping `get.chezmoi.io` to sh. `./install.sh --plan` and `make plan` init (if needed) and dry-run apply. Personal source repos for skills and some plugins may still follow a branch because they change faster than a useful pin.
