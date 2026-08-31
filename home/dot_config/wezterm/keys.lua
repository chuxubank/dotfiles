local wezterm = require("wezterm")
local act = wezterm.action

-- Super uses WezTerm's native tab bindings.
-- Ctrl+Shift+Arrow keeps WezTerm pane navigation; Super+Arrow passes to the mux.
-- Ctrl+Tab / Ctrl+Shift+Tab stay as terminal-native next/previous tab.
-- Ctrl+R is passed through for Pi reverse search; Super+R still reloads.
-- Ctrl+Shift+P/N go to Pi/OMP model cycle. Palette moves to Super+Shift+P.
-- Super+N still opens a WezTerm window.

local keys = {}

local function passthrough(key, mods)
  table.insert(keys, {
    key = key,
    mods = mods,
    action = act.DisableDefaultAssignment,
  })
end

passthrough("t", "CTRL|SHIFT")
passthrough("T", "CMD|SHIFT")
passthrough("w", "CTRL|SHIFT")
passthrough("r", "CTRL")
passthrough("p", "CTRL|SHIFT")
passthrough("P", "CTRL|SHIFT")
passthrough("n", "CTRL|SHIFT")
passthrough("N", "CTRL|SHIFT")
passthrough("[", "CMD|SHIFT")
passthrough("]", "CMD|SHIFT")
passthrough("PageUp", "CTRL")
passthrough("PageDown", "CTRL")
passthrough("PageUp", "CTRL|SHIFT")
passthrough("PageDown", "CTRL|SHIFT")
passthrough("Z", "CTRL|SHIFT")
passthrough('"', "CTRL|SHIFT|ALT")
passthrough("%", "CTRL|SHIFT|ALT")

for _, key in ipairs({ "LeftArrow", "DownArrow", "UpArrow", "RightArrow" }) do
  passthrough(key, "CMD")
end

table.insert(keys, {
  key = "B",
  mods = "CTRL|SHIFT",
  action = act.EmitEvent("toggle-opacity"),
})
table.insert(keys, {
  key = "l",
  mods = "CTRL|SHIFT|ALT",
  action = act.ShowLauncher,
})
table.insert(keys, {
  key = "P",
  mods = "CMD|SHIFT",
  action = act.ActivateCommandPalette,
})

return keys
