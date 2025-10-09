local wezterm = require("wezterm")
local act = wezterm.action

return {
  {
    key = "B",
    mods = "CTRL|SHIFT",
    action = wezterm.action.EmitEvent("toggle-opacity"),
  },
  {
    key = "l",
    mods = "CTRL|SHIFT|ALT",
    action = act.ShowLauncher,
  },
  {
    key = "w",
    mods = "CTRL|SHIFT|ALT",
    action = act.CloseCurrentPane({ confirm = true }),
  },
  {
    key = "`",
    mods = "CTRL|SHIFT",
    action = act.PaneSelect,
  },
}
