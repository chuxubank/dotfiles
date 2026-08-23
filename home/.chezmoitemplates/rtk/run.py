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
    return subprocess.run(cmd).returncode


def install(item):
    return rtk_init(item)


def uninstall(item):
    rtk_init(item, uninstall=True)
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
