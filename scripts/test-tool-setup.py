#!/usr/bin/env python3
"""Exercise shared tool initialization with offline commands and secret readers."""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
source = (root / "home/.chezmoiscripts/run_onchange_after_101_setup-tools.py.tmpl").read_text()
command = ["chezmoi"]
for flag, variable in (
    ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
    ("--cache", "CHEZMOI_VERIFY_CACHE"),
):
    if os.environ.get(variable):
        command.extend([flag, os.environ[variable]])
command.extend(["execute-template", "--source", str(root)])


def template(text):
    return subprocess.run(
        command, input=text, text=True, capture_output=True, check=True
    ).stdout


def render(home, host="personal", platform="darwin", disabled=False, specs=None, env=None):
    prefix = (
        '{{- $_ := set . "host_env" ' + json.dumps(host) + " -}}"
        '{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + " -}}"
        '{{- $_ := set .chezmoi "homeDir" ' + json.dumps(str(home)) + " -}}"
    )
    if disabled:
        prefix += '{{- $_ := set .tools "ncm-cli" (dict "when" (dict "enabled" false)) -}}'
    if specs is not None:
        prefix += '{{- $_ := set . "tools" (fromJson ' + json.dumps(json.dumps(specs)) + ') -}}'
    return subprocess.run(
        command, input=prefix + source,
        env={**os.environ, "CI": "false", "GITHUB_ACTIONS": "false", **(env or {})},
        text=True, capture_output=True, check=True,
    ).stdout


with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    for kwargs in ({"host": "ci"}, {"disabled": True}, {"platform": "android"},
                   {"env": {"CI": "true"}}, {"env": {"GITHUB_ACTIONS": "true"}}):
        assert not render(home, **kwargs).strip()
    pass_path = template("{{ .path.personal.pass }}").strip()
    entry = home / pass_path / "Personal/Tech/NetEase/Music.gpg"
    entry.parent.mkdir(parents=True)
    first = render(home)
    assert 'missing' in first
    entry.write_bytes(b"encrypted-placeholder-one")
    second = render(home)
    entry.write_bytes(b"encrypted-placeholder-two")
    assert render(home) != second != first, "encrypted entry changes must trigger setup"
    assert "encrypted-placeholder" not in second

    # Package and skills share the setup's enablement switch.
    manifest = '''
{{- $packages := includeTemplate "package/items" (dict "ctx" . "path" (list "node" "global")) | fromJson -}}
{{- $agents := list -}}
{{- range $skill := includeTemplate "skills/providers" . | fromJson -}}
{{- if eq $skill.source "NetEase/skills" -}}
{{- $agents = includeTemplate "skills/when" (merge (dict "skill" $skill) $) | fromJson -}}
{{- end -}}{{- end -}}
{{- dict "packages" $packages "agents" $agents | toJson -}}
'''
    for platform in ("darwin", "linux", "windows", "android"):
        for host in ("personal", "iv", "ci"):
            prefix = ('{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + ' -}}'
                      '{{- $_ := set . "host_env" ' + json.dumps(host) + ' -}}')
            data = json.loads(template(prefix + manifest))
            enabled = platform != "android" and host != "ci"
            assert any(isinstance(p, dict) and p["name"] == "@music163/ncm-cli"
                       for p in data["packages"]) == enabled
            assert bool(data["agents"]) == enabled

    bins = home / template("{{ .path.tool.bun }}").strip() / "bin"
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

    def run(extra=None):
        result = subprocess.run(
            [sys.executable, str(script)], env={**env, **(extra or {})},
            text=True, capture_output=True,
        )
        assert "placeholder-app" not in result.stdout + result.stderr
        assert "placeholder-key" not in result.stdout + result.stderr
        assert "Traceback" not in result.stderr
        return result

    for platform in ("darwin", "linux", "windows"):
        script.write_text(render(home, platform=platform))
        ast.parse(script.read_text())
        log.unlink(missing_ok=True)
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
    script.write_text(render(home, specs=specs))
    assert run().returncode != 0
    assert log.read_text() == payload + "\n"
    assert not marker.exists()
    specs.pop("a-failing")
    script.write_text(render(home, specs=specs))
    assert run().returncode == 0

print("ok tool setup: gates, rotation, literal argv, preflight, redaction and retry")
