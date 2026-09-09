#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
CHEZMOI_SOURCE=${CHEZMOI_SOURCE:-$ROOT}
failed=0

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
state="$tmpdir/chezmoistate.boltdb"
cache="$tmpdir/cache"
mkdir -p "$cache"
for candidate in \
	"${XDG_CONFIG_HOME:-$HOME/.config}/chezmoi/chezmoistate.boltdb" \
	"$HOME/Library/Application Support/chezmoi/chezmoistate.boltdb" \
	"${LOCALAPPDATA:-}/chezmoi/chezmoistate.boltdb"; do
	if [ -n "$candidate" ] && [ -f "$candidate" ]; then
		cp "$candidate" "$state"
		break
	fi
done

cm() {
	chezmoi --persistent-state "$state" --cache "$cache" "$@"
}

cd "$ROOT"

for required in chezmoi shellcheck ruff; do
	if ! command -v "$required" >/dev/null 2>&1; then
		echo "verify: $required is not on PATH" >&2
		exit 1
	fi
done

CHECK_JSONSCHEMA_VERSION=0.38.0

check_schema() {
	if command -v uvx >/dev/null 2>&1; then
		uvx --from "check-jsonschema==$CHECK_JSONSCHEMA_VERSION" check-jsonschema "$@"
	elif command -v check-jsonschema >/dev/null 2>&1 &&
		[ "$(check-jsonschema --version)" = "check-jsonschema, version $CHECK_JSONSCHEMA_VERSION" ]; then
		check-jsonschema "$@"
	else
		echo "verify: uvx or check-jsonschema $CHECK_JSONSCHEMA_VERSION is required" >&2
		return 1
	fi
}

run_template() {
	name=$1
	out=
	if ! out=$(cm execute-template --source "$CHEZMOI_SOURCE" "{{ includeTemplate \"$name\" . }}"); then
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

if ! check_schema --builtin-schema vendor.github-workflows \
	"$ROOT/.github/workflows/ci.yaml"; then
	failed=1
fi
if ! check_schema --check-metaschema "$ROOT/schemas/integrations.schema.json"; then
	failed=1
fi
if ! check_schema --schemafile "$ROOT/schemas/integrations.schema.json" \
	--regex-variant python "$ROOT/home/.chezmoidata/integrations.yaml"; then
	failed=1
fi
if ! CHEZMOI_VERIFY_STATE="$state" CHEZMOI_VERIFY_CACHE="$cache" \
	python3 "$ROOT/scripts/check-integration-semantics.py" "$ROOT"; then
	failed=1
fi
if ! python3 "$ROOT/scripts/test-integration-engine.py" "$ROOT"; then
	failed=1
fi

if ! python3 - "$ROOT" <<'PY'; then
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
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
tools_text = (root / "home/.chezmoidata/tools.yaml").read_text(encoding="utf-8")
owner_names = set(re.findall(r"^  ([a-z0-9][a-z0-9-]*):$", tools_text, re.MULTILINE))
for path in (root / "home/.chezmoiscripts").glob("*.py.tmpl"):
    name = path.name
    for owner in owner_names:
        if re.search(rf"(?:setup|teardown)-{re.escape(owner)}\.py\.tmpl$", name):
            print(
                f"verify: integration owner {owner} has a dedicated lifecycle script: {name}",
                file=sys.stderr,
            )
            failed = True
for owner in owner_names:
    adapter = root / "home/.chezmoitemplates" / owner
    for filename in ("run.py", "cleanup.py"):
        path = adapter / filename
        if path.exists():
            print(
                f"verify: integration owner {owner} has a dedicated adapter: {path.relative_to(root)}",
                file=sys.stderr,
            )
            failed = True
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
    for i, line in enumerate(text.splitlines(), 1):
        if 'includeTemplate "safe/pass"' in line or "includeTemplate 'safe/pass'" in line:
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

export PYTHONPYCACHEPREFIX="$tmpdir"
: >"$tmpdir/syntax_failed"

mark_syntax_failed() {
	echo 1 >"$tmpdir/syntax_failed"
}

check_shell() {
	interp=$1
	src=$2
	file=$3
	if [ "$interp" = sh ]; then
		sh -n "$file" || {
			echo "verify: sh -n failed: $src" >&2
			mark_syntax_failed
		}
	elif command -v "$interp" >/dev/null 2>&1; then
		"$interp" -n "$file" || {
			echo "verify: $interp -n failed: $src" >&2
			mark_syntax_failed
		}
	fi

	case $interp in
	sh | bash)
		if ! shellcheck --severity=warning --shell="$interp" "$file"; then
			echo "verify: shellcheck failed: $src" >&2
			mark_syntax_failed
		fi
		;;
	esac
}

check_python() {
	src=$1
	file=$2
	if command -v python3 >/dev/null 2>&1; then
		if ! python3 -W error::SyntaxWarning -W error::DeprecationWarning -c \
			'import sys; compile(open(sys.argv[1], "rb").read(), sys.argv[2], "exec")' \
			"$file" "$src"; then
			echo "verify: python3 compile failed: $src" >&2
			mark_syntax_failed
		fi
	fi
	if ! ruff check --quiet --select E9,F63,F7,F82 \
		--stdin-filename "${src%.tmpl}" - <"$file"; then
		echo "verify: ruff failed: $src" >&2
		mark_syntax_failed
	fi
}

check_by_shebang() {
	src=$1
	file=$2
	first=$3
	case $first in
	'#!'*zsh*)
		check_shell zsh "$src" "$file"
		;;
	'#!'*bash*)
		check_shell bash "$src" "$file"
		;;
	'#!/bin/sh'* | '#!/usr/bin/env sh'*)
		check_shell sh "$src" "$file"
		;;
	'#!'*python*)
		check_python "$src" "$file"
		;;
	esac
}

find home/.chezmoiscripts home/bin -type f -name '*.tmpl' 2>/dev/null | sort |
	while IFS= read -r tmpl; do
		if ! rendered=$(cm execute-template --source "$CHEZMOI_SOURCE" <"$tmpl"); then
			echo "verify: template failed: $tmpl" >&2
			mark_syntax_failed
			continue
		fi
		stripped=$(printf '%s' "$rendered" | tr -d '[:space:]')
		if [ -z "$stripped" ]; then
			if [ -n "$rendered" ]; then
				echo "verify: disabled script is not 0 bytes: $tmpl" >&2
				mark_syntax_failed
			fi
			continue
		fi
		out="$tmpdir/script"
		printf '%s\n' "$rendered" >"$out"
		first=$(printf '%s\n' "$rendered" | sed -n '/[^[:space:]]/{p;q;}')
		check_by_shebang "$tmpl" "$out" "$first"
	done

find . \
	-name .git -prune -o \
	-name __pycache__ -prune -o \
	-name .chezmoitemplates -prune -o \
	-type f ! -name '*.tmpl' ! -name '*.pyc' -print |
	sort |
	while IFS= read -r file; do
		rel=${file#./}
		case $rel in
		*.py)
			check_python "$rel" "$file"
			continue
			;;
		esac
		first=$(sed -n '/[^[:space:]]/{p;q;}' "$file" 2>/dev/null) || continue
		check_by_shebang "$rel" "$file" "$first"
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
