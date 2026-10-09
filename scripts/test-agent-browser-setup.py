#!/usr/bin/env python3
"""Validate agent-browser declarations and browser setup with offline stubs."""

import json
import os
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


def render(source, host="iv", platform="darwin", arch="arm64", disabled=False):
    prefix = (
        '{{- $_ := set . "host_env" ' + json.dumps(host) + " -}}"
        '{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + " -}}"
        '{{- $_ := set .chezmoi "arch" ' + json.dumps(arch) + " -}}"
    )
    if disabled:
        prefix += '{{- $_ := set .tools "agent-browser" (dict "when" (dict "enabled" false)) -}}'
    return subprocess.run(
        command, input=prefix + source, text=True, capture_output=True, check=True
    ).stdout


# Real declarations must converge together, including the disabled/CI cases.
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
for host, platform, arch, enabled in (
    ("iv", "darwin", "arm64", True),
    ("personal", "darwin", "amd64", True),
    ("personal", "linux", "amd64", True),
    ("iv", "linux", "arm64", True),
    ("personal", "windows", "amd64", True),
    ("ci", "linux", "amd64", False),
    ("personal", "android", "arm64", False),
):
    manifest = json.loads(render(manifest_template, host, platform, arch))
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
    setup = render(setup_path.read_text(), host, platform, arch)
    assert bool(setup.strip()) == enabled

manifest = json.loads(render(manifest_template, disabled=True))
assert not any(
    isinstance(item, dict) and item["name"] == "agent-browser"
    for item in manifest["packages"]
)
assert manifest["agents"] == []
assert not render(setup_path.read_text(), disabled=True).strip()

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    log = sandbox / "calls.log"
    # The script prepends this rendered Bun bin. No host PATH during execution:
    # an absolute zsh -f bypasses user startup files and no real installer exists.
    bun_path = render('{{ .path.tool.bun }}').strip()
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
        script.write_text(render(setup_path.read_text(), platform=platform, arch=arch))
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

    script.write_text(render(setup_path.read_text(), platform="linux", arch="arm64"))
    log.unlink()
    subprocess.run(["/bin/zsh", "-f", str(script)], env=env, check=True, capture_output=True)
    assert not log.exists(), "unsupported Chrome download must not run on Linux ARM"

    script.write_text(render(setup_path.read_text()))
    binary.unlink()
    missing = subprocess.run(["/bin/zsh", "-f", str(script)], env=env, capture_output=True)
    assert missing.returncode == 127, "missing CLI must keep setup retryable"

print("ok agent-browser: package/skill gates, offline browser setup success/failure and retry")
