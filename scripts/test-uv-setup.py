#!/usr/bin/env python3
"""Windows CI must install uv tools with a managed CPython, not MSYS2 Python."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _testlib import render

root = Path(sys.argv[1]).resolve()
template = (
    root / "home/.chezmoiscripts/run_onchange_after_100_setup-uv.sh.tmpl"
).read_text()
zsh = shutil.which("zsh")


def rendered(os_name, host_env):
    prefix = (
        '{{- $_ := set . "host_env" "' + host_env + '" -}}'
        '{{- $_ := set .chezmoi "os" "' + os_name + '" -}}'
    )
    return render(root, template, prefix=prefix)


windows_ci = rendered("windows", "ci")
assert "export UV_MANAGED_PYTHON=1\n" in windows_ci
assert "uv python install 3.14" in windows_ci
for script in (
    rendered("windows", "personal"),
    rendered("darwin", "ci"),
    rendered("linux", "ci"),
):
    assert "UV_MANAGED_PYTHON" not in script
    assert "uv python install" not in script

if zsh:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "setup-uv.zsh"
        path.write_text(windows_ci)
        subprocess.run([zsh, "-n", str(path)], check=True)

print("ok uv setup: Windows CI uses managed CPython")
