local wezterm = require("wezterm")

return {
  {
    key = "l",
    mods = "ALT",
    action = wezterm.action.ShowLauncher,
  },
  {
    key = "w",
    mods = "CTRL|SHIFT|ALT",
    action = wezterm.action.CloseCurrentPane { confirm = true },
  },
}
