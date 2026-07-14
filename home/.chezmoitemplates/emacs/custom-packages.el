{{- $selected := includeTemplate "emacs/selected-packages" (dict "ctx" .) | fromJson -}}
{{- $vc := includeTemplate "package/items" (dict "ctx" . "path" (list "emacs" "vc")) | fromJson -}}
{{- $pinned := includeTemplate "emacs/pinned-packages" (dict "ctx" .) | fromJson -}}
{{- /* Fill package-selected-packages to fill-column like Emacs does:
first token after "   '(", continuation lines indented 16 spaces,
wrapping at 70 columns. */ -}}
{{- $selBody := includeTemplate "emacs/fill-list" (dict "items" $selected "width" 70 "first" "   '(" "indent" 16 "suffix" ")") -}}
{{- /* Fill package-vc-selected-packages the same way: each element is a
plist (name :url URL [:lisp-dir DIR] [:branch B]) wrapped at 70
columns, continuation lines aligned under the first token. */ -}}
{{- $vcElems := list -}}
{{- range $p := $vc -}}
{{-   $toks := list ":url" (printf "%q" $p.url) -}}
{{-   if hasKey $p "lisp_dir" }}{{ $toks = concat $toks (list ":lisp-dir" (printf "%q" $p.lisp_dir)) }}{{ end -}}
{{-   if hasKey $p "branch" }}{{ $toks = concat $toks (list ":branch" (printf "%q" $p.branch)) }}{{ end -}}
{{-   $elem := includeTemplate "emacs/fill-list" (dict "items" $toks "width" 65 "first" (printf "(%s " $p.name) "indent" (add (len $p.name) 7) "suffix" ")") -}}
{{-   $vcElems = append $vcElems $elem -}}
{{- end -}}
{{- $vcBody := "" -}}
{{- range $i, $e := $vcElems -}}
{{-   if eq $i 0 }}{{ $vcBody = $e }}{{ else }}{{ $vcBody = printf "%s\n     %s" $vcBody $e }}{{ end -}}
{{- end -}}
{{ print " " }}'(package-pinned-packages
   '(
     {{- range $p := $pinned }}
     ({{ $p.name }} . "{{ $p.archive }}")
     {{- end }}))
 '(package-selected-packages
   {{ $selBody }})
 '(package-vc-selected-packages
   '({{ $vcBody }}))
{{- "" -}}
