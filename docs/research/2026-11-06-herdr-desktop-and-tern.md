# Official Herdr desktop and Stencil Tern

**Date:** 2026-11-06 (date supplied by the parent; the available tools cannot execute `date +%F`, independently corroborated by Homebrew JSON's `generated_date`).  
**Question:** How should this repo declare official Herdr desktop and the Tern associated with omp's author, using the package-owner lifecycle?  
**Method:** Read the local lifecycle, package data and schemas first; inspect first-party product pages, GitHub README/source and Homebrew JSON/Ruby. No installation, application launch, or live agent configuration access. Versions below are observations, not proposed pins. Search summaries were discovery only. Source-check validation was attempted: Tern returned passages but no automated semantic verdict; Herdr's check failed to retrieve passages, so the already-fetched original cask JSON and Ruby were manually inspected instead. Follow-up searches encountered rate limits and some fetches failed.

> Later decision: `herdr-app` is owned by the existing `herdr` switch, with the cask zap paths on that tool. The separate-tool recommendation below is the original investigation.

## Recommendation

**Add official desktop as its own `herdr-app` tool, not another package owned by the currently disabled `herdr` switch. Reserve `tern` for Stencil's Tern, but leave it disabled and package-less until an authenticated first-party distribution can be inspected. Do not install tern.build's packages: that is a different product.** This is a researcher recommendation based on the product distinction and this repo's [one-switch/owner contract](../tool-lifecycle.md), [owner ADR](../adr/0003-owner-lifecycle.md), and [one-writer invariant](../../CONTEXT.md).

Proposed declaration in [tools.yaml](../../home/.chezmoidata/tools.yaml), if enabling Herdr desktop now:

```yaml
  herdr-app:
    when:
      enabled:
        os: [darwin]
      disabled:
        host_env: [ci]
    purge:
      - ".config/herdr-app/**"
      - when:
          enabled:
            os: [darwin]
        paths:
          - "Library/Preferences/dev.herdr.app.plist"

  tern:
    when: *disabled
```

There is no `remove` entry for either new tool: this proposal introduces no chezmoi-managed destination config. The Herdr paths come directly from the [official Homebrew cask](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/h/herdr-app.rb). The plist uses an exact command-object `paths` entry without `command`, avoiding an ignore on the shared Preferences parent; [the lifecycle](../tool-lifecycle.md) explicitly supports this. Omit all Tern purge paths: none was verified for **Stencil** Tern. Do not borrow `~/.tern` from the unrelated product.

Concrete package changes:

| Owning file | Recommended change |
|---|---|
| [casks.toml](../../home/.chezmoidata/packages/brew/casks.toml) | Add `{ name = "herdr-app", owner = "herdr-app" }`. No Tern cask yet. |
| [brews.toml](../../home/.chezmoidata/packages/brew/brews.toml) | No addition. Keep `{ name = "herdr", owner = "herdr" }` unchanged. No invented `tern` formula. |
| [taps.toml](../../home/.chezmoidata/packages/brew/taps.toml) | No new tap for official Herdr (`homebrew/cask`); no Tern trust entry until its package is verified. Keep existing `owo-network/brew` scoped to `trusted.cask = "herdrm"`, owner `herdr`. |
| [tools.yaml](../../home/.chezmoidata/tools.yaml) | Add the two entries above; preserve existing `herdr` state and cleanup. |

The macOS/non-CI condition follows the desktop-specific scoping used by nearby tools without introducing an arbitrary disk threshold or copying a model/version into configuration. **Architecture caveat:** the Herdr cask supports only arm64. The current [condition schema](../../schemas/tools.schema.json) has no architecture key; `os: darwin` alone cannot exclude Intel. Enable only on known Apple Silicon hosts, or retain `when: *disabled` until an explicit supported host allowlist is chosen. Do not pretend that the above condition makes Intel supported. [Homebrew cask JSON](https://formulae.brew.sh/api/cask/herdr-app.json).

**Keep herdrm declared and disabled with existing `herdr` for now.** Adding official desktop is not evidence that the user wants the other console removed. Do not silently turn `herdr` on: it currently controls the TUI formula, third-party console, tap, and managed `.config/herdr` files together. A future independent `herdrm` switch is a separate lifecycle decision, not required to install official desktop. These existing affiliations are direct local evidence in [tools.yaml](../../home/.chezmoidata/tools.yaml), [casks.toml](../../home/.chezmoidata/packages/brew/casks.toml), and [taps.toml](../../home/.chezmoidata/packages/brew/taps.toml).

If Stencil's first-party beta provides a verified cask, add its fully qualified name with `owner = "tern"` and its tap with only `trusted.cask = "<verified-token>"`, also `owner = "tern"`. Add a formula only if its CLI is separately needed and it does not duplicate the cask's command. The current [package schema](../../schemas/packages.schema.json) supports singular `trusted.cask` and `trusted.formula`; no schema extension is needed for one of each. Do not use whole-tap trust. If there is no cask but there is a stable authenticated app archive, use the existing Applications external mechanism, not a downloading `run_` script, per [AGENTS.md](../../AGENTS.md). Neither case is justified by the evidence currently available.

## Official Herdr: what is being installed

1. **Direct evidence, high confidence:** [herdr.dev](https://herdr.dev/) and [herdrdev/herdr-app README](https://github.com/herdrdev/herdr-app/blob/master/README.md) describe the official desktop for terminals and coding agents. The window is a client of **herdr-core**; core runs terminals independently of window lifetime. The [agent guide](https://github.com/herdrdev/herdr-app/blob/master/defaults/AGENTS.md) distinguishes `herdr-app` (window) from `hc` (core). This is not the already-declared `owo-network/brew/herdrm` package.

2. **Direct evidence, high confidence:** install with `brew install --cask herdr-app`, with no third-party tap. Observed [cask JSON](https://formulae.brew.sh/api/cask/herdr-app.json), generated 2026-11-06: version **0.1.13**, tap `homebrew/cask`, DMG `https://releases.herdr.dev/app/0.1.13/Herdr.dmg`, app `/Applications/Herdr.app`, linked executable `herdr-app`, `auto_updates: true`, arm64 requirement. [Cask Ruby](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/h/herdr-app.rb) independently matches those declarations. The [changelog](https://github.com/herdrdev/herdr-app/blob/master/CHANGELOG.md) dates 0.1.13 to **2026-11-04**.

3. **Direct evidence, high confidence:** [download page](https://herdr.dev/download/) offers an Apple Silicon DMG and `curl -fsSL https://releases.herdr.dev/app/install.sh | sh`. The [README](https://github.com/herdrdev/herdr-app/blob/master/README.md) says macOS release builds are Apple Silicon, Intel users can build from source; Linux releases are x86-64/ARM64 and require desktop/Vulkan; Windows releases are x64. The [shell installer](https://github.com/herdrdev/herdr-app/blob/master/distribution/install.sh) puts macOS app in `~/Applications/Herdr.app` and a launcher in `~/.local/bin`, unlike Homebrew's `/Applications` install. Do not combine these installation managers.

4. **Direct evidence with limitation:** the [cask Ruby](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/h/herdr-app.rb) says only `depends_on :macos`, with no explicit numeric minimum; [JSON](https://formulae.brew.sh/api/cask/herdr-app.json) advertises arm64 platforms including Big Sur. That is cask metadata, **not proof that the app's complete runtime works on every listed release**. A documented numeric application minimum was not verified; do not assert macOS 12/13 or another guessed floor.

5. **Direct evidence, high confidence:** [README Updates and privacy](https://github.com/herdrdev/herdr-app/blob/master/README.md#updates-and-privacy) says installed releases download updates in the background and switch on quit/reopen or update action; source builds do not self-update. Core keeps terminals running. The [download page](https://herdr.dev/download/) also explicitly says the app updates itself. Let the cask own initial installation; do not add a second updater script.

6. **Direct evidence plus interpretation, high confidence:** [formula JSON](https://formulae.brew.sh/api/formula/herdr.json), generated 2026-11-06, describes the **terminal multiplexer** at stable **0.9.5**, source `herdrdev/herdr`, executable `herdr`. The [desktop cask](https://formulae.brew.sh/api/cask/herdr-app.json) provides `herdr-app`, not `herdr` or `hc`, and declares no core formula dependency. The [desktop installer](https://github.com/herdrdev/herdr-app/blob/master/distribution/install.sh) separately installs `herdr-core`/`hc` if missing; the [README](https://github.com/herdrdev/herdr-app/blob/master/README.md) says the app can install/update an unusable core. **Interpretation:** desktop neither duplicates nor replaces the `herdr` formula's executable; do not remove that formula to resolve an imaginary binary collision, and do not assume the formula supplies core. App-managed core is a separate lifecycle side effect, not automatically Homebrew-owned.

7. **Direct evidence and bounded cleanup:** the [cask zap](https://github.com/Homebrew/homebrew-cask/blob/master/Casks/h/herdr-app.rb) names `~/.config/herdr-app` and `~/Library/Preferences/dev.herdr.app.plist`; the [download guide](https://herdr.dev/download/) places the app's agent guide under `~/.config/herdr-app/AGENTS.md`. These support the proposed purge. Do not move existing `.config/herdr/**` cleanup to desktop: that is the old tool's scope. Core runtime/service/bundle cleanup is not fully audited here. The [0.1.13 changelog](https://github.com/herdrdev/herdr-app/blob/master/CHANGELOG.md) says core is now its own macOS app, **Herdr Core**, but that alone does not establish its installed path or a safe uninstaller. Omit speculative core paths and do not claim desktop purge stops a core daemon or removes all session state.

## Tern: identity first, then the installation gap

**Yes: the requested Stencil Tern belongs to the same Stencil/Can Bölük project lineage as this repo's omp. No: tern.build does not.** Local [node.toml](../../home/.chezmoidata/packages/node.toml) installs `@oh-my-pi/pi-coding-agent`, owner `omp`. Its first-party [package.json](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/package.json) names **Stencil Labs, Inc.** as author and `can1357/oh-my-pi` as repository (observed version **18.17.0**). [GitHub's user record](https://api.github.com/users/can1357) identifies can1357 as **Can Bölük**; the [OMP README](https://github.com/can1357/oh-my-pi/blob/main/README.md) credits Can Bölük and Stencil Labs and acknowledges the original Pi by Mario Zechner. The [Stencil Tern page](https://scl.so/tern) calls Tern a Stencil product and demonstrates omp natively. This establishes shared authorship/organization, not a claim that one person wrote every component. **Support: direct evidence and identity interpretation; confidence high.**

### What the correct Tern is

The [first-party landing page](https://scl.so/tern) describes a Rust-native “neoterminal”: persistent daemon-backed sessions, a desktop workspace, iPhone/browser access, files and native blocks, and daemon commands including `tern daemon`, `tern remote serve`, `tern split`, `run`, and `capture`. It explicitly states **closed beta** and routes access through a Stencil-account waitlist. It also explicitly names the **Tern Surface Protocol**, by which programs describe UI that Tern renders natively. This is first-party protocol evidence; no digest is needed. **Support: direct evidence; confidence high about the published claims, not independent runtime validation.**

[OMP's browser documentation](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/browser.md#browser-modes) separately documents detection inside a Tern pane and visible browser picture-in-picture using native **WKWebView**, not Chromium. `app.tern: false` opts out; `app.tern: true` requires Tern. This is documented native integration, not evidence that installing Tern must rewrite OMP's provider/model configuration. The page does not establish the framing/transport details of the entire surface protocol; do not invent an in-band wire format. **Support: direct evidence; confidence high.**

### What can actually be declared today

The public [can1357/homebrew-tap README](https://github.com/can1357/homebrew-tap/blob/main/README.md) documents `brew install can1357/tap/omp`, **not Tern**. Its [complete tree](https://api.github.com/repos/can1357/homebrew-tap/git/trees/main?recursive=1), observed at commit `90d4d36567ea6c22a6420ce8decc15e56a4e18f5` with `truncated: false`, contains only `README.md`, `Formula`, and `Formula/omp.rb`. There is no Tern formula or cask in that observed tap. This is a bounded negative, not proof that no private beta distribution exists. The [landing page](https://scl.so/tern) exposes a waitlist rather than a public brew or archive installation instruction in the fetched content. **Support: direct evidence; confidence high for those sources, low for any claim about private access.**

Therefore the exact Tern cask/formula token, tap, desktop bundle name/path, downloadable release URL, minimum macOS version, arm64/Intel release matrix, updater behavior, and config/cache/runtime directories remain **unverified**. The first-party demo establishes a CLI and GUI but is not a package manifest. No public canonical Tern source repository or GitHub organization was established beyond the OMP repository's relationship to Stencil; do not invent `stencil-labs/tern` or turn `can1357/tap/omp` into `can1357/tap/tern`.

Whether Tern writes other agents' config or injects hooks is likewise **unknown**, not “no.” The inspected [Tern page](https://scl.so/tern) and [OMP browser docs](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/browser.md) do not provide a complete install/uninstall contract. Do not treat it as Magpie's config-switcher or invent a setup command. If verified beta documentation later shows hooks into another agent, declare that wiring in [integrations.yaml](../../home/.chezmoidata/integrations.yaml), as required by [the local lifecycle](../tool-lifecycle.md), rather than hiding cross-tool writes in `tools.yaml`.

### The unrelated Tern to reject

[tern.build/download](https://tern.build/download) and [Shubham-1994/homebrew-tern README](https://github.com/Shubham-1994/homebrew-tern/blob/main/README.md) document a different IDE, a Go/AppKit desktop, tap `shubham-1994/tern`, formula `tern`, cask `tern-desktop`, and state/worktrees in `~/.tern`. Its [desktop docs](https://tern.build/docs/desktop) identify its Go/AppKit implementation. Those names and paths must **not** be attributed to Can Bölük/Stencil's Rust-native Tern. Do not add them to this repo for the requested product. These primary sources were retained only to disambiguate the collision.

## Contradictions and missing evidence

- The original tern.build clue conflicts with the intended author. The two first-party product families are distinct; this note follows the parent's correction to Stencil Tern.
- No contradiction found between Herdr's README and cask: installer-managed `~/Applications` versus Homebrew-managed `/Applications` are different installation methods, not competing facts.
- Herdr's numeric macOS runtime minimum and complete app-installed core lifecycle remain unknown. The cask-only purge is intentionally incomplete for core.
- Stencil Tern remains blocked on a verified first-party beta installer/package and path inventory. Search rate limiting and fetch failures limit completeness; absence from one complete tap tree is not global absence.
- Rejected/deprioritized: nuts.nvirellia.im digests, social mirrors, aggregator posts, and vendor benchmark claims. None supplies installation or lifecycle evidence here.

## Next steps

1. Integrate only the verified Herdr cask/owner declaration after confirming Apple Silicon host scope. Inspect a signed downloaded bundle's deployment target if support for older macOS matters; do not launch against live config.
2. Obtain the Stencil beta install instructions via the official waitlist. Inspect its package/cask/archive, bundle metadata, path ownership and uninstall behavior before adding package or purge entries. Audit agent-config writers in a scratch HOME if needed.
3. After actual data edits, render the Brewfile and assert cask/owner filtering and scoped trust; run `make verify` without installs or product execution. This research-only change does not alter keyboard config or keybinding documentation.
