#!/usr/bin/env python3
"""Validate agent-browser declarations and browser setup with offline stubs."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
setup_path = root / "home/.chezmoiscripts/run_onchange_after_101_setup-agent-browser.sh.tmpl"
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
  {{- if eq $skill.source "vercel-labs/agent-browser" -}}
    {{- $agents = includeTemplate "skills/when" (merge (dict "skill" $skill) $) | fromJson -}}
  {{- end -}}
{{- end -}}
{{- dict "packages" $packages "agents" $agents | toJson -}}
'''


def render_cases(defines, cases, prelude=""):
    """Render every case in one chezmoi process.

    Each define has its own variable scope per execution. preambles mutate the
    shared root context and must not print.
    """
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
    )
    found = dict(re.findall(r"@@CASE:(.*?)@@(.*?)@@END:\1@@", result.stdout, flags=re.DOTALL))
    missing = [key for key, _, _, _ in cases if key not in found]
    if missing:
        raise AssertionError("missing template output for " + ", ".join(missing))
    return found


def ctx(host, platform, arch):
    return (
        '{{- $_ := set . "host_env" ' + json.dumps(host) + " -}}"
        '{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + " -}}"
        '{{- $_ := set .chezmoi "arch" ' + json.dumps(arch) + " -}}"
    )


matrix = (
    ("iv", "darwin", "arm64", True),
    ("personal", "darwin", "amd64", True),
    ("personal", "linux", "amd64", True),
    ("iv", "linux", "arm64", True),
    ("personal", "windows", "amd64", True),
    ("ci", "linux", "amd64", False),
    ("personal", "android", "arm64", False),
)
# Execution below also needs host iv on linux/amd64 and windows/amd64.
extra_setup = (("linux", "amd64"), ("windows", "amd64"))
cases = []
for host, platform, arch, _enabled in matrix:
    preamble = ctx(host, platform, arch)
    key = f"{host}|{platform}|{arch}"
    cases.append((key + "|manifest", preamble, "manifest", "."))
    cases.append((key + "|setup", preamble, "setup", "."))
for platform, arch in extra_setup:
    cases.append((f"iv|{platform}|{arch}|setup", ctx("iv", platform, arch), "setup", "."))
disabled = ctx("iv", "darwin", "arm64") + (
    '{{- $_ := set .tools "agent-browser" (dict "when" (dict "enabled" false)) -}}'
)
cases.append(("disabled|manifest", disabled, "manifest", "."))
cases.append(("disabled|setup", disabled, "setup", "."))
cases.append(("bun", '{{- $_ := set . "host_env" .host_env -}}', "bun", "."))
rendered = render_cases(
    {
        "manifest": manifest_template,
        "setup": setup_path.read_text(),
        "bun": "{{ .path.tool.bun }}",
    },
    cases,
)

for host, platform, arch, enabled in matrix:
    key = f"{host}|{platform}|{arch}"
    manifest = json.loads(rendered[key + "|manifest"])
    packages = [
        item for item in manifest["packages"]
        if isinstance(item, dict) and item["name"] == "agent-browser"
    ]
    assert bool(packages) == enabled, (host, platform, packages)
    if enabled:
        assert len(packages) == 1 and packages[0]["trust"] is True
        assert "pi" in manifest["agents"]
    else:
        assert manifest["agents"] == []
    assert bool(rendered[key + "|setup"].strip()) == enabled

disabled_manifest = json.loads(rendered["disabled|manifest"])
assert not any(
    isinstance(item, dict) and item["name"] == "agent-browser"
    for item in disabled_manifest["packages"]
)
assert disabled_manifest["agents"] == []
assert not rendered["disabled|setup"].strip()

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    log = sandbox / "calls.log"
    # The script prepends this rendered Bun bin. No host PATH during execution:
    # an absolute zsh -f bypasses user startup files and no real installer exists.
    bun_path = rendered["bun"].strip()
    bins = sandbox / bun_path / "bin"
    bins.mkdir(parents=True)
    binary = bins / "agent-browser"
    binary.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> "$MOCK_LOG"\n'
        'exit "${MOCK_INSTALL_STATUS:-0}"\n'
    )
    binary.chmod(0o755)
    env = {
        "HOME": str(sandbox),
        "PATH": str(sandbox / "empty-bin"),
        "MOCK_LOG": str(log),
    }
    for platform, arch in (
        ("darwin", "arm64"), ("linux", "amd64"), ("windows", "amd64")
    ):
        script = sandbox / "setup.zsh"
        script.write_text(rendered[f"iv|{platform}|{arch}|setup"])
        subprocess.run(["/bin/zsh", "-n", str(script)], check=True)
        log.unlink(missing_ok=True)
        subprocess.run(["/bin/zsh", "-f", str(script)], env=env, check=True, capture_output=True)
        assert log.read_text() == "install\n", (platform, log.read_text())
        failed = subprocess.run(
            ["/bin/zsh", "-f", str(script)],
            env={**env, "MOCK_INSTALL_STATUS": "7"}, capture_output=True,
        )
        assert failed.returncode == 7, (platform, failed.returncode)
        # Same script succeeds on retry: no custom checkpoint masks the failure.
        subprocess.run(["/bin/zsh", "-f", str(script)], env=env, check=True, capture_output=True)
        assert log.read_text() == "install\ninstall\ninstall\n"

    script.write_text(rendered["iv|linux|arm64|setup"])
    log.unlink()
    subprocess.run(["/bin/zsh", "-f", str(script)], env=env, check=True, capture_output=True)
    assert not log.exists(), "unsupported Chrome download must not run on Linux ARM"

    script.write_text(rendered["iv|darwin|arm64|setup"])
    binary.unlink()
    missing = subprocess.run(["/bin/zsh", "-f", str(script)], env=env, capture_output=True)
    assert missing.returncode == 127, "missing CLI must keep setup retryable"

print("ok agent-browser: package/skill gates, offline browser setup success/failure and retry")
