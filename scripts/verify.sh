#!/bin/sh
set -eu

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
CHEZMOI_SOURCE=${CHEZMOI_SOURCE:-$ROOT}
if ! SOURCE=$(CDPATH='' cd -- "$CHEZMOI_SOURCE" && pwd -P); then
	echo "verify: CHEZMOI_SOURCE is not a readable directory: $CHEZMOI_SOURCE" >&2
	exit 1
fi
CHEZMOI_SOURCE=$SOURCE
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

cd "$SOURCE"

for required in bash chezmoi python3 shellcheck ruff zsh; do
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
	"$SOURCE/.github/workflows/ci.yaml"; then
	failed=1
fi
if ! check_schema --check-metaschema "$SOURCE/schemas/integrations.schema.json"; then
	failed=1
fi
if ! check_schema --schemafile "$SOURCE/schemas/integrations.schema.json" \
	--regex-variant python "$SOURCE/home/.chezmoidata/integrations.yaml"; then
	failed=1
fi
if ! check_schema --check-metaschema "$SOURCE/schemas/plugin-managers.schema.json"; then
	failed=1
fi
if ! check_schema --schemafile "$SOURCE/schemas/plugin-managers.schema.json" \
	"$SOURCE/home/.chezmoidata/plugin-managers.yaml"; then
	failed=1
fi
if ! CHEZMOI_VERIFY_STATE="$state" CHEZMOI_VERIFY_CACHE="$cache" \
	python3 "$SOURCE/scripts/check-integration-semantics.py" "$SOURCE"; then
	failed=1
fi
if ! CHEZMOI_VERIFY_STATE="$state" CHEZMOI_VERIFY_CACHE="$cache" \
	python3 "$SOURCE/scripts/check-plugin-manager-semantics.py" "$SOURCE"; then
	failed=1
fi
if ! python3 "$SOURCE/scripts/test-integration-engine.py" "$SOURCE"; then
	failed=1
fi
if ! python3 "$SOURCE/scripts/test-plugin-engine.py" "$SOURCE"; then
	failed=1
fi

if ! python3 - "$SOURCE" <<'PY'; then
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
		bash -n "$file" || {
			echo "verify: bash -n failed: $src" >&2
			mark_syntax_failed
		}
	else
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
	if ! python3 -W error::SyntaxWarning -W error::DeprecationWarning -m py_compile \
		"$file"; then
		echo "verify: python3 py_compile failed: $src" >&2
		mark_syntax_failed
	fi
	if ! ruff check --quiet --select E9,F63,F7,F82 \
		--stdin-filename "${src%.tmpl}" - <"$file"; then
		echo "verify: ruff failed: $src" >&2
		mark_syntax_failed
	fi
}

check_python_heredocs() {
	src=$1
	file=$2
	if ! blocks=$(python3 - "$file" "$tmpdir" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
outdir = Path(sys.argv[2])
heredoc = re.compile(
    r"(?<![\w.-])python3?(?![\w.-])[^\n<]*<<-?[ \t]*"
    r"(?:'([^']+)'|\"([^\"]+)\"|\\([^ \t\r\n]+))"
)
lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
block = 0
for line_number, line in enumerate(lines):
    if line.lstrip().startswith("#"):
        continue
    match = heredoc.search(line)
    if not match:
        continue
    delimiter = next(value for value in match.groups() if value is not None)
    strip_tabs = "<<-" in line[match.start() : match.end()]
    body = []
    for body_line in lines[line_number + 1 :]:
        candidate = body_line.rstrip("\r\n")
        if (candidate.lstrip("\t") if strip_tabs else candidate) == delimiter:
            break
        body.append(body_line)
    else:
        raise SystemExit(
            f"verify: unclosed quoted Python heredoc in {source}:{line_number + 1}"
        )
    block += 1
    path = outdir / f"python-heredoc-{block}.py"
    path.write_text("".join(body), encoding="utf-8")
    print(path)
PY
	); then
		echo "verify: Python heredoc extraction failed: $src" >&2
		mark_syntax_failed
		return
	fi
	block=0
	for heredoc in $blocks; do
		block=$((block + 1))
		check_python "$src Python heredoc $block" "$heredoc"
	done
}

check_by_shebang() {
	src=$1
	file=$2
	first=$3
	case $first in
	'#!'*zsh*)
		check_shell zsh "$src" "$file"
		check_python_heredocs "$src" "$file"
		;;
	'#!'*bash*)
		check_shell bash "$src" "$file"
		check_python_heredocs "$src" "$file"
		;;
	'#!/bin/sh'* | '#!/usr/bin/env sh'*)
		check_shell sh "$src" "$file"
		check_python_heredocs "$src" "$file"
		;;
	'#!'*python*)
		check_python "$src" "$file"
		;;
	esac
}

render_dir="$tmpdir/rendered-templates"
mkdir -p "$render_dir"
if ! python3 - "$SOURCE" "$state" "$cache" "$render_dir" <<'PY'; then
import concurrent.futures
import shutil
import subprocess
import sys
from pathlib import Path

source, state, cache, render_dir = map(Path, sys.argv[1:])
templates = sorted((source / "home").rglob("*.tmpl"))


def render(index_and_template):
    index, template = index_and_template
    worker = render_dir / str(index)
    worker.mkdir()
    worker_state = worker / "chezmoistate.boltdb"
    if state.exists():
        shutil.copy2(state, worker_state)
    result = subprocess.run(
        [
            "chezmoi",
            "--persistent-state",
            str(worker_state),
            "--cache",
            str(worker / "cache"),
            "execute-template",
            "--source",
            str(source),
        ],
        input=template.read_bytes(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (worker / "output").write_bytes(result.stdout)
    (worker / "stderr").write_bytes(result.stderr)
    return index, template.relative_to(source).as_posix(), result.returncode

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(render, enumerate(templates)))

with (render_dir / "manifest").open("w", encoding="utf-8") as manifest:
    for index, template, status in results:
        print(index, template, status, sep="\t", file=manifest)
PY
	echo "verify: could not render executable templates" >&2
	failed=1
fi

if [ -f "$render_dir/manifest" ]; then
while IFS='	' read -r index tmpl status; do
	case ${tmpl##*/} in
	executable_* | run_*) is_candidate=1 ;;
	*)
		if grep -q '#!' "$tmpl"; then
			is_candidate=1
		else
			is_candidate=0
		fi
		;;
	esac
	out="$render_dir/$index/output"
	if [ "$status" -ne 0 ]; then
		if [ "$is_candidate" -eq 1 ]; then
			echo "verify: template failed: $tmpl" >&2
			cat "$render_dir/$index/stderr" >&2
			mark_syntax_failed
		fi
		continue
	fi
	stripped=$(tr -d '[:space:]' <"$out")
	[ -n "$stripped" ] || continue
	first=$(sed -n '/[^[:space:]]/{p;q;}' "$out")
	case $first in
	'#!'*) ;;
	*)
		if [ "$is_candidate" -eq 1 ]; then
			echo "verify: executable template has no shebang: $tmpl" >&2
			mark_syntax_failed
		fi
		continue
		;;
	esac
	check_by_shebang "$tmpl" "$out" "$first"
done <"$render_dir/manifest"
fi

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
