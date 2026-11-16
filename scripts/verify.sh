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

# Validate static declaration contracts before templates consume typed fields.
# One interpreter load when uvx is available. Exit 1 aborts on data/schema
# failures; exit 2 is only the workflow file, which must not hide later checks.
# Without uvx, the pinned check-jsonschema binary still batches metaschemas.
schema_status=0
if command -v uvx >/dev/null 2>&1; then
	uvx --from "check-jsonschema==$CHECK_JSONSCHEMA_VERSION" python3 - "$SOURCE" <<'PY' || schema_status=$?
import sys
from pathlib import Path

from check_jsonschema.cli import main

source = Path(sys.argv[1])


def run(args):
    code = main.main(list(args), standalone_mode=False)
    return int(code or 0)


def instances(schema, paths):
    files = [str(path) for path in paths]
    if not files:
        print(f"verify: no files for {schema.name}", file=sys.stderr)
        return 1
    return run(
        ["--schemafile", str(schema), "--regex-variant", "python", *files]
    )


schemas = sorted((source / "schemas").glob("*.schema.json"))
if not schemas or run(["--check-metaschema", *[str(path) for path in schemas]]):
    sys.exit(1)

data = source / "home/.chezmoidata"
packages = data / "packages"
groups = (
    ("tools.schema.json", [data / "tools.yaml"]),
    ("defaults.schema.json", [data / "defaults.yaml"]),
    ("integrations.schema.json", [data / "integrations.yaml"]),
    ("plugin-managers.schema.json", [data / "plugin-managers.yaml"]),
    (
        "packages.schema.json",
        sorted(packages.glob("*.toml")) + sorted((packages / "brew").glob("*.toml")),
    ),
    ("skills.schema.json", sorted((data / "skills").glob("*.yaml"))),
    ("plugins.schema.json", sorted((data / "plugins").glob("*.yaml"))),
    ("llm-policy.schema.json", sorted((data / "llm").glob("*.yaml"))),
)
for name, paths in groups:
    if instances(source / "schemas" / name, paths):
        sys.exit(1)
if run(
    [
        "--builtin-schema",
        "vendor.github-workflows",
        str(source / ".github/workflows/ci.yaml"),
    ]
):
    sys.exit(2)
sys.exit(0)
PY
else
	check_schema --check-metaschema "$SOURCE"/schemas/*.schema.json || schema_status=1
	if [ "$schema_status" -eq 0 ]; then
		for domain in tools defaults integrations plugin-managers; do
			check_schema --schemafile "$SOURCE/schemas/$domain.schema.json" \
				--regex-variant python "$SOURCE/home/.chezmoidata/$domain.yaml" || schema_status=1
			[ "$schema_status" -eq 0 ] || break
		done
	fi
	if [ "$schema_status" -eq 0 ]; then
		check_schema --schemafile "$SOURCE/schemas/packages.schema.json" \
			--regex-variant python "$SOURCE"/home/.chezmoidata/packages/*.toml \
			"$SOURCE"/home/.chezmoidata/packages/brew/*.toml || schema_status=1
	fi
	if [ "$schema_status" -eq 0 ]; then
		check_schema --schemafile "$SOURCE/schemas/skills.schema.json" \
			--regex-variant python "$SOURCE"/home/.chezmoidata/skills/*.yaml || schema_status=1
	fi
	if [ "$schema_status" -eq 0 ]; then
		check_schema --schemafile "$SOURCE/schemas/plugins.schema.json" \
			--regex-variant python "$SOURCE"/home/.chezmoidata/plugins/*.yaml || schema_status=1
	fi
	if [ "$schema_status" -eq 0 ]; then
		check_schema --schemafile "$SOURCE/schemas/llm-policy.schema.json" \
			--regex-variant python "$SOURCE"/home/.chezmoidata/llm/*.yaml || schema_status=1
	fi
	if [ "$schema_status" -eq 0 ]; then
		check_schema --builtin-schema vendor.github-workflows \
			"$SOURCE/.github/workflows/ci.yaml" || schema_status=2
	fi
fi
if [ "$schema_status" -eq 2 ]; then
	failed=1
elif [ "$schema_status" -ne 0 ]; then
	exit 1
fi

run_template verify/contracts
run_template verify/model

# Independent of each other. The state db is single-writer, so each job gets
# a copy; the HTTP cache is safe to share.
: >"$tmpdir/py.jobs"
start_py() {
	_log=$tmpdir/py.$1.log
	_copy=$tmpdir/py.$1.boltdb
	shift
	if [ -f "$state" ]; then
		cp "$state" "$_copy"
	fi
	(
		CHEZMOI_VERIFY_STATE="$_copy" CHEZMOI_VERIFY_CACHE="$cache" "$@"
	) >"$_log" 2>&1 &
	printf '%s|%s\n' "$!" "$_log" >>"$tmpdir/py.jobs"
}
start_py integration-semantics python3 "$SOURCE/scripts/check-integration-semantics.py" "$SOURCE"
start_py plugin-manager-semantics python3 "$SOURCE/scripts/check-plugin-manager-semantics.py" "$SOURCE"
start_py integration-engine python3 "$SOURCE/scripts/test-integration-engine.py" "$SOURCE"
start_py plugin-engine python3 "$SOURCE/scripts/test-plugin-engine.py" "$SOURCE"
for test in test-hermes-setup.py test-tool-setup.py test-tool-purge.py test-tool-upgrades.py test-rust-setup.py test-llm-providers.py test-llm-client-providers.py test-llm-path-models.py test-agent-browser-setup.py test-skills-setup.py; do
	start_py "${test%.py}" python3 "$SOURCE/scripts/$test" "$SOURCE"
done
while IFS='|' read -r pid log; do
	if ! wait "$pid"; then
		failed=1
	fi
	cat "$log"
done <"$tmpdir/py.jobs"

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
		printf '%s\n' "$file" >>"$tmpdir/shellcheck.$interp"
		;;
	esac
}

flush_shellcheck() {
	interp=$1
	list=$tmpdir/shellcheck.$interp
	[ -s "$list" ] || return 0
	set --
	while IFS= read -r file; do
		set -- "$@" "$file"
	done <"$list"
	if ! shellcheck --severity=warning --shell="$interp" "$@"; then
		echo "verify: shellcheck ($interp) failed" >&2
		mark_syntax_failed
	fi
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
import os
import shutil
import subprocess
import sys
from pathlib import Path

source, state, cache, render_dir = map(Path, sys.argv[1:])
home = source / "home"
# Fresh-machine modify templates see an empty destination, not a missing key.
empty_stdin = b'{{- $_ := set .chezmoi "stdin" "" -}}\n'


def kind_of(template: Path):
    relative = template.relative_to(home).as_posix()
    if relative == ".chezmoi.toml.tmpl" or relative.startswith(".chezmoitemplates/"):
        return None
    name = template.name
    # modify_* is the destination-merge contract, even without a .tmpl suffix.
    if name.startswith("modify_"):
        return "modify"
    if not name.endswith(".tmpl"):
        return None
    if name.startswith(("executable_", "run_")) or b"#!" in template.read_bytes():
        return "script"
    return "template"


items = []
for path in sorted(home.rglob("*")):
    if not path.is_file():
        continue
    kind = kind_of(path)
    if kind:
        items.append((kind, path))


def render_chunk(index_chunk):
    index, chunk = index_chunk
    # bolt is single-writer. Renders inside one worker are sequential, so they
    # share a copy instead of cloning the state db for every template.
    worker_state = render_dir / f"worker-{index}.boltdb"
    if state.exists():
        shutil.copy2(state, worker_state)
    env = os.environ.copy()
    # safe/pass must not touch the live store while verification renders.
    env["CI"] = "true"
    rendered = []
    for kind, template in chunk:
        rel = template.relative_to(source).as_posix()
        worker = render_dir / rel
        worker.parent.mkdir(parents=True, exist_ok=True)
        data = template.read_bytes()
        if kind == "modify":
            data = empty_stdin + data
        result = subprocess.run(
            [
                "chezmoi",
                "--persistent-state",
                str(worker_state),
                "--cache",
                str(cache),
                "execute-template",
                "--source",
                str(source),
            ],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        worker.write_bytes(result.stdout)
        worker.with_suffix(worker.suffix + ".stderr").write_bytes(result.stderr)
        rendered.append((kind, rel, result.returncode))
    return rendered


workers = min(8, len(items) or 1)
chunks = [items[i::workers] for i in range(workers)]
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
    groups = executor.map(render_chunk, enumerate(c for c in chunks if c))
results = [item for group in groups for item in group]
results.sort(key=lambda item: item[1])

with (render_dir / "manifest").open("w", encoding="utf-8") as manifest:
    for kind, template, status in results:
        print(kind, template, status, sep="\t", file=manifest)
PY
	echo "verify: could not render templates" >&2
	failed=1
fi

if [ -f "$render_dir/manifest" ]; then
while IFS='	' read -r kind tmpl status; do
	out="$render_dir/$tmpl"
	if [ "$status" -ne 0 ]; then
		echo "verify: template failed: $tmpl" >&2
		cat "$out.stderr" >&2
		mark_syntax_failed
		continue
	fi
	# Syntax checks stay on script templates. modify_* and other configs are
	# only required to render, including an empty fresh-machine stdin.
	[ "$kind" = script ] || continue
	stripped=$(tr -d '[:space:]' <"$out")
	[ -n "$stripped" ] || continue
	first=$(sed -n '/[^[:space:]]/{p;q;}' "$out")
	case $first in
	'#!'*) ;;
	*)
		echo "verify: executable template has no shebang: $tmpl" >&2
		mark_syntax_failed
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

flush_shellcheck sh
flush_shellcheck bash

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
