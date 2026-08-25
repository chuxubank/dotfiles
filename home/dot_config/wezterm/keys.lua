local wezterm = require("wezterm")
local act = wezterm.action

-- Cmd uses WezTerm's native tab bindings. Ctrl+1..9 passes to the mux.
-- Pane shortcuts also pass through to the mux.
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
  passthrough(key, "CTRL|SHIFT")
  passthrough(key, "CTRL|SHIFT|ALT")
end

table.insert(keys, {
  key = "B",
  mods = "CTRL|SHIFT",
  action = wezterm.action.EmitEvent("toggle-opacity"),
})
table.insert(keys, {
  key = "l",
  mods = "CTRL|SHIFT|ALT",
  action = act.ShowLauncher,
})

return keys
