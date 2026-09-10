{{- $phase := dig "phase" "" . -}}
{{- if not (has $phase (list "before" "after")) -}}
{{- fail "plugins/dispatch.py: phase must be before or after" -}}
{{- end -}}
{{- $managers := includeTemplate "plugins/managers" (merge (dict "phase" $phase) .) | fromJson -}}
#!/usr/bin/env python3
# Reconciliation epoch: {{ includeTemplate "week" . }}

import json

MANAGERS = [
{{- range $manager := $managers }}
    json.loads({{ includeTemplate "plugins/payload" (merge (dict "manager" $manager) $) | quote }}),
{{- end }}
]

{{ includeTemplate "plugins/engine.py" }}


if __name__ == "__main__":
    for manager in MANAGERS:
        reconcile(manager)
