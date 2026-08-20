# Do not pin vendor bootstrap installers

We tried version + SHA256 pins in `installers.yaml` and `install.sh`. Official install scripts (especially SDKMAN) change at HEAD, so the hash went stale and a new machine could not install. Dual-sourcing the chezmoi checksum in `install.sh` and data files made the same drift worse.

Vendor `curl | sh` is accepted for chezmoi, uv, bun, SDKMAN, and Homebrew. The non-writing entry is `make plan` (`chezmoi apply --dry-run`). First-machine `./install.sh` still runs `init --apply`. PATH chezmoi is used as-is.
