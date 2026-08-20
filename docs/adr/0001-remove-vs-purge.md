# Split dest cleanup into remove and purge

Turning a tool off used to list `/**` directory wipes in `remove`, so `.chezmoiremove` deleted login state, history, and caches together with managed config. The alternative was to stop deleting dest files entirely and rely on ignore, which would leave stale managed files in place.

`remove` is now the managed-file list and always runs when the tool is off. `purge` holds runtime data and runs only when `policies.purge_disabled_tools` is on. Default off: disabling a tool on a machine must not surprise-delete session data.
