def run_lifecycle(
    mode,
    integrations,
    binary,
    install,
    uninstall,
    cleanup,
    label,
    extra_teardown=None,
    uninstall_disabled=False,
):
    names = [item["tool"] for item in integrations]
    if mode == "teardown":
        print("󰯁 Teardown %s agent integrations" % label)
        if binary():
            for item in integrations:
                uninstall(item)
            if extra_teardown is not None:
                extra_teardown()
        cleanup(names, extras=True)
        return
    print("󰯁 Setup %s agent integrations" % label)
    if not binary():
        print("%s is not installed; removing leftover agent integrations" % label)
        cleanup(names, extras=True)
        return
    for item in integrations:
        if item["enabled"]:
            print("  init %s" % item["tool"])
            code = install(item)
            if code not in (0, None):
                sys.exit(code)
    disabled = [item for item in integrations if not item["enabled"]]
    if uninstall_disabled:
        for item in disabled:
            uninstall(item)
    for item in disabled:
        print("  remove %s" % item["tool"])
    if disabled:
        cleanup([item["tool"] for item in disabled], extras=False)
