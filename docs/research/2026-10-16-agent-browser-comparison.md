# Agent browsers for coding agents on macOS

**Date:** 2026-10-16  
**Question:** Besides ego lite, which agent-browser tools are actually useful from Cursor, Codex, or Claude Code on this Mac, and how do they differ?  
**Method:** Official READMEs, first-party docs, and the ego-browser skill. Local facts come from chezmoi data files and from commands run on this machine the same day. Vendor comparison grids and blogs are not used as evidence about other products.

## Recommendation

Keep the split this machine already has. Chrome DevTools MCP, started as `bunx chrome-devtools-mcp@latest --no-usage-statistics --autoConnect`, is the tool for the daily Chrome: the coding agent calls DevTools tools, Chrome 144+ must already be running with remote debugging allowed, and the person approves the connection in that same browser. `agent-browser` 0.39.0 is the tool for a separate automation browser. Chezmoi installs the CLI with bun, `agent-browser install` has already placed Chrome for Testing 155.0.8059.39 under `~/.agent-browser/browsers`, and the default session is headless unless the agent passes `--headed`.

Leave ego lite uninstalled. It is the only product here whose own skill describes one Chromium app, the user's ego lite profile, a visible agent cursor, and an explicit `handOff()` back to the person. That is a new daily browser plus a DMG and a GUI onboarding step, and neither configured tool is missing a browser on this Mac.

Leave the Browser Use Python library and Browser Harness off the default path. The library's `Agent.run()` is its own model loop. The Browser Use CLI, which the docs say is backed by Browser Harness, is the variant aimed at Claude Code, Codex, and Cursor, and its default is to attach to the running Chrome the DevTools MCP already uses. Playwright MCP is already listed in `home/.chezmoidata/mcp.yaml` with `when.disabled: true`; its README tells coding agents to prefer the Playwright CLI, and enabling the MCP would add a third general browser next to `agent-browser`. Stagehand, Browserbase, Skyvern, and Lightpanda are real agent-browser products. None of them replaces the local pair above for ordinary coding-agent work on this Mac.

## This machine

Checked 2026-10-16:

- `agent-browser` resolves to `/Users/misaka/.bun/bin/agent-browser`, version 0.39.0, macOS aarch64. `agent-browser doctor --json` reported Chrome for Testing 155.0.8059.39, no active daemon, and a headless launch to `about:blank` in 0.93s. `AI_GATEWAY_API_KEY` is unset, so the doctor marked the `chat` command disabled.
- Chezmoi owns that install: bun package `agent-browser` in `home/.chezmoidata/packages/node.toml`, tool `agent-browser` in `home/.chezmoidata/tools.yaml` (darwin/linux/windows, disabled on `host_env: ci`), and `home/.chezmoiscripts/run_onchange_after_101_setup-agent-browser.sh.tmpl` runs `agent-browser install`. The skill source `vercel-labs/agent-browser` is in `home/.chezmoidata/skills/providers.yaml`.
- Chrome DevTools MCP is enabled in `home/.chezmoidata/mcp.yaml` except for the `opencode` tool. The stdio command is `bunx` with args `chrome-devtools-mcp@latest`, `--no-usage-statistics`, `--autoConnect`.
- Playwright MCP is in the same file and `when.disabled: true`. The command would be `bunx -y @playwright/mcp@latest`.
- `home/.chezmoidata/plugins/codex.yaml` lists `browser-use` with source `browser-use@openai-bundled`. What that bundled plugin does is unverified below.
- The ego-browser skill source `citrolabs/ego-lite` is declared for darwin and disabled on `host_env: ci`. `ego-browser` is not on `PATH`. No app whose name matches ego or lite is in `/Applications` or `~/Applications`.

## Comparison

| Tool | What it is | Which browser | Who runs the loop | Person can watch | Headless |
|---|---|---|---|---|---|
| [ego lite](https://lite.ego.app/) | macOS Chromium app plus `ego-browser` CLI | Its own profile; onboarding can import Chrome data | Coding agent runs Node scripts. No product model loop in the skill | Same app. `handOff()` / `waitForControl()` | The skill describes a visible browser |
| [agent-browser](https://github.com/vercel-labs/agent-browser) | Rust CLI, optional stdio MCP, local dashboard | Its own Chrome for Testing by default. `--auto-connect` / `--cdp` attach to a running Chrome. `--profile <name>` copies a Chrome profile | Coding agent calls the CLI or MCP. `chat` is a separate gateway model | `--headed` shows a window. Dashboard shows a live viewport. No handoff API in the README | Headless unless `--headed` |
| [browser-use library](https://github.com/browser-use/browser-use) | Python library (`uv add browser-use`) | Local browser, system Chrome profile, or Browser Use Cloud | `Agent.run()` uses the library's model | Cloud V4 documents a live-view takeover. Local window behavior is unverified | Unverified for the local default |
| [Browser Use CLI / Harness](https://docs.browser-use.com/open-source/browser-use-cli) | CLI plus skill. Docs: CLI is backed by [Browser Harness](https://github.com/browser-use/browser-harness) | Default: running Chrome over CDP, including existing tabs and logins. Cloud and raw CDP are optional | Coding agent runs Python through the CLI | Same Chrome, but the skill avoids bringing the tab forward | Attaches to the user's Chrome; it does not launch a separate headless app |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | stdio MCP around Playwright | Its own profile, or an existing Chrome/Edge via the Playwright extension or `--cdp-endpoint` | Coding agent calls MCP tools | Headed window by default. Extension mode asks which tab. `browser_annotate` waits for drawn marks | `--headless` opts in. Headed is the default |
| [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) | stdio MCP (Puppeteer) plus a CLI | Own profile, or `--autoConnect` to running Chrome 144+ | Coding agent calls MCP tools | With `--autoConnect`, the same Chrome, after an Allow dialog | `--headless` defaults to false |
| [Stagehand](https://github.com/browserbase/stagehand) | TypeScript / Python / Go SDK, plus a hosted MCP | Local Chrome with a `userDataDir`, or a Browserbase cloud browser | `act` / `observe` / `extract` call Stagehand's model. Page methods are ordinary driver calls | Unverified for the local window | Unverified |
| [Browserbase](https://docs.browserbase.com/introduction) | Cloud platform and hosted MCP | Cloud browsers | Depends on the caller. The platform also offers models | Cloud live view is a Browserbase/Stagehand feature, not a local window | Remote browser |
| [Skyvern](https://github.com/Skyvern-AI/skyvern) | Python service, local UI, Playwright-style SDK | Its own browser, Skyvern Cloud, or CDP to local Chrome | Skyvern's agents (`run_task`, `page.act`) | Local UI at port 8080. CDP mode uses the existing Chrome | Not stated as the default |
| [Lightpanda](https://github.com/lightpanda-io/browser) | Zig headless browser, CDP server, `lightpanda mcp`, and `lightpanda agent` | Its own engine | `lightpanda mcp`: the coding agent. `lightpanda agent`: Lightpanda's model | No window. It is headless by design | Headless |

## ego lite / ego-browser

ego lite is a macOS Chromium app. The site calls it the browser that replaces daily Chrome and the agent's Chromium, and says bookmarks, history, cookies, and passwords stay on the computer. The installed skill is the control contract: the `ego-browser` command comes from the app, agents run `ego-browser nodejs` scripts against TaskSpace and Page APIs, and those scripts are not Playwright. One task space is reused across rounds. The agent can `handOff()` when the person must act, then resume the same space; `finish()` closes agent pages. Permission prompts stay with the person. A visible agent cursor can be labeled from pointer actions.

Install is a DMG into `/Applications` (or `~/Applications`), a quarantine strip, and a GUI onboarding step that registers `ego-browser` on `PATH`, usually `~/.local/bin`. The skill's install script is macOS-only. Other platforms are told to download from the site. Profiles are ego lite profiles; the skill says not to pick one unless the user asks. Onboarding can import data from Chrome. This is ego lite's browser, not an attachment to a running Chrome window.

It fits a person who wants one browser they also live in, with logins in that profile and a real handoff. It is a poor fit on this Mac today: the app is absent, the work already has a daily Chrome plus a separate automation Chrome, and adding it means Gatekeeper, onboarding, and a second place to be logged in.

Sources: [lite.ego.app](https://lite.ego.app/), skill `SKILL.md` and `references/install.md` under the local ego-browser skill.

## Vercel agent-browser

The README calls it a browser-automation CLI for AI agents: a native Rust binary, with npm, Homebrew, Cargo, or a from-source build. `agent-browser install` downloads Chrome for Testing. The daemon does not need Node or Playwright. This machine's copy is the bun global package, and `doctor` shows the Chrome for Testing binary above.

The coding agent issues commands (`open`, `snapshot`, `click @e2`, `fill`) or starts `agent-browser mcp` over stdio. The default MCP profile is `core`. An optional `chat` command and the dashboard's AI tab send natural language through the Vercel AI Gateway; that path is off here because the gateway key is unset.

Default browsing is headless Chrome for Testing. `--headed` shows a window on the interactive desktop. `agent-browser dashboard start` serves a local page on port 4848 with JPEG frames and a command feed. The README does not describe yielding that window to the person the way ego's `handOff()` does. `--confirm-interactive` can prompt on a TTY.

Login state has several different mechanisms. `--profile <name>` copies an existing Chrome profile to a temp directory as a read-only snapshot and does not write back to the original profile. A path argument is a persistent profile of agent-browser's own. `--auto-connect` discovers a running Chrome; the installed help text describes it as a way to reuse auth state, and the README also uses it as a live CDP attachment shared across sessions. `--cdp` is the explicit port or WebSocket. `--session` plus `--restore` saves cookies and localStorage under `~/.agent-browser/sessions/`.

It is the right local tool when a coding agent should click through a site without touching the daily Chrome, including batch commands, refs, and a headed window or dashboard when someone wants to watch. It is a poor daily browser, and pointing `--auto-connect` at the same Chrome as Chrome DevTools MCP duplicates the attachment this machine already configured. `--engine lightpanda` can swap in Lightpanda; that engine is still the experimental alternative, with `chrome` as the default.

Sources: [vercel-labs/agent-browser README](https://github.com/vercel-labs/agent-browser/blob/HEAD/README.md), and `agent-browser --help` / `agent-browser doctor --json` on this machine.

## Browser Use, the Python library

The README describes an open-source browser agent, MIT licensed, installed with `uv add browser-use` on Python 3.11 or newer. The quickstart constructs `Agent(task=..., llm=...)` and calls `agent.run()`. The library supplies the system prompt. The model can be a provider wrapper such as `ChatOpenAI` or Browser Use's own `ChatBrowserUse` with `BROWSER_USE_API_KEY`. `Browser(use_cloud=True)` sends the browser to Browser Use Cloud; the default snippet does not.

`Browser.from_system_chrome()` is the documented way to reuse a local Chrome profile, cookies, and extensions. The real-browser page says Chrome may need to be fully closed first, and it lists the macOS executable and `~/Library/Application Support/Google/Chrome`. That is launching Chrome with the user's profile directory, which is a different operation from attaching to an already-open window.

The library is a fit when an application should contain the agent: custom tools, structured output, a chosen model, local or cloud browser. It is a poor fit for Cursor, Codex, or Claude Code, because those products already are the agent. The company's own product map says to use the CLI when an existing coding agent needs a browser, and the library when you want to run and customize the Browser Use agent in your own code. Hosted V4 is a third mode: Browser Use runs both the agent and the browser, and the cloud human-in-the-loop guide opens a `live_view_url`, lets a person take over, then continues the same session. That takeover is documented for the cloud SDK, not shown in the local `Agent` quickstart.

Sources: [browser-use README](https://github.com/browser-use/browser-use/blob/main/README.md), [which product](https://docs.browser-use.com/cloud/which-product), [real browser](https://docs.browser-use.com/open-source/customize/browser/real-browser), [human in the loop](https://docs.browser-use.com/cloud/agent/human-in-the-loop).

## Browser Use CLI and Browser Harness

The docs page titled Browser Use CLI says `browser-use` gives coding agents direct browser control and is backed by Browser Harness. Install is `uv tool install browser-use`. The agent passes Python into the CLI (`new_tab(...)`, `page_info()`). The default local flow attaches to the running Chrome or Chromium over CDP and keeps that browser's tabs, cookies, extensions, and logins. Cloud browsers and an arbitrary CDP endpoint are the other two modes. The README's related-repo table describes Browser Harness as the CLI for giving agents control of the user's browser, and its setup prompt targets Claude Code, Codex, and Cursor.

The Harness skill tells the agent to open a new tab for a task, then reuse it, and not to call `activate_tab()` unless the user asks to see that tab. Screenshots and CDP input are specified to work in the background. One local daemon is one connection to the whole Chrome instance. On macOS, if Chrome reports `permission-blocked`, `browser-harness mac-approve` handles the Allow sheet and needs Accessibility permission for the app that launched the CLI. The first remote-debugging checkbox at `chrome://inspect/#remote-debugging` is a manual step.

This is the Browser Use piece that matches a coding agent. On this Mac it overlaps Chrome DevTools MCP's `--autoConnect`: both want the same running Chrome and a user permission. It is a poor addition unless the Python-over-CDP skill is doing something the DevTools tools are not. It is also a poor fit for a clean automation profile, because the documented default is the user's Chrome rather than a private one.

Sources: [Browser Use CLI](https://docs.browser-use.com/open-source/browser-use-cli), [browser-harness README](https://github.com/browser-use/browser-harness/blob/main/README.md), [install.md](https://github.com/browser-use/browser-harness/blob/main/install.md), [SKILL.md](https://github.com/browser-use/browser-harness/blob/main/SKILL.md).

## Playwright MCP

`@playwright/mcp` is an MCP server. The README's standard config is `npx @playwright/mcp@latest`. Requirements are Node.js 18 or newer and an MCP client, including Cursor. The server is built so a model can act from accessibility snapshots instead of screenshots. `--headless` exists; headed is the default. An idle headed browser is not closed by the default idle timeout.

The User profile section says a persistent profile is the default, on macOS at `~/Library/Caches/ms-playwright/mcp-{channel}-{workspace-hash}`, so projects do not share cookies. The same README's `--user-data-dir` row says that omitting the flag creates a temporary directory. Those two sentences disagree; the concrete cache path is the more specific claim, and `--isolated` is the documented way to discard state when the browser closes. A persistent profile can be used by only one browser at a time.

The person's existing Chrome is opt-in. `--extension` plus the Playwright Chrome extension connects to tabs in the default profile; the first interaction asks which tab, and several clients can be separated into tab groups. `--cdp-endpoint` connects to a CDP browser. `browser_annotate`, behind `--caps=devtools`, opens a dashboard and waits for the person to draw on the page. That is a narrow intervention, not a general handoff.

The same README says coding agents may be better served by [Playwright CLI and skills](https://github.com/microsoft/playwright-cli) because CLI calls avoid loading large tool schemas and accessibility trees. This note does not review that CLI. Playwright MCP is a reasonable accessibility-snapshot MCP with a persistent per-workspace profile. It is a poor thing to enable here while `agent-browser` already covers coding-agent browser commands and the MCP entry is explicitly disabled.

Source: [microsoft/playwright-mcp README](https://github.com/microsoft/playwright-mcp/blob/main/README.md), [Playwright extension README](https://github.com/microsoft/playwright/blob/main/packages/extension/README.md).

## Chrome DevTools MCP

The README describes an MCP server, plus a CLI, that lets a coding agent control and inspect a live Chrome for automation, debugging, and performance traces. It uses Puppeteer and supports Google Chrome and Chrome for Testing. The documented client config is `npx -y chrome-devtools-mcp@latest`. Node.js LTS, current stable Chrome, and npm are the requirements. This machine uses bunx, adds `--no-usage-statistics`, and adds `--autoConnect`.

Without `--autoConnect`, the server starts Chrome on its own profile, `$HOME/.cache/chrome-devtools-mcp/chrome-profile` on macOS, reused across runs and limited to one browser at a time. `--headless` defaults to false, so that launched Chrome has a window. `--isolated` uses a temporary profile instead.

`--autoConnect` is the other mode, and it is the one configured here. It needs Chrome 144 or newer, remote debugging turned on at `chrome://inspect/#remote-debugging`, and the user to start Chrome. The server connects to the default profile if several are open, can see all windows of that profile, and shows an Allow dialog. The advanced-usage page describes this as the way to share state between manual testing and agent-driven testing, including sites that refuse a WebDriver-launched browser. The README also says the server can read and modify any data in that browser, so a daily profile is a wide permission.

It is the right tool for debugging a page, reading network and console, recording a performance trace, or continuing from a login that already exists in daily Chrome. It is a poor isolated sandbox: `--autoConnect` is the daily browser, and the dedicated-profile mode is a second Chrome the user did not ask to live in. `--slim` reduces the server to navigation, script, and screenshot tools; the full server is larger than a snapshot-and-click CLI.

Sources: [chrome-devtools-mcp README](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/README.md), [configuration](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md), [advanced usage](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/advanced-usage.md).

## Stagehand

The Stagehand README calls it the SDK for browser agents. Local install is `pnpm add @browserbasehq/stagehand`, `pip install stagehand`, or a Go module, and local runs need Chrome. The sample launches `localBrowser` with a `userDataDir` so cookies survive, then mixes Playwright-style `page.locator` calls with `observe`, `act`, and `extract`. Those three call a configured model. The README also documents a hosted MCP at `https://mcp.browserbase.com/mcp` that exposes `navigate`, `act`, `observe`, and `extract` to Claude Code, Cursor, and Codex with a Browserbase API key and no local browser.

Stagehand fits application code that wants natural-language actions and a model chosen by the SDK, locally or on Browserbase. It is a poor default for this Mac's coding agents: `act` spends a second model call, the hosted MCP is a cloud browser, and `agent-browser` plus Chrome DevTools MCP already cover local control. The README does not say whether the local browser is headed.

Source: [browserbase/stagehand README](https://github.com/browserbase/stagehand/blob/main/README.md).

## Browserbase

Browserbase's introduction calls it the platform for building and deploying agents that browse the web: cloud browsers, search, page fetch, a sandbox, and model access under one API key. Stagehand is the SDK that points a script at `browserbase.launch()`. The hosted MCP above is the coding-agent entry, and it does not drive the Chrome installed on this Mac.

Use it for remote, parallel, or stealth browsers. Skip it for local logged-in work that Chrome DevTools MCP or a headed `agent-browser` session can already see.

Source: [docs.browserbase.com/introduction](https://docs.browserbase.com/introduction), Stagehand README as above.

## Skyvern

The Skyvern README presents a system that automates browser workflows with LLMs and computer vision, plus a Playwright-compatible SDK (`page.act`, `page.extract`, `page.agent.run_task`) and a no-code UI. Local setup is `pip install "skyvern[all]"` and `skyvern quickstart`, with SQLite by default, or Docker Compose for Postgres, API, and UI at `http://localhost:8080`. It can attach to an existing Chrome after remote debugging is enabled at `chrome://inspect/#remote-debugging`, including a cloud tunnel onto the local browser.

Skyvern fits a workflow product that plans and executes its own tasks. It is a poor drop-in for a coding agent that should keep the loop, and the local service is a heavier install than a CLI or MCP on a machine that already has both.

Source: [Skyvern-AI/skyvern README](https://github.com/Skyvern-AI/skyvern/blob/main/README.md).

## Lightpanda

The Lightpanda README describes a headless browser written in Zig for agents and automation, not a Chromium fork. macOS install is Homebrew (`brew install lightpanda-io/browser/lightpanda`) or a nightly aarch64 binary. It serves CDP for Puppeteer, has `lightpanda mcp` for a coding agent, and `lightpanda agent` for its own model loop. `agent-browser --engine lightpanda` can point the already installed CLI at that engine. The README's own crawler write-up claims about 16× less peak memory and 9× faster execution than headless Chrome on 100 pages; this note did not rerun that benchmark.

Lightpanda fits high-volume headless fetches and CDP automation where Chromium is too heavy. It is a poor fit for logged-in sites, extensions, or a window a person can click.

Source: [lightpanda-io/browser README](https://github.com/lightpanda-io/browser/blob/main/README.md).

## Unverified

- What Codex's `browser-use@openai-bundled` plugin implements. The source string is in `home/.chezmoidata/plugins/codex.yaml`. No matching plugin files turned up in a search under `~/.codex`. The same file also lists `browser@openai-bundled` and `chrome@openai-bundled`, which this note does not describe.
- Whether the Browser Use Python library shows a window by default. The quickstart says the agent opens a browser and does not say headed or headless.
- Whether Stagehand's `localBrowser.launch()` is headed.
- Playwright MCP's persistent-profile paragraph and its `--user-data-dir` flag description disagree, as noted above. Behavior was not executed.
- Playwright CLI, mentioned only because the Playwright MCP README points coding agents at it.
- ego lite's site publishes a feature grid against extensions, cloud browsers, CLIs, and other AI browsers. Those cells are not used as facts about the other tools.
- No task-success rates were measured. Lightpanda's 16× / 9× figures are the project's own benchmark claim.
