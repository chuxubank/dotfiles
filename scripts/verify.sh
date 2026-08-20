#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CHEZMOI_SOURCE=${CHEZMOI_SOURCE:-$ROOT}
failed=0

cd "$ROOT"

if ! command -v chezmoi >/dev/null 2>&1; then
	echo "verify: chezmoi is not on PATH" >&2
	exit 1
fi

run_template() {
	name=$1
	out=
	if ! out=$(chezmoi execute-template --source "$CHEZMOI_SOURCE" "{{ includeTemplate \"$name\" . }}"); then
		echo "verify: $name failed" >&2
		failed=1
		return 1
	fi
	stripped=$(printf '%s' "$out" | tr -d '[:space:]')
	if [ "$stripped" != ok ]; then
		echo "verify: $name produced unexpected output:" >&2
		printf '%s\n' "$out" >&2
		failed=1
		return 1
	fi
	echo "ok $name"
}

run_template verify/contracts
run_template verify/model

if ! python3 - "$ROOT" <<'PY'; then
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
allow_exact = {
    "home/dot_config/rclone/modify_private_rclone.conf": (
        '{{ "123456" | output "rclone" "obscure" }}',
    ),
}
skip_suffixes = {".asc", ".gpg", ".png", ".jpg", ".jpeg", ".webp", ".ico"}
secret_res = [
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"""(?i)\bpassword\s*=\s*["'][^"'{$\n]{4,}["']"""),
    re.compile(r"""(?i)\bsecret\s*=\s*["'][^"'{$\n]{4,}["']"""),
    re.compile(r"""(?i)\btoken\s*=\s*["'][^"'{$\n]{4,}["']"""),
    # Quoted rclone-style pass, excluding destination paths.
    re.compile(r"""(?i)\bpass\s*=\s*["'][^"'{$\n./][^"'{$\n]{2,}["']"""),
]
failed = False
for path in root.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(root).as_posix()
    if rel.startswith(".git/") or "/.git/" in rel:
        continue
    if path.suffix.lower() in skip_suffixes:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    allowed = allow_exact.get(rel, ())
    for i, line in enumerate(text.splitlines(), 1):
        if 'includeTemplate "safe/pass"' in line or "includeTemplate 'safe/pass'" in line:
            continue
        if any(token in line for token in allowed):
            continue
        for rx in secret_res:
            if rx.search(line):
                print(f"verify: possible secret {rel}:{i}: {line.strip()}", file=sys.stderr)
                failed = True
if failed:
    sys.exit(1)
print("ok credentials")
PY
	failed=1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
: >"$tmpdir/syntax_failed"

find home/.chezmoiscripts home/bin -type f -name '*.tmpl' 2>/dev/null | sort |
	while IFS= read -r tmpl; do
		if ! rendered=$(chezmoi execute-template --source "$CHEZMOI_SOURCE" <"$tmpl"); then
			echo "verify: template failed: $tmpl" >&2
			echo 1 >"$tmpdir/syntax_failed"
			continue
		fi
		stripped=$(printf '%s' "$rendered" | tr -d '[:space:]')
		if [ -z "$stripped" ]; then
			if [ -n "$rendered" ]; then
				echo "verify: disabled script is not 0 bytes: $tmpl" >&2
				echo 1 >"$tmpdir/syntax_failed"
			fi
			continue
		fi
		out="$tmpdir/script"
		printf '%s\n' "$rendered" >"$out"
		first=$(printf '%s\n' "$rendered" | sed -n '/[^[:space:]]/{p;q;}')
		case $first in
		'#!'*zsh*)
			if command -v zsh >/dev/null 2>&1; then
				zsh -n "$out" || {
					echo "verify: zsh -n failed: $tmpl" >&2
					echo 1 >"$tmpdir/syntax_failed"
				}
			fi
			;;
		'#!'*'/bin/sh'* | '#!'*'/usr/bin/env sh'* | '#!/bin/sh' | '#!/usr/bin/env sh')
			sh -n "$out" || {
				echo "verify: sh -n failed: $tmpl" >&2
				echo 1 >"$tmpdir/syntax_failed"
			}
			;;
		esac
	done

if [ -s "$tmpdir/syntax_failed" ]; then
	failed=1
else
	echo "ok scripts"
fi

if [ "$failed" -ne 0 ]; then
	echo "verify: failed" >&2
	exit 1
fi
echo "verify: ok"
