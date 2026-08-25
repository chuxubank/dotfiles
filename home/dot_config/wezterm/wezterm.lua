local wezterm = require("wezterm")
local theme = require("theme")
local launch = require("launch")
local keys = require("keys")

-- This table will hold the configuration.
local config = {}

-- In newer versions of wezterm, use the config_builder which will
-- help provide clearer error messages
if wezterm.config_builder then
  config = wezterm.config_builder()
end

-- Font
config.font_size = 14

-- UI
config.window_decorations = "RESIZE"
config.tab_bar_at_bottom = true
config.use_fancy_tab_bar = false
config.hide_tab_bar_if_only_one_tab = true
config.enable_scroll_bar = true
config.color_scheme = theme.color_scheme

-- Use a standalone local mux server so tabs, panes, and their processes can
-- survive closing the WezTerm GUI and be reattached on the next launch.
config.unix_domains = {
  {
    name = "unix",
  },
}
config.default_domain = "unix"
config.default_gui_startup_args = { "connect", "unix" }

-- Discover concrete Host entries (including Include files) from ~/.ssh/config.
-- WezTerm creates both SSH:<host> for a direct connection and SSHMUX:<host>
-- for attaching to a persistent remote WezTerm mux over SSH.
config.ssh_domains = wezterm.default_ssh_domains()
for _, domain in ipairs(config.ssh_domains) do
  -- All managed SSH targets are POSIX hosts. This lets direct SSH domains
  -- preserve the remote cwd when opening another tab or pane.
  domain.assume_shell = "Posix"
end

-- Keyboard
-- Kitty keyboard protocol lets apps distinguish Shift+Enter from Enter.
config.enable_kitty_keyboard = true
-- Match Ghostty's Alt mapping so Herdr sees Alt+0 and other Alt chords.
config.send_composed_key_when_left_alt_is_pressed = false
config.send_composed_key_when_right_alt_is_pressed = false

-- Modules
config.launch_menu = launch.launch_menu
config.default_prog = launch.default_prog
config.set_environment_variables = launch.set_environment_variables
config.keys = keys

-- and finally, return the configuration to wezterm
return config
