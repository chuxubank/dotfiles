local wezterm = require("wezterm")

function get_appearance()
  if wezterm.gui then
    return wezterm.gui.get_appearance()
  end
  return "Dark"
end

local dark = { "Gruvbox Dark (Gogh)", "Everforest Dark (Gogh)" }

local light = { "Gruvbox (Gogh)", "EverforestLight (Gogh)" }

function scheme_for_appearance(appearance, index)
  if appearance:find("Dark") then
    return dark[index]
  else
    return light[index]
  end
end

wezterm.on("window-config-reloaded", function(window, pane)
  -- approximately identify this gui window, by using the associated mux id
  local id = tostring(window:window_id())

  -- maintain a mapping of windows that we have previously seen before in this event handler
  local seen = wezterm.GLOBAL.seen_windows or {}
  local index = wezterm.GLOBAL.scheme_index or 0
  -- set a flag if we haven't seen this window before
  local is_new_window = not seen[id]
  -- and update the mapping
  seen[id] = true
  wezterm.GLOBAL.seen_windows = seen

  -- now act upon the flag
  if is_new_window then
    index = index + 1
    if index > #dark then
      index = 1
    end
  end

  wezterm.log_info(string.format("Set theme index: %s", index))
  window:set_config_overrides({
    color_scheme = scheme_for_appearance(get_appearance(), index),
  })
  wezterm.GLOBAL.scheme_index = index
end)
