;;; Directory Local Variables            -*- no-byte-compile: t -*-
;;; For more information see (info "(emacs) Directory Variables")

((js-mode . ((eval . (setf
                      (alist-get 'prettier-javascript apheleia-formatters)
                      '("apheleia-npx" "prettier" "--stdin-filepath" filepath "--parser=babel-flow" "--trailing-comma=es5"
                        (apheleia-formatters-js-indent "--use-tabs" "--tab-width")))))))
