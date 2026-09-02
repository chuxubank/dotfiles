{{- /* chezmoi:modify-template */ -}}
{{- "" -}}
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
{{- includeTemplate "emacs/logview/timestamp-formats" . }})
   t)
 '(logview-additional-level-mappings
   '(("Zscaler"
      (error "ERR")
      (warning "WRN")
      (information "INF")
      (debug "DBG"))
{{- includeTemplate "emacs/logview/level-mappings" . }})
   t)
 '(logview-additional-submodes
   '(("Zscaler"
      (format . "TIMESTAMP[IGNORED:THREAD] LEVEL MESSAGE")
      (levels . "Zscaler")
      (timestamp "Zscaler"))
     ("Luna"
      (format . "TIMESTAMP IGNORED LEVEL T: <<RX:THREAD:.+?>> NAME - MESSAGE")
      (levels . "Logback"))
{{- includeTemplate "emacs/logview/submodes" . }})
   t)
 {{- end }}
 {{- if eq .host_env "iv" }}
 '(logview-additional-level-mappings
   '(("IV"
      (error "ERROR")
      (warning "WARN")
      (information "INFO")
      (debug "DEBUG"))
{{- includeTemplate "emacs/logview/level-mappings" . }})
   t)
 '(logview-additional-submodes
   '(("IV"
      (format . "TIMESTAMP [LEVEL] [NAME] MESSAGE")
      (levels . "IV")
      (timestamp "ISO 8601 datetime + millis"))
{{- includeTemplate "emacs/logview/submodes" . }})
   t)
 {{- end }}
 '(gptel-model-updater-backends
   '(gptel--gemini
     {{- if eq .host_env "iv" }}
     (gptel--iv :providers (all))
     (gptel--openai :providers (all))
     (gptel--anthropic :providers (all))
     {{- end }}
     {{- if has "llm" .roles }}
     gptel--llama gptel--mlx gptel--ollama
     {{- end }}
     gptel--openrouter))
 '(gptel-model-updater-external-targets
   '((gptel-magit-backend gptel-magit-model "GPTel-Magit"
                          ("IV:deepseek-v4-flash"
                           "OpenRouter:openrouter/free"))
     (gptel-forge-prs-backend gptel-forge-prs-model "GPTel-Forge-Prs"
                              ("IV:deepseek-v4-flash"
                               "OpenRouter:openrouter/free"))))
 '(gptel-model-updater-models
   '("IV:gpt-5.6-sol"
     "IV:claude-opus-5"
     "IV:deepseek-v4-pro"
     "OpenRouter:auto"))
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
{{- if eq .host_env "iv" }}
(with-eval-after-load 'gptel
  (setq gptel--iv
        (gptel-make-openai "IV"
          :models '()
          :host "llm.invalley.co"
          :protocol "http"
          :key (cat/gptel-api-key-from-pass
                "Work/IV/LLM" "default-auth-token")
          :stream t)
        gptel--openai
        (gptel-make-openai "OpenAI"
          :host "llm.invalley.co"
          :protocol "http"
          :key (cat/gptel-api-key-from-pass
                "Work/IV/LLM" "codex-auth-token")
          :stream t)
        gptel--anthropic
        (gptel-make-anthropic "Anthropic"
          :host "llm.invalley.co"
          :protocol "http"
          :key (cat/gptel-api-key-from-pass
                "Work/IV/LLM" "cc-auth-token")
          :stream t)))
{{- end }}
