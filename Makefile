.PHONY: apply re-add diff status update edit

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
