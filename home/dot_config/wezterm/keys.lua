local wezterm = require("wezterm")
local act = wezterm.action

-- Terminal layer: disable tab/pane defaults so the mux can own them.
-- Keep Cmd+C/V, Cmd+N, Cmd+W, font size, and the custom chords below.
local keys = {}

local function passthrough(key, mods)
  table.insert(keys, {
    key = key,
    mods = mods,
    action = act.DisableDefaultAssignment,
  })
end

passthrough("t", "CMD")
passthrough("t", "CTRL|SHIFT")
passthrough("T", "CMD|SHIFT")
passthrough("Tab", "CTRL")
passthrough("Tab", "CTRL|SHIFT")
passthrough("[", "CMD|SHIFT")
passthrough("]", "CMD|SHIFT")
passthrough("PageUp", "CTRL")
passthrough("PageDown", "CTRL")
passthrough("PageUp", "CTRL|SHIFT")
passthrough("PageDown", "CTRL|SHIFT")
passthrough("Z", "CTRL|SHIFT")
passthrough('"', "CTRL|SHIFT|ALT")
passthrough("%", "CTRL|SHIFT|ALT")

for i = 1, 9 do
  passthrough(tostring(i), "CMD")
  passthrough(tostring(i), "CTRL|SHIFT")
end

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
