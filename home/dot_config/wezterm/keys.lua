local wezterm = require("wezterm")
local act = wezterm.action

-- Super uses WezTerm's native tab bindings.
-- Ctrl+Shift+Arrow keeps WezTerm pane navigation; Super+Arrow passes to the mux.
-- Ctrl+Tab / Ctrl+Shift+Tab stay as terminal-native next/previous tab.
-- Ctrl+R is passed through for Pi reverse search; Super+R still reloads.
-- Ctrl+Shift+P/N are NOT passed through: Luvus panes support neither the kitty
-- keyboard protocol nor modifyOtherKeys, so Ctrl+Shift+letter collapses onto
-- Ctrl+letter and can never reach Pi/OMP. Model cycle is Alt+N / Alt+P instead,
-- so Ctrl+Shift+P keeps WezTerm's command palette and Ctrl+Shift+N its window.
-- Super+Shift+P is a second palette chord. Super+N still opens a window.

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
