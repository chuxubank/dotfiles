{{- /* chezmoi:modify-template */ -}}

{{- $selected := includeTemplate "emacs/selected-packages" (dict "ctx" .) | fromJson -}}
{{- $vc := includeTemplate "package/items" (dict "ctx" . "path" (list "emacs" "vc")) | fromJson -}}
{{- $pinned := includeTemplate "emacs/pinned-packages" (dict "ctx" .) | fromJson -}}
{{- /* Fill package-selected-packages to fill-column like Emacs does:
       first token after "   '(", continuation lines indented 16 spaces,
       wrapping at 70 columns. */ -}}
{{- $selBody := includeTemplate "emacs/fill-list" (dict "items" $selected "width" 70 "first" "   '(" "indent" 16 "suffix" "))") -}}
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
{{-   if eq $i 0 }}{{ $vcBody = printf "   '(%s" $e }}{{ else }}{{ $vcBody = printf "%s\n     %s" $vcBody $e }}{{ end -}}
{{- end -}}
{{- $vcBody = printf " '(package-vc-selected-packages\n%s))" $vcBody -}}
;;; -*- lexical-binding: t -*-
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(auth-source-save-behavior nil)
 '(mouse-wheel-progressive-speed nil)
 '(org-roam-mode-sections
   (list #'org-roam-backlinks-section #'org-roam-reflinks-section
         #'org-roam-unlinked-references-section) nil nil "Customized with use-package org-roam")
 '(package-pinned-packages
   '(
     {{- range $p := $pinned }}
     ({{ $p.name }} . "{{ $p.archive }}")
     {{- end }}))
 '(package-selected-packages
{{ $selBody }}
{{ $vcBody }}
 '(safe-local-variable-values
   '((org-highlight-latex-and-related) (org-blank-before-new-entry))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
