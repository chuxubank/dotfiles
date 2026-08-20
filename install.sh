#!/bin/sh

# -e: exit on error
# -u: exit on unset variables
set -eu

usage() {
	cat <<'EOF'
usage: install.sh [--install-only] [--init] [--apply]

Install chezmoi if it is missing, then optionally init/apply this source.

  (no flags)       install chezmoi if needed, then init --apply
  --install-only   install chezmoi binary only
  --init           chezmoi init (installs chezmoi if needed)
  --apply          chezmoi init --apply
EOF
}

do_init=0
do_apply=0

if [ "$#" -eq 0 ]; then
	do_init=1
	do_apply=1
else
	for arg; do
		case $arg in
		--install-only) ;;
		--init) do_init=1 ;;
		--apply)
			do_init=1
			do_apply=1
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			echo "install.sh: unknown argument: $arg" >&2
			usage >&2
			exit 2
			;;
		esac
	done
fi

if ! chezmoi="$(command -v chezmoi)"; then
	bin_dir="${HOME}/.local/bin"
	chezmoi="${bin_dir}/chezmoi"
	echo "Installing chezmoi to '${chezmoi}'" >&2
	if command -v curl >/dev/null; then
		chezmoi_install_script="$(curl -fsSL https://chezmoi.io/get)"
	elif command -v wget >/dev/null; then
		chezmoi_install_script="$(wget -qO- https://chezmoi.io/get)"
	else
		echo "To install chezmoi, you must have curl or wget installed." >&2
		exit 1
	fi
	sh -c "${chezmoi_install_script}" -- -b "${bin_dir}"
	unset chezmoi_install_script bin_dir
fi

script_dir="$(cd -P -- "$(dirname -- "$(command -v -- "$0")")" && pwd -P)"

if [ "$do_init" -eq 0 ] && [ "$do_apply" -eq 0 ]; then
	exit 0
fi

if [ "$do_apply" -eq 1 ]; then
	echo "Running 'chezmoi init --apply --source=${script_dir}'" >&2
	exec "$chezmoi" init --apply --source="${script_dir}"
fi

echo "Running 'chezmoi init --source=${script_dir}'" >&2
exec "$chezmoi" init --source="${script_dir}"
