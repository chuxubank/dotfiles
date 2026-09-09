{{- $mode := dig "mode" "" . -}}
{{- if ne $mode "teardown" -}}
{{- fail "orca/run.py: only teardown is supported" -}}
{{- end -}}
#!/usr/bin/env python3

{{ includeTemplate "integrations/hooks.py" }}
{{ includeTemplate "orca/cleanup.py" }}

INTEGRATIONS = json.loads({{ includeTemplate "integrations/payload" (merge (dict "owner" "orca") .) | quote }})


if __name__ == "__main__":
    print("󰯁 Teardown Orca agent integrations")
    remove_agents([item["tool"] for item in INTEGRATIONS], extras=True)
