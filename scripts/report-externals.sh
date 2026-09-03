#!/bin/sh
# Run chezmoi and report which git-repo externals it pulled.
#
# chezmoi already records, per git-repo external, the moment it last ran
# clone/pull: the gitRepoExternalState bucket in the persistent state. A repo
# whose runAt advanced during this invocation is exactly a repo chezmoi
# refreshed, so no git commands and no HEAD snapshots are needed.
#
# This has to wrap chezmoi rather than hang off [hooks.*], because chezmoi
# holds an exclusive lock on the persistent state for the whole run:
#   chezmoi: timeout obtaining persistent state lock
#
# Usage: report-externals.sh update [chezmoi flags...]
set -u

CHEZMOI=${CHEZMOI:-chezmoi}

tmp=$(mktemp -d) || exit 1
trap 'rm -rf "$tmp"' EXIT INT TERM

# Forward only the flags that select which persistent state to read, so a
# --persistent-state or -c override on the wrapped command cannot make the
# before/after dumps read a different state than the run itself used.
state_flags=''
quote() { printf "%s" "$1" | sed "s/'/'\\\\''/g"; }

# Rotate the argument list: each iteration inspects $1 then appends it back, so
# after "$#" rotations "$@" is byte-identical to what the caller passed.
argc=$#
want_value=''
i=0
while [ "$i" -lt "$argc" ]; do
	if [ -n "$want_value" ]; then
		state_flags="$state_flags '$(quote "$1")'"
		want_value=''
	else
		case $1 in
		--config=* | --source=* | --destination=* | --cache=* | --persistent-state=*)
			state_flags="$state_flags '$(quote "$1")'"
			;;
		--config | -c | --source | -S | --destination | -D | --cache | --persistent-state)
			state_flags="$state_flags '$(quote "$1")'"
			want_value=yes
			;;
		esac
	fi
	set -- "$@" "$1"
	shift
	i=$((i + 1))
done

# Missing bucket (first ever run) is not an error; treat it as empty.
dump() {
	eval "\"\$CHEZMOI\" state get-bucket --bucket=gitRepoExternalState $state_flags" 2>/dev/null ||
		echo '{}'
}

dump >"$tmp/before.json"
"$CHEZMOI" "$@"
rc=$?
dump >"$tmp/after.json"

python3 - "$tmp/before.json" "$tmp/after.json" <<'PY'
import json
import os
import sys


def load(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def run_at(entry):
    return entry.get("runAt") if isinstance(entry, dict) else None


before, after = (load(path) for path in sys.argv[1:3])

pulled = sorted(key for key, value in after.items() if run_at(value) != run_at(before.get(key, {})))
skipped = len(after) - len(pulled)

if os.isatty(1):
    bold, cyan, dim, reset = "\033[1m", "\033[36m", "\033[2m", "\033[0m"
else:
    bold = cyan = dim = reset = ""

home = os.path.expanduser("~") + os.sep
if not pulled:
    print(f"{dim}No git-repo externals were refreshed ({skipped} up to date).{reset}")
else:
    print(f"{bold}Refreshed externals:{reset}")
    for key in pulled:
        shown = key[len(home):] if key.startswith(home) else key
        print(f"  {cyan}{shown}{reset}")
    if skipped:
        print(f"  {dim}({skipped} not due for refresh){reset}")
PY

exit "$rc"
