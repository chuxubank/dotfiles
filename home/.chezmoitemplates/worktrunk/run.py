{{- $mode := dig "mode" "" . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "worktrunk/run.py: mode must be setup or teardown" -}}
{{- end -}}
#!/usr/bin/env python3

import os
import shutil
import subprocess

{{ includeTemplate "integrations/hooks.py" }}
{{ includeTemplate "integrations/loop.py" }}

INTEGRATIONS = json.loads({{ includeTemplate "integrations/payload" (merge (dict "owner" "worktrunk") .) | quote }})
MODE = {{ $mode | quote }}

# `wt config plugins pi` resolves the hook via PI_CODING_AGENT_DIR, then
# PI_CONFIG_DIR (default .omp). Named PI_PROFILE/OMP_PROFILE ignore the
# agent-dir override. https://github.com/max-sixty/worktrunk/pull/3594
PI_ENV = {
    "pi": {
        "PI_CODING_AGENT_DIR": str(HOME / ".pi" / "agent"),
        "PI_PROFILE": None,
        "OMP_PROFILE": None,
    },
    "omp": {
        "PI_CODING_AGENT_DIR": None,
        "PI_CONFIG_DIR": None,
        "PI_PROFILE": None,
        "OMP_PROFILE": None,
    },
}


def wt_bin():
    return shutil.which("wt")


def wt_env(item):
    env = os.environ.copy()
    for key, value in PI_ENV.get(item["tool"], {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def wt_plugins(item, uninstall=False):
    cmd = [wt_bin(), "config", "plugins"] + list(item.get("args") or [])
    cmd.append("uninstall" if uninstall else "install")
    cmd.append("--yes")
    return subprocess.run(cmd, capture_output=True, text=True, env=wt_env(item))


def _write_proc(proc):
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")


def _skip(err):
    text = err.lower()
    return (
        "not found" in text
        or "no such file" in text
        or "unrecognized subcommand" in text
    )


def install(item):
    proc = wt_plugins(item)
    if proc.returncode in (0, None):
        _write_proc(proc)
        return 0
    err = (proc.stderr or "") + (proc.stdout or "")
    if _skip(err):
        detail = err.strip().splitlines()[-1] if err.strip() else "not found"
        print("  skip %s: %s" % (item["tool"], detail))
        return 0
    _write_proc(proc)
    return proc.returncode


def uninstall(item):
    proc = wt_plugins(item, uninstall=True)
    _write_proc(proc)
    return 0


def remove_agents(agents, extras=False):
    return


if __name__ == "__main__":
    run_lifecycle(
        MODE,
        INTEGRATIONS,
        wt_bin,
        install,
        uninstall,
        remove_agents,
        "Worktrunk",
        uninstall_disabled=True,
    )
