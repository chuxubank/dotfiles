{{- $mode := dig "mode" "" . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "integrations/dispatch.py: mode must be setup or teardown" -}}
{{- end -}}
{{- $owners := includeTemplate "integrations/owners" (merge (dict "mode" $mode) .) | fromJson -}}
#!/usr/bin/env python3

import json

SPECS = [
{{- range $owner := $owners }}
    json.loads({{ includeTemplate "integrations/payload" (merge (dict "owner" $owner) $) | quote }}),
{{- end }}
]
MODE = {{ $mode | quote }}
AGENT_ROOTS = json.loads({{ default dict .integration_agents | toJson | quote }})

{{ includeTemplate "integrations/engine.py" }}


if __name__ == "__main__":
    for spec in SPECS:
        reconcile(spec, MODE, AGENT_ROOTS)
