#!/usr/bin/env python3
"""Exercise shared tool initialization with offline commands and secret readers."""

import ast
import json
import os
import re
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

manifest_template = '''
{{- $packages := includeTemplate "package/items" (dict "ctx" . "path" (list "node" "global")) | fromJson -}}
{{- $agents := list -}}
{{- range $skill := includeTemplate "skills/providers" . | fromJson -}}
{{- if eq $skill.source "NetEase/skills" -}}
{{- $agents = includeTemplate "skills/when" (merge (dict "skill" $skill) $) | fromJson -}}
{{- end -}}{{- end -}}
{{- dict "packages" $packages "agents" $agents | toJson -}}
'''


def render_cases(defines, cases, env=None, prelude=""):
    """Render every case in one chezmoi process.

    Hash rotation and the CI / GITHUB_ACTIONS gates stay outside this helper:
    they depend on filesystem changes or process environment between calls.
    """
    merged = {**os.environ, "CI": "false", "GITHUB_ACTIONS": "false", **(env or {})}
    parts = [prelude]
    for name, body in defines.items():
        parts.append("{{ define " + json.dumps(name) + " }}" + body + "{{ end }}")
    for key, preamble, define_name, dot in cases:
        quoted_key = json.dumps(key)
        parts.append(preamble)
        parts.append(
            "{{ printf " + json.dumps("@@CASE:%s@@") + " " + quoted_key + " }}"
            "{{ template " + json.dumps(define_name) + " " + dot + " }}"
            "{{ printf " + json.dumps("@@END:%s@@") + " " + quoted_key + " }}"
        )
    result = subprocess.run(
        command,
        input="".join(parts),
        text=True,
        capture_output=True,
        check=True,
        env=merged,
    )
    found = dict(re.findall(r"@@CASE:(.*?)@@(.*?)@@END:\1@@", result.stdout, flags=re.DOTALL))
    missing = [key for key, _, _, _ in cases if key not in found]
    if missing:
        raise AssertionError("missing template output for " + ", ".join(missing))
    return found


def ctx(home, host="personal", platform="darwin"):
    return (
        '{{- $_ := set . "host_env" ' + json.dumps(host) + " -}}"
        '{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + " -}}"
        '{{- $_ := set .chezmoi "homeDir" ' + json.dumps(str(home)) + " -}}"
    )


def render_setup(home, host="personal", platform="darwin", disabled=False, specs=None, env=None):
    preamble = ctx(home, host, platform)
    if disabled:
        preamble += '{{- $_ := set .tools "ncm-cli" (dict "when" (dict "enabled" false)) -}}'
    if specs is not None:
        preamble += '{{- $_ := set . "tools" (fromJson ' + json.dumps(json.dumps(specs)) + ") -}}"
    return render_cases({"setup": source}, [("only", preamble, "setup", ".")], env=env)["only"]


with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    # Manifests need the original ncm-cli declaration, so the disabled override
    # is last in this process. CI and GITHUB_ACTIONS are separate processes.
    static_cases = []
    for platform in ("darwin", "linux", "windows", "android"):
        for host in ("personal", "iv", "ci"):
            static_cases.append((
                f"manifest|{platform}|{host}",
                ctx(home, host, platform),
                "manifest",
                ".",
            ))
    static_cases.extend((
        ("gate-ci", ctx(home, host="ci"), "setup", "."),
        ("gate-android", ctx(home, platform="android"), "setup", "."),
        (
            "gate-disabled",
            ctx(home) + '{{- $_ := set .tools "ncm-cli" (dict "when" (dict "enabled" false)) -}}',
            "setup",
            ".",
        ),
        ("pass", '{{- $_ := set . "host_env" .host_env -}}', "pass", "."),
        ("bun", '{{- $_ := set . "host_env" .host_env -}}', "bun", "."),
    ))
    static = render_cases(
        {
            "manifest": manifest_template,
            "setup": source,
            "pass": "{{ .path.personal.pass }}",
            "bun": "{{ .path.tool.bun }}",
        },
        static_cases,
    )
    assert not static["gate-ci"].strip()
    assert not static["gate-disabled"].strip()
    assert not static["gate-android"].strip()
    assert not render_setup(home, env={"CI": "true"}).strip()
    assert not render_setup(home, env={"GITHUB_ACTIONS": "true"}).strip()

    pass_path = static["pass"].strip()
    entry = home / pass_path / "Personal/Tech/NetEase/Music.gpg"
    entry.parent.mkdir(parents=True)
    first = render_setup(home)
    assert "missing" in first
    entry.write_bytes(b"encrypted-placeholder-one")
    second = render_setup(home)
    entry.write_bytes(b"encrypted-placeholder-two")
    assert render_setup(home) != second != first, "encrypted entry changes must trigger setup"
    assert "encrypted-placeholder" not in second

    for platform in ("darwin", "linux", "windows", "android"):
        for host in ("personal", "iv", "ci"):
            data = json.loads(static[f"manifest|{platform}|{host}"])
            enabled = platform != "android" and host != "ci"
            assert any(isinstance(p, dict) and p["name"] == "@music163/ncm-cli"
                       for p in data["packages"]) == enabled
            assert bool(data["agents"]) == enabled

    bins = home / static["bun"].strip() / "bin"
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

    platforms = render_cases(
        {"setup": source},
        [(platform, ctx(home, platform=platform), "setup", ".") for platform in ("darwin", "linux", "windows")],
    )
    for platform in ("darwin", "linux", "windows"):
        script.write_text(platforms[platform])
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
    without_failing = dict(specs)
    without_failing.pop("a-failing")

    def specs_preamble(spec_map):
        return ctx(home) + (
            '{{- $_ := set . "tools" (fromJson ' + json.dumps(json.dumps(spec_map)) + ") -}}"
        )

    spec_scripts = render_cases(
        {"setup": source},
        [
            ("with-failing", specs_preamble(specs), "setup", "."),
            ("without-failing", specs_preamble(without_failing), "setup", "."),
        ],
    )
    script.write_text(spec_scripts["with-failing"])
    assert run().returncode != 0
    assert log.read_text() == payload + "\n"
    assert not marker.exists()
    specs.pop("a-failing")
    script.write_text(spec_scripts["without-failing"])
    assert run().returncode == 0

print("ok tool setup: gates, rotation, literal argv, preflight, redaction and retry")
