{{- /* Shared RTK chezmoi script. Caller sets rtkMode to "setup" or "teardown". */ -}}
{{- $mode := dig "rtkMode" "" . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "rtk/run.py: rtkMode must be setup or teardown" -}}
{{- end -}}
{{- $ctx := . -}}
{{- $ints := dig "integrations" (list) (index $ctx.tools "rtk") -}}
{{- if eq (len $ints) 0 -}}
{{- fail "rtk: integrations is empty" -}}
{{- end -}}
{{- $payload := list -}}
{{- range $int := $ints -}}
  {{- $enabled := includeTemplate "tool/enabled" (merge (dict "tool" $int.tool) $ctx) | fromJson -}}
  {{- $payload = append $payload (dict
        "tool" $int.tool
        "args" (dig "args" (list) $int)
        "enabled" $enabled) -}}
{{- end -}}
#!/usr/bin/env python3

import shutil
import subprocess

{{ includeTemplate "rtk/cleanup.py" }}

INTEGRATIONS = json.loads({{ $payload | toJson | quote }})
MODE = {{ $mode | quote }}


def rtk_bin():
    return shutil.which("rtk")


def run_init(item, uninstall=False):
    cmd = [rtk_bin(), "init"] + list(item["args"])
    if uninstall:
        cmd.append("--uninstall")
    return subprocess.run(cmd).returncode


def setup():
    print("󰯁 Setup RTK agent integrations")
    if not rtk_bin():
        print("rtk is not installed; removing leftover agent integrations")
        remove_agents([item["tool"] for item in INTEGRATIONS])
        return
    for item in INTEGRATIONS:
        if item["enabled"]:
            print("  init %s" % item["tool"])
            if run_init(item) != 0:
                sys.exit(1)
    disabled = [item["tool"] for item in INTEGRATIONS if not item["enabled"]]
    for name in disabled:
        print("  remove %s" % name)
    if disabled:
        remove_agents(disabled)


def teardown():
    # Before package uninstall so `rtk init --uninstall` still has the binary.
    # File cleanup always runs: rtk's own uninstall leaves artifacts.
    print("󰯁 Teardown RTK agent integrations")
    if rtk_bin():
        for item in INTEGRATIONS:
            run_init(item, uninstall=True)
    remove_agents([item["tool"] for item in INTEGRATIONS])


if __name__ == "__main__":
    if MODE == "setup":
        setup()
    else:
        teardown()
