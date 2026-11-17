#!/usr/bin/env python3
"""Exercise shared tool initialization with offline commands and secret readers."""

import ast
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _testlib import render

root = Path(sys.argv[1]).resolve()
source = (root / "home/.chezmoiscripts/run_onchange_after_101_setup-tools.py.tmpl").read_text()
# The template also blanks itself when the process is CI. Pin both off for
# the renders that must produce a script.
offline = {"CI": "false", "GITHUB_ACTIONS": "false"}


def ctx(home):
    return (
        '{{- $_ := set . "host_env" "personal" -}}'
        '{{- $_ := set .chezmoi "os" "darwin" -}}'
        '{{- $_ := set .chezmoi "homeDir" ' + json.dumps(str(home)) + " -}}"
    )


def render_setup(prefix, env=None):
    return render(root, source, prefix=prefix, env={**offline, **(env or {})})


with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    pass_path = render(root, "{{ .path.personal.pass }}").strip()
    bun_path = render(root, "{{ .path.tool.bun }}").strip()
    entry = home / pass_path / "Personal/Tech/NetEase/Music.gpg"
    entry.parent.mkdir(parents=True)
    first = render_setup(ctx(home))
    assert "missing" in first
    entry.write_bytes(b"encrypted-placeholder-one")
    second = render_setup(ctx(home))
    entry.write_bytes(b"encrypted-placeholder-two")
    third = render_setup(ctx(home))
    assert third != second != first, "encrypted entry changes must trigger setup"
    assert "encrypted-placeholder" not in second
    assert not render_setup(ctx(home), env={"CI": "true"}).strip()
    assert not render_setup(ctx(home), env={"GITHUB_ACTIONS": "true"}).strip()

    bins = home / bun_path / "bin"
    bins.mkdir(parents=True)
    (home / "bin").mkdir()
    reader = home / "bin/pass-field"
    reader.write_text(
        '#!/bin/sh\n'
        '[ "$1" = Personal/Tech/NetEase/Music ] || exit 9\n'
        '[ "${MOCK_PASS_STATUS:-0}" = 0 ] || exit "$MOCK_PASS_STATUS"\n'
        '[ "${MOCK_EMPTY:-}" != "$2" ] || exit 0\n'
        'case "$2" in\n'
        'appid) printf "%s\\n" placeholder-app ;;\n'
        'private-key) printf "%s\\n" "placeholder-key with spaces; $literal" ;;\n'
        '*) exit 9 ;;\nesac\n'
    )
    reader.chmod(0o755)
    binary = bins / "ncm-cli"
    binary.write_text(
        '#!/bin/sh\n'
        '[ "$#" = 4 ] && [ "$1 $2" = "config set" ] || exit 9\n'
        'case "$3" in\n'
        'appId) [ "$4" = placeholder-app ] || exit 9 ;;\n'
        'privateKey) [ "$4" = "placeholder-key with spaces; $literal" ] || exit 9 ;;\n'
        '*) exit 9 ;;\nesac\n'
        'printf "%s\\n" "$3" >> "$MOCK_LOG"\n'
        'printf "%s\\n" "$4"\n'
        'printf "%s\\n" "$4" >&2\n'
        '[ "${MOCK_FAIL_KEY:-}" != "$3" ]\n'
    )
    binary.chmod(0o755)
    log = home / "calls.log"
    env = {"HOME": str(home), "PATH": str(home / "empty-bin"), "MOCK_LOG": str(log)}
    script = home / "setup.py"
    script.write_text(third)
    ast.parse(script.read_text())

    def run(extra=None):
        result = subprocess.run(
            [sys.executable, str(script)],
            env={**env, **(extra or {})},
            text=True,
            capture_output=True,
            check=False,
        )
        assert "placeholder-app" not in result.stdout + result.stderr
        assert "placeholder-key" not in result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        return result

    assert run().returncode == 0
    assert log.read_text() == "appId\nprivateKey\n"
    for key in ("appId", "privateKey"):
        log.unlink()
        assert run({"MOCK_FAIL_KEY": key}).returncode != 0
        expected = "appId\n" if key == "appId" else "appId\nprivateKey\n"
        assert log.read_text() == expected, "failure must stop remaining steps"
        assert run().returncode == 0
    log.unlink()
    assert run({"MOCK_PASS_STATUS": "7"}).returncode != 0
    assert run({"MOCK_EMPTY": "private-key"}).returncode != 0
    assert not log.exists(), "all inputs must resolve before any mutation"
    binary.unlink()
    assert run().returncode != 0

    # Literal argv is never interpreted as shell syntax; one failed tool does
    # not suppress another tool. Both retry on the next chezmoi attempt.
    touch = shutil.which("touch")
    marker = home / "not-created"
    literal = bins / "literal"
    literal.write_text('#!/bin/sh\nprintf "%s\\n" "$1" >> "$MOCK_LOG"\n')
    literal.chmod(0o755)
    payload = f"; {touch} {marker}"
    specs = {
        "a-failing": {"setup": [{"command": ["missing-command"]}]},
        "b-literal": {"setup": [{"command": ["literal", payload]}]},
        "c-disabled": {"when": {"enabled": False}, "setup": [{"command": ["missing"]}]},
    }

    def specs_prefix(spec_map):
        return ctx(home) + (
            '{{- $_ := set . "tools" (fromJson ' + json.dumps(json.dumps(spec_map)) + ") -}}"
        )

    script.write_text(render_setup(specs_prefix(specs)))
    assert run().returncode != 0
    assert log.read_text() == payload + "\n"
    assert not marker.exists()
    without_failing = dict(specs)
    without_failing.pop("a-failing")
    script.write_text(render_setup(specs_prefix(without_failing)))
    assert run().returncode == 0

print("ok tool setup: rotation, literal argv, preflight, redaction and retry")
