{{- $mode := dig "mode" "" . -}}
{{- if not (has $mode (list "setup" "teardown")) -}}
{{- fail "integrations/dispatch.py: mode must be setup or teardown" -}}
{{- end -}}
{{- $owners := includeTemplate "integrations/owners" (merge (dict "mode" $mode) .) | fromJson -}}
#!/usr/bin/env python3

RUNNERS = {
{{- range $owner := $owners }}
    {{ $owner | quote }}: {{ includeTemplate (printf "%s/run.py" $owner) (merge (dict "mode" $mode) $) | quote }},
{{- end }}
}


if __name__ == "__main__":
    for owner, source in RUNNERS.items():
        namespace = {"__name__": "__main__", "__file__": "<integration:%s>" % owner}
        exec(compile(source, namespace["__file__"], "exec"), namespace)
