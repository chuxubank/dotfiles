{{- /* chezmoi:modify-template */ -}}
{{- "" -}}
{{- /* llm/gptel-backends owns the backend list. This file prints it as the
       saved value of cat-gptel-backends. The defcustom keeps that value
       instead of its standard fallbacks. Specs stay data: the module
       evaluates plist values only after gptel has loaded. */ -}}
{{- $gptel := includeTemplate "llm/gptel-backends" . | fromJson -}}
;;; -*- lexical-binding: t -*-
(load (cat-template-file "custom.el") nil 'nomessage)
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(datetime-timezone 'Asia/Shanghai)
 '(auth-source-save-behavior nil)
 '(smtpmail-smtp-server "smtp.qq.com")
 {{- if eq .host_env "aa" }}
 '(telega-docker-run-arguments "--platform linux/amd64 --userns=keep-id")
 '(telega-use-docker "podman")
 {{- else }}
 '(telega-docker-run-arguments "--platform linux/amd64")
 '(telega-use-docker "docker")
 {{- end }}
 {{- if eq .host_env "iv" }}
 '(cat-forge-alist
   '(("git.infinityparadise.com" "git.infinityparadise.com/api/v4"
      "git.infinityparadise.com" forge-gitlab-repository)))
 '(cat-gptel-forge-prs-prompt-file "prompt/iv-mr.yml.j2")
 {{- end }}
 {{- if eq .host_env "aa" }}
 '(logview-additional-timestamp-formats
   '(("Zscaler"
      (java-pattern . "yyyy-MM-dd HH:mm:ss.SSSSSS(Z)"))
{{- includeTemplate "emacs/logview/timestamp-formats.eld" . | nindent 5 }})
   t)
 '(logview-additional-level-mappings
   '(("Zscaler"
      (error "ERR")
      (warning "WRN")
      (information "INF")
      (debug "DBG"))
{{- includeTemplate "emacs/logview/level-mappings.eld" . | nindent 5 }})
   t)
 '(logview-additional-submodes
   '(("Zscaler"
      (format . "TIMESTAMP[IGNORED:THREAD] LEVEL MESSAGE")
      (levels . "Zscaler")
      (timestamp "Zscaler"))
     ("Luna"
      (format . "TIMESTAMP IGNORED LEVEL T: <<RX:THREAD:.+?>> NAME - MESSAGE")
      (levels . "Logback"))
{{- includeTemplate "emacs/logview/submodes.eld" . | nindent 5 }})
   t)
 {{- end }}
 {{- if eq .host_env "iv" }}
 '(logview-additional-level-mappings
   '(("IV"
      (error "ERROR")
      (warning "WARN")
      (information "INFO")
      (debug "DEBUG"))
{{- includeTemplate "emacs/logview/level-mappings.eld" . | nindent 5 }})
   t)
 '(logview-additional-submodes
   '(("IV"
      (format . "TIMESTAMP [LEVEL] [NAME] MESSAGE")
      (levels . "IV")
      (timestamp "ISO 8601 datetime + millis"))
{{- includeTemplate "emacs/logview/submodes.eld" . | nindent 5 }})
   t)
 {{- end }}
 '(cat-gptel-backends
   '{{ if $gptel.backends }}({{ range $i, $b := $gptel.backends }}{{ if $i }}
     {{ end }}({{ $b.symbol }} {{ $b.constructor }} {{ $b.name | quote }}
      :models nil
      :host {{ $b.host | quote }}
      :protocol {{ $b.protocol | quote }}
      :endpoint {{ $b.endpoint | quote }}{{ if hasKey $b "auth_path" }}
      :key (cat/gptel-api-key-from-pass
            {{ index $b "auth_path" | quote }}{{ if hasKey $b "auth_field" }} {{ index $b "auth_field" | quote }}{{ end }}){{ end }}
      :stream t){{ end }}){{ else }}nil{{ end }}
   nil nil "Resolved llm aliases; replaces the standard fallbacks")
 '(gptel-model-updater-model-metadata-file
   {{ joinPath .chezmoi.homeDir (index .path.cache "models-dev-api") | quote }})
{{- $filters := list -}}
{{- range $b := $gptel.backends -}}
  {{- if hasKey $b "include" -}}{{- $filters = append $filters $b -}}{{- end -}}
{{- end -}}
{{- if $filters }}
 '(gptel-model-updater-backend-filters
   '({{ range $i, $b := $filters }}{{ if $i }}
     {{ end }}({{ $b.name | quote }} :include {{ $b.include | quote }}){{ end }}))
{{- end }}
 '(gptel-model-updater-backends
   '({{ range $i, $b := $gptel.backends }}{{ if $i }}
     {{ end }}{{ if or (hasKey $b "cache_file") (hasKey $b "metadata_providers") }}({{ end }}{{ $b.symbol }}{{ if hasKey $b "metadata_providers" }} :providers ({{ join " " $b.metadata_providers }}){{ end }}{{ if hasKey $b "cache_file" }} :cache {{ $b.cache_file | quote }}{{ end }}{{ if or (hasKey $b "cache_file") (hasKey $b "metadata_providers") }}){{ end }}{{ end }}))
 '(gptel-model-updater-external-targets
   '((gptel-magit-backend gptel-magit-model "GPTel-Magit"{{ if $gptel.small_models }}
                          ({{ range $i, $m := $gptel.small_models }}{{ if $i }}
                           {{ end }}{{ $m | quote }}{{ end }}){{ end }})
     (gptel-forge-prs-backend gptel-forge-prs-model "GPTel-Forge-Prs"{{ if $gptel.small_models }}
                              ({{ range $i, $m := $gptel.small_models }}{{ if $i }}
                               {{ end }}{{ $m | quote }}{{ end }}){{ end }})))
 '(gptel-model-updater-models
   '({{ range $i, $m := $gptel.models }}{{ if $i }}
     {{ end }}{{ $m | quote }}{{ end }}))
 '(mouse-wheel-progressive-speed nil)
 '(cat-org-cliplink-title-replacements
   '(("_哔哩哔哩_bilibili\\'" "")))
 '(org-roam-mode-sections
   (list #'org-roam-backlinks-section #'org-roam-reflinks-section
         #'org-roam-unlinked-references-section) nil nil "Customized with use-package org-roam")
 '(safe-local-variable-values
   '((eval valign-mode nil) (org-highlight-latex-and-related)
     (org-blank-before-new-entry))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
