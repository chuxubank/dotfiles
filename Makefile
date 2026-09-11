.PHONY: apply re-add diff status update edit install init plan verify

# Let chezmoi authenticate GitHub API requests using the token managed by gh.
# Keep an explicitly supplied chezmoi token, and otherwise leave this empty if
# gh is unavailable or not logged in.
export CHEZMOI_GITHUB_ACCESS_TOKEN ?= $(shell \
	if command -v gh >/dev/null 2>&1; then \
		gh auth token --hostname github.com 2>/dev/null; \
	fi)

# Surface git-repo external refreshes in real time; see the shim itself
# (home/dot_local/libexec/chezmoi-git-shim/executable_git) for the rationale.
GIT_SHIM := $(HOME)/.local/libexec/chezmoi-git-shim

install:
	./install.sh --install-only

init:
	./install.sh --init

plan:
	chezmoi apply --dry-run --force --no-tty --verbose --exclude=encrypted,scripts,externals

apply:
	PATH="$(GIT_SHIM):$$PATH" chezmoi apply --init

re-add:
	chezmoi re-add

diff:
	chezmoi diff

status:
	chezmoi status

update:
	PATH="$(GIT_SHIM):$$PATH" chezmoi update

edit:
	chezmoi edit

verify:
	./scripts/verify.sh
