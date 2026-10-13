#!/usr/bin/env python3
"""Exercise rendered Bun/uv upgrade scripts with offline executables only."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
command = ["chezmoi"]
for flag, variable in (
    ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
    ("--cache", "CHEZMOI_VERIFY_CACHE"),
):
    if os.environ.get(variable):
        command.extend([flag, os.environ[variable]])
command.extend(["execute-template", "--source", str(root)])
prefix = '{{- $_ := set . "host_env" "personal" -}}'
zsh = shutil.which("zsh")

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    scripts = {}
    for number, tool in ((102, "bun"), (103, "uv")):
        template = root / f"home/.chezmoiscripts/run_onchange_after_{number}_upgrade-{tool}.sh.tmpl"
        script = sandbox / f"{tool}.zsh"
        script.write_text(subprocess.run(
            command, input=prefix + template.read_text(), text=True,
            capture_output=True, check=True,
        ).stdout)
        subprocess.run([zsh, "-n", str(script)], check=True)
        scripts[tool] = script

    def executable(path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)

    def case(tool, layout, *, brew=True, cellar_status=0, self_status=0,
             package_status=0, refusal=False, expected=0):
        home = sandbox / f"{tool}-{layout}-{brew}-{cellar_status}-{self_status}-{package_status}-{refusal}"
        bins = home / "bin"
        bins.mkdir(parents=True)
        (home / ".zshenv").write_text("")
        cellar = home / "custom brew/Cellar"
        body = (
            f'printf "{tool} %s\\n" "$*" >> "$MOCK_LOG"\n'
            'case "$*" in\n'
            '  upgrade|"self update")\n'
            '    if [ "$MOCK_REFUSAL" = 1 ]; then\n'
            '      echo "only works with standalone installation scripts" >&2\n'
            '    fi\n'
            '    exit "$MOCK_SELF_STATUS" ;;\n'
            '  "update -g --latest"|"tool upgrade --all") exit "$MOCK_PACKAGE_STATUS" ;;\n'
            'esac\nexit 0\n'
        )
        brewed = cellar / tool / "1.0/bin" / tool
        if layout in ("brewed", "shadowed"):
            executable(brewed, body)
            (bins / tool).symlink_to(brewed)
        else:
            executable(bins / tool, body)
        if layout == "shadowed":
            # The selected standalone copy wins even with the formula installed.
            executable(home / ".local/bin" / tool, body)
        if brew:
            executable(bins / "brew", 'echo "$MOCK_CELLAR"\nexit "$MOCK_CELLAR_STATUS"\n')
        executable(bins / "bunx", 'printf "bunx %s\\n" "$*" >> "$MOCK_LOG"\n')
        log = home / "calls.log"
        env = {
            **os.environ, "HOME": str(home), "PATH": str(bins),
            "BUN_INSTALL": str(home / "bun"), "MOCK_LOG": str(log),
            "MOCK_CELLAR": str(cellar), "MOCK_CELLAR_STATUS": str(cellar_status),
            "MOCK_SELF_STATUS": str(self_status), "MOCK_PACKAGE_STATUS": str(package_status),
            "MOCK_REFUSAL": "1" if refusal else "0",
        }
        result = subprocess.run([zsh, "-f", str(scripts[tool])], env=env,
                                text=True, capture_output=True)
        assert result.returncode == expected, (tool, layout, result.stdout, result.stderr)
        calls = log.read_text().splitlines()
        self_call = "bun upgrade" if tool == "bun" else "uv self update"
        skip = layout == "brewed" and brew and cellar_status == 0
        assert (self_call in calls) == (not skip), (tool, layout, calls)
        package_call = "bun update -g --latest" if tool == "bun" else "uv tool upgrade --all"
        assert package_call in calls, (tool, layout, calls)
        if tool == "bun":
            assert "bunx playwright install chromium" in calls, calls
        if skip:
            assert "managed by Homebrew; skipping self-update" in result.stdout

    for tool in scripts:
        case(tool, "brewed")
        case(tool, "standalone")
        case(tool, "shadowed")
        case(tool, "standalone", brew=False)
        case(tool, "standalone", cellar_status=1)
        case(tool, "brewed", package_status=1, expected=1)
        case(tool, "standalone", self_status=1, expected=1 if tool == "uv" else 0)
    case("uv", "standalone", self_status=1, refusal=True)

print("ok tool upgrades")
