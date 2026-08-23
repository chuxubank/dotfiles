{{- $mode := dig "mode" "" . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "termio/run.py: mode must be setup or teardown" -}}
{{- end -}}
#!/usr/bin/env python3

import shutil

{{ includeTemplate "integrations/hooks.py" }}
{{ includeTemplate "termio/cleanup.py" }}
{{ includeTemplate "integrations/loop.py" }}

INTEGRATIONS = json.loads({{ includeTemplate "integrations/payload" (merge (dict "owner" "termio") .) | quote }})
MODE = {{ $mode | quote }}


def termio_bin():
    return shutil.which("termio")


def install(item):
    return 0


def uninstall(item):
    return 0


if __name__ == "__main__":
    run_lifecycle(
        MODE,
        INTEGRATIONS,
        termio_bin,
        install,
        uninstall,
        remove_agents,
        "termio",
    )
