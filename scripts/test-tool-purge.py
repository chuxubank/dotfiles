#!/usr/bin/env python3
"""Offline command-purge checks: best-effort uninstall, then Trash leftovers."""

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
    for case, expected in (
        ("missing", 0), ("dangling", 0), ("non-executable", 0),
        ("absent", 0), ("success", 0), ("uninstall-failed", 0),
        ("uninstall-partial", 0), ("no-trash", 1), ("trash-failed", 9),
        ("trash-partial", 1),
    ):
        home = sandbox / (case + " with spaces")
        home.mkdir()
        bins = home / "bin"
        bins.mkdir()
        owned = home / "owned"
        launcher = home / "cleanup"
        other_launcher = home / ".local/bin/fixture"
        other_launcher.parent.mkdir(parents=True)
        shared = home / "shared-skill"
        shared.write_text("must survive cleanup")
        if case != "absent":
            owned.mkdir()
            (owned / "skill").symlink_to(shared)
            other_launcher.symlink_to(home / "missing-runtime")
        if case == "dangling":
            launcher.symlink_to(home / "missing-runtime")
        elif case == "non-executable":
            launcher.write_text("not executable")
        elif case.startswith("uninstall-") or case == "success":
            launcher.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\nfrom pathlib import Path\n"
                "Path(os.environ['MOCK_LOG']).write_text(json.dumps([sys.argv[1:], os.environ['FIXTURE_VALUE']]))\n"
                "if os.environ['CASE'] == 'uninstall-failed': sys.exit(7)\n"
                "if os.environ['CASE'] == 'success':\n"
                "    home = Path.home()\n"
                "    (home / 'owned/skill').unlink()\n"
                "    (home / 'owned').rmdir()\n"
                "    (home / '.local/bin/fixture').unlink()\n"
                "    Path(sys.argv[0]).unlink()\n"
            )
            launcher.chmod(0o755)
        if case != "no-trash":
            trash = bins / "trash"
            trash.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys\nfrom pathlib import Path\n"
                "with open(os.environ['TRASH_LOG'], 'a') as f: f.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                "if os.environ['CASE'] == 'trash-failed': sys.exit(9)\n"
                "if os.environ['CASE'] == 'trash-partial': sys.exit(0)\n"
                "assert sys.argv[1] == '--'\n"
                "p = Path(sys.argv[2])\n"
                "dest = Path.home() / 'Trash'\n"
                "dest.mkdir(exist_ok=True)\n"
                "p.rename(dest / p.name)\n"
            )
            trash.chmod(0o755)
        # Deterministic non-macOS result for the no-backend case.
        uname = bins / "uname"
        uname.write_text("#!/bin/sh\nprintf 'Linux\\n'\n")
        uname.chmod(0o755)
        log = home / "trash.jsonl"
        calls_log = home / "calls.json"
        env = {**os.environ, "HOME": str(home), "PATH": str(bins), "CASE": case,
               "TRASH_LOG": str(log), "MOCK_LOG": str(calls_log)}
        result = subprocess.run(["/bin/sh", str(script)], env=env, text=True, capture_output=True)
        assert result.returncode == expected, (case, result.returncode, result.stderr)
        assert shared.read_text() == "must survive cleanup", "must not follow skill symlinks"
        assert not (home / "injected").exists()
        if calls_log.exists():
            assert json.loads(calls_log.read_text()) == [[literal], literal]
        if case == "uninstall-failed":
            assert "7" in result.stderr and "warning" in result.stderr.lower(), result.stderr
        if expected == 0:
            assert not owned.exists() and not other_launcher.is_symlink(), case
            if case not in ("absent", "success"):
                assert (home / "Trash/owned/skill").is_symlink()
                assert (home / "Trash/fixture").is_symlink()
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                assert calls == [["--", str(owned)], ["--", str(other_launcher)]]
            previous = log.read_text() if log.exists() else ""
            subprocess.run(["/bin/sh", str(script)], env=env, check=True, capture_output=True)
            assert (log.read_text() if log.exists() else "") == previous
        else:
            assert owned.exists(), case

# Reproduce the live Hermes shape without touching any real files.
hermes = json.loads(subprocess.run(
    command, input='{{ .tools.hermes | toJson }}', text=True, capture_output=True, check=True,
).stdout)
hermes["when"] = {"enabled": False}
with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    bins = home / "bin"
    bins.mkdir()
    shared = home / "shared/skills/example"
    shared.mkdir(parents=True)
    (shared / "SKILL.md").write_text("keep shared skill")
    owned = home / ".hermes/skills"
    owned.mkdir(parents=True)
    (owned / "example").symlink_to(shared)
    unrelated = home / ".local/bin/unrelated"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("keep unrelated launcher")
    trash = bins / "trash"
    trash.write_text(
        f"#!{sys.executable}\n"
        "import sys\nfrom pathlib import Path\n"
        "assert sys.argv[1] == '--'\n"
        "p = Path(sys.argv[2])\n"
        "dest = Path.home() / 'Trash'\n"
        "dest.mkdir(exist_ok=True)\n"
        "p.rename(dest / p.name)\n"
    )
    trash.chmod(0o755)
    script = home / "hermes-purge.sh"
    script.write_text(render({
        "tools": {"hermes": hermes}, "policies": {"purge_disabled_tools": True},
        "chezmoi": {"os": "linux"},
    }))
    subprocess.run(["/bin/sh", "-n", str(script)], check=True)
    env = {**os.environ, "HOME": str(home), "PATH": str(bins)}
    for _ in range(2):
        subprocess.run(["/bin/sh", str(script)], env=env, check=True, capture_output=True)
    assert not (home / ".hermes").exists()
    assert (home / "Trash/.hermes/skills/example").is_symlink()
    assert (shared / "SKILL.md").read_text() == "keep shared skill"
    assert unrelated.read_text() == "keep unrelated launcher"

print("ok command purge: gates, literal argv/env, uninstall warnings, Trash cleanup/retry and Hermes leftovers")
