#!/usr/bin/env python3
"""Render Hermes templates and exercise installation with offline stubs only."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
setup_path = root / "home/.chezmoiscripts/run_after_100_setup-hermes.sh.tmpl"
upgrade_path = root / "home/.chezmoiscripts/run_onchange_after_104_upgrade-hermes.sh.tmpl"
config_path = root / "home/private_dot_hermes/modify_private_config.yaml"
command = ["chezmoi"]
for flag, variable in (
    ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
    ("--cache", "CHEZMOI_VERIFY_CACHE"),
):
    if os.environ.get(variable):
        command.extend([flag, os.environ[variable]])
command.extend(["execute-template", "--source", str(root)])


def render(path, host="iv", platform="linux", extra="", enabled_fixture=True):
    prefix = (
        '{{- $_ := set . "host_env" ' + json.dumps(host) + " -}}"
        '{{- $_ := set .chezmoi "os" ' + json.dumps(platform) + " -}}"
    )
    # Test installation independently of the live switch; keep exercising the
    # IV-only branch even while Hermes is disabled in the actual declarations.
    if enabled_fixture:
        prefix += '{{- $_ := set .tools.hermes "when" (dict "enabled" (dict "host_env" (list "iv"))) -}}'
    return subprocess.run(
        command,
        input=prefix + extra + path.read_text(),
        text=True,
        capture_output=True,
        check=True,
    ).stdout


setup = render(setup_path)
upgrade = render(upgrade_path)
assert setup.startswith("#!/bin/sh")
assert render(setup_path, platform="darwin").startswith("#!/bin/sh")
assert render(setup_path, platform="windows").strip() == ""
assert render(upgrade_path, platform="windows").strip() == ""
for host in ("personal", "aa", "ci"):
    assert render(setup_path, host=host).strip() == ""
    assert render(upgrade_path, host=host).strip() == ""
for host in ("iv", "personal", "aa", "ci"):
    assert render(setup_path, host=host, enabled_fixture=False).strip() == ""
    assert render(upgrade_path, host=host, enabled_fixture=False).strip() == ""
assert not (root / "home/.chezmoiscripts/run_onchange_after_100_setup-hermes.sh.tmpl").exists()

# Replace the whole LLM tree: no real tokens or live catalogs are read.
fixture = {
    "models": {},
    "providers": {"fixture": {"base_url": "https://example.invalid"}},
    "tools": {
        "hermes": {
            "model": "iv-codex/fixture-model",
            "reasoning_effort": "high",
            "providers": {"iv-codex": {"provider": "fixture"}},
        }
    },
}
for effort in ("high", "low"):
    fixture["tools"]["hermes"]["reasoning_effort"] = effort
    extra = (
        '{{- $_ := set . "llm" ('
        + json.dumps(json.dumps(fixture))
        + " | fromJson) -}}"
        '{{- $_ := set .chezmoi "stdin" "agent:\\n  reasoning_effort: medium\\n  max_iterations: 17\\n" -}}'
    )
    rendered = render(config_path, extra=extra)
    assert f"reasoning_effort: {effort}" in rendered
    assert "max_iterations: 17" in rendered
    assert "provider: custom:iv-codex" in rendered
    assert "default: fixture-model" in rendered

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    script = sandbox / "setup.sh"
    script.write_text(setup)
    subprocess.run(["/bin/sh", "-n", str(script)], check=True)
    upgrade_script = sandbox / "upgrade.zsh"
    upgrade_script.write_text(upgrade)
    subprocess.run(["zsh", "-n", str(upgrade_script)], check=True)
    bins = sandbox / "bin"
    bins.mkdir()
    # No host PATH during execution: never invoke a real installer or Hermes.
    for name in ("mkdir", "mktemp", "rm"):
        (bins / name).symlink_to(shutil.which(name))

    def executable(path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)

    executable(
        bins / "curl",
        'printf "curl %s\\n" "$*" >> "$MOCK_LOG"\n'
        'while [ "$#" -gt 0 ]; do\n'
        '  if [ "$1" = -o ]; then shift; printf "# offline fixture\\n" > "$1"; fi\n'
        '  shift\n'
        'done\n'
        'exit "${MOCK_DOWNLOAD_STATUS:-0}"\n',
    )
    executable(
        bins / "bash",
        'printf "bash %s\\n" "$*" >> "$MOCK_LOG"\n'
        '[ "$HERMES_HOME" = "$HOME/.hermes" ] || exit 90\n'
        '[ "$HERMES_INSTALL_DIR" = "$HOME/.hermes/hermes-agent" ] || exit 91\n'
        '[ "${MOCK_INSTALL_STATUS:-0}" = 0 ] || exit "$MOCK_INSTALL_STATUS"\n'
        'if [ "${MOCK_NO_LAUNCHER:-0}" != 1 ]; then\n'
        '  printf "#!/bin/sh\\nexit %s\\n" "${MOCK_HEALTH_STATUS:-0}" > "$HOME/.local/bin/hermes"\n'
        '  /bin/chmod +x "$HOME/.local/bin/hermes"\n'
        'fi\n',
    )

    def case(name, *, launcher=None, foreign=False, expected=0, **variables):
        home = sandbox / name
        local_bin = home / ".local/bin"
        local_bin.mkdir(parents=True)
        temp_dir = home / "temp"
        temp_dir.mkdir()
        log = home / "calls.log"
        target = local_bin / "hermes"
        if launcher == "dangling":
            target.symlink_to(home / "missing-python")
        elif launcher is not None:
            executable(target, f"exit {launcher}\n")
        foreign_bin = home / "foreign-bin"
        foreign_bin.mkdir()
        if foreign:
            executable(foreign_bin / "hermes", "exit 0\n")
        env = {
            **os.environ,
            "HOME": str(home),
            "PATH": str(foreign_bin) + os.pathsep + str(bins),
            "TMPDIR": str(temp_dir),
            "MOCK_LOG": str(log),
            # Even inherited overrides must not redirect the managed install.
            "HERMES_HOME": str(home / "unmanaged"),
            "HERMES_INSTALL_DIR": str(home / "unmanaged-install"),
            **variables,
        }
        for key in (
            "MOCK_DOWNLOAD_STATUS", "MOCK_INSTALL_STATUS", "MOCK_NO_LAUNCHER", "MOCK_HEALTH_STATUS"
        ):
            if key not in variables:
                env.pop(key, None)
        result = subprocess.run(["/bin/sh", str(script)], env=env, capture_output=True, text=True)
        assert result.returncode == expected, (name, result.returncode, result.stderr)
        assert list(temp_dir.iterdir()) == [], (name, "installer tempfile leaked")
        calls = log.read_text() if log.exists() else ""
        return home, calls, result.stderr

    for name, launcher, foreign in (
        ("healthy", 0, False),
        ("broken", 7, False),
        ("dangling", "dangling", False),
        ("foreign", None, True),
    ):
        _, calls, _ = case(name, launcher=launcher, foreign=foreign, expected=0 if name == "healthy" else 1)
        assert calls == "", (name, "must not overwrite existing installation")

    _, calls, _ = case("download-failed", expected=22, MOCK_DOWNLOAD_STATUS="22")
    assert "curl " in calls and "bash " not in calls
    _, calls, _ = case("install-failed", expected=7, MOCK_INSTALL_STATUS="7")
    assert "bash " in calls
    case("missing-launcher", expected=1, MOCK_NO_LAUNCHER="1")
    case("installed-broken", expected=1, MOCK_HEALTH_STATUS="7")
    home, calls, _ = case("success")
    assert (home / ".local/bin/hermes").exists()
    assert "--retry 3" in calls and "--connect-timeout 15" in calls
    assert "--non-interactive --skip-browser --skip-computer-use" in calls
    assert "--skip-setup" not in calls
    # Removing a successfully installed launcher triggers installation on the
    # next invocation, without resetting any chezmoi success/checkpoint state.
    (home / ".local/bin/hermes").unlink()
    retry_env = {
        **os.environ,
        "HOME": str(home),
        "PATH": str(bins),
        "TMPDIR": str(home / "temp"),
        "MOCK_LOG": str(home / "calls.log"),
    }
    subprocess.run(["/bin/sh", str(script)], env=retry_env, check=True, capture_output=True)
    assert (home / "calls.log").read_text().count("curl ") == 2
    assert list((home / "temp").iterdir()) == []

print("ok Hermes setup: gates, config effort, offline success/failure and retry")
