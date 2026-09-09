# Split dest cleanup into remove and purge

Turning a tool off used to list `/**` directory wipes in `remove`, so `.chezmoiremove` deleted login state, history, and caches together with managed config. The alternative was to stop deleting dest files entirely and rely on ignore, which would leave stale managed files in place.

`remove` is now the managed-file list and always runs when the tool is off. `purge` holds runtime data and runs only when `policies.purge_disabled_tools` is on. The policy is explicit rather than implied by disabling a tool; this repository currently enables it, so disabled-tool runtime data is moved to Trash during apply.
