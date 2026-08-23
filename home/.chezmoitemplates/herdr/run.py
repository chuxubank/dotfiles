{{- $mode := dig "mode" "" . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "herdr/run.py: mode must be setup or teardown" -}}
{{- end -}}
#!/usr/bin/env python3

import shutil
import subprocess

{{ includeTemplate "integrations/hooks.py" }}
{{ includeTemplate "herdr/cleanup.py" }}
{{ includeTemplate "integrations/loop.py" }}

INTEGRATIONS = json.loads({{ includeTemplate "integrations/payload" (merge (dict "owner" "herdr") .) | quote }})
MODE = {{ $mode | quote }}

HERDR_TARGETS = [
    "pi",
    "omp",
    "claude",
    "codex",
    "copilot",
    "devin",
    "droid",
    "kimi",
    "opencode",
    "kilo",
    "hermes",
    "qodercli",
    "cursor",
    "mastracode",
    "antigravity-cli",
    "grok",
]


def herdr_bin():
    return shutil.which("herdr")


def herdr_integration(item, uninstall=False):
    cmd = [herdr_bin(), "integration"]
    cmd.append("uninstall" if uninstall else "install")
    cmd.extend(item.get("args") or [])
    return subprocess.run(cmd).returncode


def install(item):
    return herdr_integration(item)


def uninstall(item):
    herdr_integration(item, uninstall=True)
    return 0


def extra_teardown():
    binary = herdr_bin()
    if not binary:
        return
    declared = set()
    for item in INTEGRATIONS:
        declared.update(item.get("args") or [])
    for target in HERDR_TARGETS:
        if target in declared:
            continue
        subprocess.run([binary, "integration", "uninstall", target])


if __name__ == "__main__":
    run_lifecycle(
        MODE,
        INTEGRATIONS,
        herdr_bin,
        install,
        uninstall,
        remove_agents,
        "herdr",
        extra_teardown=extra_teardown,
        uninstall_disabled=True,
    )
