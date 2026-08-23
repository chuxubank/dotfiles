{{- $mode := dig "mode" (dig "rtkMode" "" .) . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "rtk/run.py: mode must be setup or teardown" -}}
{{- end -}}
#!/usr/bin/env python3

import shutil
import subprocess

{{ includeTemplate "integrations/hooks.py" }}
{{ includeTemplate "rtk/cleanup.py" }}
{{ includeTemplate "integrations/loop.py" }}

INTEGRATIONS = json.loads({{ includeTemplate "integrations/payload" (merge (dict "owner" "rtk") .) | quote }})
MODE = {{ $mode | quote }}


def rtk_bin():
    return shutil.which("rtk")


def rtk_init(item, uninstall=False):
    cmd = [rtk_bin(), "init"] + list(item.get("args") or [])
    if uninstall:
        cmd.append("--uninstall")
    return subprocess.run(cmd, capture_output=True, text=True)


def _write_proc(proc):
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")


def install(item):
    proc = rtk_init(item)
    if proc.returncode in (0, None):
        _write_proc(proc)
        return 0
    err = (proc.stderr or "") + (proc.stdout or "")
    lowered = err.lower()
    if "no such file" in lowered or "not found" in lowered:
        detail = err.strip().splitlines()[-1] if err.strip() else "not found"
        print("  skip %s: %s" % (item["tool"], detail))
        return 0
    _write_proc(proc)
    return proc.returncode


def uninstall(item):
    proc = rtk_init(item, uninstall=True)
    _write_proc(proc)
    return 0


if __name__ == "__main__":
    run_lifecycle(
        MODE,
        INTEGRATIONS,
        rtk_bin,
        install,
        uninstall,
        remove_agents,
        "RTK",
    )
