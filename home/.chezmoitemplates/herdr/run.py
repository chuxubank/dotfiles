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
    return subprocess.run(cmd, capture_output=True, text=True)


def install(item):
    proc = herdr_integration(item)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if proc.returncode in (0, None):
        return 0
    err = (proc.stderr or "") + (proc.stdout or "")
    if "not found" in err.lower():
        detail = err.strip().splitlines()[-1] if err.strip() else "not found"
        print("  skip %s: %s" % (item["tool"], detail))
        return 0
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return proc.returncode


def uninstall(item):
    proc = herdr_integration(item, uninstall=True)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")
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
