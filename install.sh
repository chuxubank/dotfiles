#!/bin/sh

# -e: exit on error
# -u: exit on unset variables
set -eu

CHEZMOI_VERSION="2.72.0"

usage() {
	cat <<'EOF'
usage: install.sh [--install-only] [--init] [--apply] [--plan] [--reinstall]

Install a pinned chezmoi binary, then optionally init/apply this source.

  (no flags)       install chezmoi if needed, then init --apply
  --install-only   install chezmoi binary only
  --init           chezmoi init (installs chezmoi if needed)
  --apply          chezmoi apply after init
  --plan           chezmoi apply --dry-run after init (does not apply)
  --reinstall      replace chezmoi even if it is already on PATH
EOF
}

do_init=0
do_apply=0
do_plan=0
reinstall=0

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
		--plan)
			do_init=1
			do_plan=1
			;;
		--reinstall) reinstall=1 ;;
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

if [ "$do_plan" -eq 1 ]; then
	do_apply=0
fi

fetch_verify() {
	_url=$1
	_sha256=$2
	_dest=$3
	_got=

	if command -v curl >/dev/null 2>&1; then
		curl -fsSL "$_url" -o "$_dest"
	elif command -v wget >/dev/null 2>&1; then
		wget -qO "$_dest" "$_url"
	else
		echo "install.sh: need curl or wget to download $_url" >&2
		return 1
	fi

	if command -v sha256sum >/dev/null 2>&1; then
		_got=$(sha256sum "$_dest" | awk '{print $1}')
	elif command -v shasum >/dev/null 2>&1; then
		_got=$(shasum -a 256 "$_dest" | awk '{print $1}')
	else
		echo "install.sh: need sha256sum or shasum" >&2
		return 1
	fi

	if [ "$_got" != "$_sha256" ]; then
		echo "install.sh: checksum mismatch for $_url" >&2
		echo "  expected $_sha256" >&2
		echo "  got      $_got" >&2
		rm -f "$_dest"
		return 1
	fi
}

chezmoi_archive_sha256() {
	# Mirrors installers.chezmoi.archives in .chezmoidata/installers.yaml.
	case $1 in
	darwin_amd64) echo 41be255eacf46b1b333591b4ddc7e90e2aa98ccb8dce47609b8284b856841652 ;;
	darwin_arm64) echo 53e576042afba703290bbc320e64d0b6bdf1082a8fb9f0d13b97e68a6e6c059f ;;
	linux_amd64) echo 0d6665b96c527d57fdc562bf19e808f80f48c2d977062c03e3e65c6b09eafbce ;;
	linux_arm64) echo e79a27621256390f03166d3965e6a1946f983a096c4d90f02c43d2aa5b563728 ;;
	android_arm64) echo f1bcb77b37233d4885c0b3bbb534f9e8d05fd170d6d8a87837a00e1cbe6e32b7 ;;
	*)
		echo "install.sh: no pinned checksum for chezmoi archive $1" >&2
		return 1
		;;
	esac
}

install_chezmoi() {
	bin_dir="${HOME}/.local/bin"
	chezmoi_bin="${bin_dir}/chezmoi"
	os=$(uname -s | tr '[:upper:]' '[:lower:]')
	arch=$(uname -m)
	key=
	asset=
	sha256=
	url=
	tmpdir=
	archive=

	case $arch in
	x86_64 | amd64) arch=amd64 ;;
	arm64 | aarch64) arch=arm64 ;;
	esac

	if [ -n "${PREFIX-}" ] && [ -d "${PREFIX}/bin" ] && command -v termux-info >/dev/null 2>&1; then
		os=android
	fi

	key="${os}_${arch}"
	asset="chezmoi_${CHEZMOI_VERSION}_${key}.tar.gz"
	sha256=$(chezmoi_archive_sha256 "$key")
	url="https://github.com/twpayne/chezmoi/releases/download/v${CHEZMOI_VERSION}/${asset}"

	mkdir -p "${bin_dir}"
	tmpdir=$(mktemp -d)
	archive="${tmpdir}/${asset}"
	echo "Installing chezmoi ${CHEZMOI_VERSION} to '${chezmoi_bin}'" >&2
	fetch_verify "$url" "$sha256" "$archive"
	tar -xzf "$archive" -C "$tmpdir" chezmoi
	mv "$tmpdir/chezmoi" "$chezmoi_bin"
	chmod 755 "$chezmoi_bin"
	rm -rf "$tmpdir"
	echo "$chezmoi_bin"
}

if ! chezmoi="$(command -v chezmoi)" || [ "$reinstall" -eq 1 ]; then
	chezmoi=$(install_chezmoi)
fi

script_dir="$(cd -P -- "$(dirname -- "$(command -v -- "$0")")" && pwd -P)"

if [ "$do_init" -eq 0 ] && [ "$do_apply" -eq 0 ] && [ "$do_plan" -eq 0 ]; then
	exit 0
fi

if [ "$do_plan" -eq 1 ]; then
	echo "Running 'chezmoi init --source=${script_dir}'" >&2
	"$chezmoi" init --source="${script_dir}"
	echo "Running 'chezmoi apply --dry-run --source=${script_dir}'" >&2
	exec "$chezmoi" apply --dry-run --source="${script_dir}"
fi

if [ "$do_init" -eq 1 ] && [ "$do_apply" -eq 1 ]; then
	echo "Running 'chezmoi init --apply --source=${script_dir}'" >&2
	exec "$chezmoi" init --apply --source="${script_dir}"
fi

if [ "$do_apply" -eq 1 ]; then
	echo "Running 'chezmoi apply --source=${script_dir}'" >&2
	exec "$chezmoi" apply --source="${script_dir}"
fi

if [ "$do_init" -eq 1 ]; then
	echo "Running 'chezmoi init --source=${script_dir}'" >&2
	exec "$chezmoi" init --source="${script_dir}"
fi
