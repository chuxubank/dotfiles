if clink.get_env("TERM_PROGRAM") == "WezTerm" then
    load(io.popen('starship init cmd'):read("*a"))()
end