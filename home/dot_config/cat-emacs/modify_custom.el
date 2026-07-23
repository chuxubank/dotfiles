{{- /* chezmoi:modify-template */ -}}
{{- "" -}}
;;; -*- lexical-binding: t -*-
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
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
                           "OpenRouter:openai/gpt-oss-120b:free"))
     (gptel-forge-prs-backend gptel-forge-prs-model "GPTel-Forge-Prs"
                              ("IV:deepseek-v4-flash"
                               "OpenRouter:openai/gpt-oss-120b:free"))))
 '(gptel-model-updater-models
   '("IV:gpt-5.4"
     "IV:claude-opus-4-7"
     "IV:deepseek-v4-pro"
     "OpenRouter:auto"))
 '(mouse-wheel-progressive-speed nil)
 '(org-roam-mode-sections
   (list #'org-roam-backlinks-section #'org-roam-reflinks-section
         #'org-roam-unlinked-references-section) nil nil "Customized with use-package org-roam")
 '(safe-local-variable-values
   '((org-highlight-latex-and-related) (org-blank-before-new-entry))))
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
