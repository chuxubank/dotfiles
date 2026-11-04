#!/usr/bin/env python3
"""Validate credential setup with offline pass-field and ncm-cli stubs."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
source = (root / "home/.chezmoiscripts/run_onchange_after_101_setup-ncm-cli.sh.tmpl").read_text()
command = ["chezmoi"]
for flag, variable in (
    ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
    ("--cache", "CHEZMOI_VERIFY_CACHE"),
):
    if os.environ.get(variable):
        command.extend([flag, os.environ[variable]])
command.extend(["execute-template", "--source", str(root)])


def render(home, host="personal", platform="darwin", disabled=False):
    prefix = (
        '{{- $_ := set . "host_env" ' + json.dumps(host) + " -}}"
        '{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + " -}}"
        '{{- $_ := set .chezmoi "homeDir" ' + json.dumps(str(home)) + " -}}"
    )
    if disabled:
        prefix += '{{- $_ := set .tools "ncm-cli" (dict "when" (dict "enabled" false)) -}}'
    return subprocess.run(
        command, input=prefix + source, text=True, capture_output=True, check=True
    ).stdout


with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    assert not render(home, host="ci").strip()
    assert not render(home, disabled=True).strip()
    assert not render(home, platform="android").strip()
    # A missing encrypted entry must not prevent rendering on a new host.
    assert "# pass entry: missing" in render(home)
    pass_path = subprocess.run(
        command, input="{{ .path.personal.pass }}", text=True,
        capture_output=True, check=True,
    ).stdout.strip()
    entry = home / pass_path / "Personal/Tech/NetEase/Music.gpg"
    entry.parent.mkdir(parents=True)
    entry.write_bytes(b"encrypted-placeholder-one")
    first = render(home)
    entry.write_bytes(b"encrypted-placeholder-two")
    assert render(home) != first, "credential rotation must change the retry unit"

    bun_path = subprocess.run(
        command, input="{{ .path.tool.bun }}", text=True,
        capture_output=True, check=True,
    ).stdout.strip()
    bins = home / bun_path / "bin"
    bins.mkdir(parents=True)
    (home / "bin").mkdir()
    reader = home / "bin/pass-field"
    reader.write_text(
        '#!/bin/sh\n'
        '[ "$1" = Personal/Tech/NetEase/Music ] || exit 9\n'
        '[ "${MOCK_PASS_STATUS:-0}" = 0 ] || exit "$MOCK_PASS_STATUS"\n'
        '[ "${MOCK_EMPTY:-0}" = 0 ] || exit 0\n'
        'case "$2" in\n'
        'appid) printf "%s\\n" placeholder-app ;;\n'
        'private-key) printf "%s\\n" "placeholder-key with spaces" ;;\n'
        '*) exit 9 ;;\nesac\n'
    )
    reader.chmod(0o755)
    binary = bins / "ncm-cli"
    binary.write_text(
        '#!/bin/sh\n'
        '[ "$1 $2" = "config set" ] || exit 9\n'
        'case "$3" in\n'
        'appId) [ "$4" = placeholder-app ] || exit 9 ;;\n'
        'privateKey) [ "$4" = "placeholder-key with spaces" ] || exit 9 ;;\n'
        '*) exit 9 ;;\nesac\n'
        'printf "%s\\n" "$3" >> "$MOCK_LOG"\n'
        'printf "%s\\n" "$4"\n'
        'printf "%s\\n" "$4" >&2\n'
        '[ "${MOCK_FAIL_KEY:-}" != "$3" ]\n'
    )
    binary.chmod(0o755)
    log = home / "calls.log"
    env = {"HOME": str(home), "PATH": str(home / "empty-bin"), "MOCK_LOG": str(log)}
    script = home / "setup.zsh"

    def run(extra=None):
        result = subprocess.run(
            ["/bin/zsh", "-f", str(script)], env={**env, **(extra or {})},
            text=True, capture_output=True,
        )
        assert "placeholder-app" not in result.stdout + result.stderr
        assert "placeholder-key" not in result.stdout + result.stderr
        return result

    for platform in ("darwin", "linux", "windows"):
        script.write_text(render(home, platform=platform))
        subprocess.run(["/bin/zsh", "-n", str(script)], check=True)
        log.unlink(missing_ok=True)
        assert run().returncode == 0
        assert log.read_text() == "appId\nprivateKey\n"
    for key in ("appId", "privateKey"):
        assert run({"MOCK_FAIL_KEY": key}).returncode != 0
        assert run().returncode == 0, "failed configuration must remain retryable"
    log.unlink()
    assert run({"MOCK_PASS_STATUS": "7"}).returncode != 0
    assert run({"MOCK_EMPTY": "1"}).returncode != 0
    assert not log.exists(), "missing credentials must not change CLI state"
    binary.unlink()
    assert run().returncode != 0, "missing CLI must keep setup retryable"

print("ok ncm-cli: gates, credential rotation, offline setup, redaction and retry")
