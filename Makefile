.PHONY: apply re-add diff status update edit install init plan verify

# Let chezmoi authenticate GitHub API requests using the token managed by gh.
# Keep an explicitly supplied chezmoi token, and otherwise leave this empty if
# gh is unavailable or not logged in.
export CHEZMOI_GITHUB_ACCESS_TOKEN ?= $(shell \
	if command -v gh >/dev/null 2>&1; then \
		gh auth token --hostname github.com 2>/dev/null; \
	fi)

install:
	./install.sh --install-only

init:
	./install.sh --init

plan:
	chezmoi apply --dry-run --force --no-tty --verbose --exclude=encrypted,scripts,externals

apply:
	./scripts/report-externals.sh apply --init

re-add:
	chezmoi re-add

diff:
	chezmoi diff

status:
	chezmoi status

update:
	./scripts/report-externals.sh update

edit:
	chezmoi edit

verify:
	./scripts/verify.sh
