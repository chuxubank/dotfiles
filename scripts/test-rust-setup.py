#!/usr/bin/env python3
"""Cargo setup force-reinstalls when the recorded git branch differs."""

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
prefix = (
    '{{- $_ := set . "host_env" "personal" -}}'
    '{{- $_ := set .chezmoi "os" "darwin" -}}'
)
template = (
    root / "home/.chezmoiscripts/run_onchange_after_100_setup-rust.sh.tmpl"
).read_text()
zsh = shutil.which("zsh")

CURRENT = """\
cargo-update v22.1.1:
beancount-language-server v1.9.2 (https://github.com/cat-emacs/beancount-language-server.git?branch=main#a01a4993):
dot-aep v0.1.0 (https://github.com/virtualritz/dot-aep#265bee87):
lsp-proxy v0.8.2 (https://github.com/cat-emacs/lsp-proxy.git?branch=main#897e6f39):
lukaj v0.2.0:
mermaid-rs-renderer v0.3.1:
rust-script v0.36.0:
starlists v0.1.0 (https://github.com/chuxubank/starlists#cd1de858):
"""
OLD_BRANCH = CURRENT.replace("branch=main#897e6f39", "branch=feat%2Fproject-activation#47e257b7")
NO_BRANCH = CURRENT.replace("?branch=main#a01a4993", "#55416109")
MISSING = "\n".join(
    line for line in CURRENT.splitlines() if not line.startswith("starlists ")
) + "\n"


def installs(log):
    return [
        line for line in log.splitlines()
        if line.startswith("cargo install ") and line != "cargo install --list"
    ]


with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    script = sandbox / "setup.zsh"
    script.write_text(subprocess.run(
        command, input=prefix + template, text=True, capture_output=True, check=True,
    ).stdout)
    subprocess.run([zsh, "-n", str(script)], check=True)
    rendered = script.read_text()
    assert 'cargo_source_current "lsp-proxy" "https://github.com/cat-emacs/lsp-proxy.git" "main"' in rendered
    assert 'cargo_source_current "beancount-language-server" "https://github.com/cat-emacs/beancount-language-server.git" "main"' in rendered

    bins = sandbox / "bin"
    bins.mkdir()
    (bins / "rustup").write_text("#!/bin/sh\nexit 0\n")
    (bins / "cargo").write_text(
        "#!/bin/sh\n"
        'printf "cargo %s\\n" "$*" >> "$MOCK_LOG"\n'
        'if [ "$1 $2" = "install --list" ]; then cat "$MOCK_LIST"; fi\n'
        "exit 0\n"
    )
    for path in (bins / "rustup", bins / "cargo"):
        path.chmod(0o755)

    def run(listing):
        home = sandbox / "home"
        home.mkdir(exist_ok=True)
        listed = sandbox / "list.txt"
        listed.write_text(listing)
        log = sandbox / "calls.log"
        log.write_text("")
        result = subprocess.run(
            [zsh, "-f", str(script)],
            env={
                **os.environ,
                "HOME": str(home),
                "PATH": f"{bins}{os.pathsep}/bin{os.pathsep}/usr/bin",
                "CARGO_HOME": str(home / "cargo"),
                "RUSTUP_HOME": str(home / "rustup"),
                "MOCK_LOG": str(log),
                "MOCK_LIST": str(listed),
            },
            text=True, capture_output=True,
        )
        assert result.returncode == 0, result.stderr + result.stdout
        return log.read_text()

    assert installs(run(CURRENT)) == []
    assert installs(run(OLD_BRANCH)) == [
        "cargo install --force --git https://github.com/cat-emacs/lsp-proxy.git --branch main lsp-proxy"
    ]
    assert installs(run(NO_BRANCH)) == [
        "cargo install --force --git https://github.com/cat-emacs/beancount-language-server.git --branch main beancount-language-server"
    ]
    assert installs(run(MISSING)) == [
        "cargo install --git https://github.com/chuxubank/starlists starlists"
    ]
