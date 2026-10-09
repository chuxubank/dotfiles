#!/usr/bin/env python3
"""Offline behavior checks for command purges; shape/ignore checks live in templates."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
command = ["chezmoi"]
for flag, key in (("--persistent-state", "CHEZMOI_VERIFY_STATE"), ("--cache", "CHEZMOI_VERIFY_CACHE")):
    if os.environ.get(key):
        command.extend([flag, os.environ[key]])
command.extend(["execute-template", "--source", str(root)])
source = (root / "home/.chezmoiscripts/run_before_010_purge-disabled-tool-commands.sh.tmpl").read_text()
literal = "dollar $HOME; quote ' and `touch injected`"
fixture = {
    "tools": {"fixture": {"when": {"enabled": False}, "purge": [{
        "command": ["{home}/cleanup", literal],
        "env": {"FIXTURE_VALUE": literal},
        "paths": ["owned/**", ".local/bin/fixture"],
        "when": {"enabled": {"os": ["linux"]}},
    }]}},
    "policies": {"purge_disabled_tools": True},
    "chezmoi": {"os": "linux"},
}


def render(data):
    prefix = '{{- $_ := set . "tools" (dict) -}}{{- $ := mergeOverwrite (deepCopy .) (' + json.dumps(json.dumps(data)) + " | fromJson) -}}{{- with $ -}}"
    return subprocess.run(command, input=prefix + source + "{{ end }}", text=True, capture_output=True, check=True).stdout


script_text = render(fixture)
for scope, key, value in (("policies", "purge_disabled_tools", False), ("chezmoi", "os", "darwin")):
    disabled = json.loads(json.dumps(fixture))
    disabled[scope][key] = value
    assert render(disabled).strip() == ""
enabled = json.loads(json.dumps(fixture))
enabled["tools"]["fixture"]["when"] = {"enabled": True}
assert render(enabled).strip() == ""

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    script = sandbox / "purge.sh"
    script.write_text(script_text)
    subprocess.run(["/bin/sh", "-n", str(script)], check=True)
    for name, expected in (("absent", 0), ("success", 0), ("failure", 7), ("partial", 1), ("missing", 1), ("dangling", 1)):
        home = sandbox / (name + " with spaces")
        home.mkdir()
        target = home / "owned"
        launcher = home / "cleanup"
        log = home / "calls.json"
        if name != "absent":
            target.touch()
        if name == "dangling":
            launcher.symlink_to(home / "missing-runtime")
        elif name not in ("absent", "missing"):
            launcher.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\nfrom pathlib import Path\n"
                "Path(os.environ['MOCK_LOG']).write_text(json.dumps([sys.argv[1:], os.environ['FIXTURE_VALUE']]))\n"
                "if os.environ['CASE'] == 'failure': sys.exit(7)\n"
                "if os.environ['CASE'] != 'partial': (Path.home() / 'owned').unlink()\n"
            )
            launcher.chmod(0o755)
        env = {**os.environ, "HOME": str(home), "PATH": str(home), "CASE": name, "MOCK_LOG": str(log)}
        result = subprocess.run(["/bin/sh", str(script)], env=env, text=True, capture_output=True)
        assert result.returncode == expected, (name, result.stderr)
        assert target.exists() == (expected != 0), "no destructive fallback"
        if log.exists():
            assert json.loads(log.read_text()) == [[literal], literal], "arguments/env must remain literal"
        else:
            assert name in ("absent", "missing", "dangling")
        assert not (home / "injected").exists()
        if name == "success":
            # Simulate the official uninstaller removing its own executable.
            launcher.unlink()
            subprocess.run(["/bin/sh", str(script)], env=env, check=True, capture_output=True)
            assert json.loads(log.read_text()) == [[literal], literal]

print("ok command purge: gates, literal argv/env, success, failure, leftovers and repeated apply")
