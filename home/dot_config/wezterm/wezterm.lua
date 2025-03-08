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

-- Modules
config.launch_menu = launch.launch_menu
config.default_prog = launch.default_prog
config.set_environment_variables = launch.set_environment_variables
config.keys = keys

-- and finally, return the configuration to wezterm
return config
