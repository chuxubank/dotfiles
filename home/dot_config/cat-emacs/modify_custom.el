{{- /* chezmoi:modify-template */ -}}

{{- $selected := includeTemplate "emacs/selected-packages" (dict "ctx" .) | fromJson -}}
{{- $vc := includeTemplate "package/items" (dict "ctx" . "path" (list "emacs" "vc")) | fromJson -}}
{{- $pinned := includeTemplate "emacs/pinned-packages" (dict "ctx" .) | fromJson -}}
{{- /* Fill package-selected-packages to fill-column like Emacs does:
       first token after "   '(", continuation lines indented 16 spaces,
       wrapping at 70 columns. */ -}}
{{- $selBody := includeTemplate "emacs/fill-list" (dict "items" $selected "width" 70 "first" "   '(" "indent" "                " "suffix" "))") -}}
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
 '(package-vc-selected-packages
   '(
     {{- range $p := $vc }}
     ({{ $p.name }} . (:url "{{ $p.url }}"{{ if hasKey $p "lisp_dir" }} :lisp-dir "{{ $p.lisp_dir }}"{{ end }}{{ if hasKey $p "branch" }} :branch "{{ $p.branch }}"{{ end }}))
     {{- end }}))
 '(safe-local-variable-values
   '((org-highlight-latex-and-related) (org-blank-before-new-entry))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
