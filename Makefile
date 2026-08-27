.PHONY: apply re-add diff status update edit install init plan verify

install:
	./install.sh --install-only

init:
	./install.sh --init

plan:
	chezmoi apply --dry-run --force --no-tty --verbose --exclude=encrypted,scripts,externals

apply:
	chezmoi apply --init

re-add:
	chezmoi re-add

diff:
	chezmoi diff

status:
	chezmoi status

update:
	chezmoi update

edit:
	chezmoi edit

verify:
	./scripts/verify.sh
