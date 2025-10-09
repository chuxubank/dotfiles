local wezterm = require("wezterm")

-- Helper function to get the system's appearance (Dark or Light).
-- It defaults to "Dark" if the GUI is not available.
function get_appearance()
  if wezterm.gui then
    return wezterm.gui.get_appearance()
  end
  return "Dark"
end

-- Define lists of color schemes for dark and light modes.
-- Make sure both lists have the same number of schemes.
local dark_schemes = { "Gruvbox Dark (Gogh)", "Everforest Dark (Gogh)" }
local light_schemes = { "Gruvbox (Gogh)", "EverforestLight (Gogh)" }

-- Function to select a scheme from the correct list based on appearance and index.
function scheme_for_appearance(appearance, index)
  if appearance:find("Dark") then
    return dark_schemes[index]
  else
    return light_schemes[index]
  end
end

wezterm.on("window-config-reloaded", function(window, pane)
  local overrides = window:get_config_overrides() or {}
  local window_id = tostring(window:window_id())

  wezterm.GLOBAL.window_theme_map = wezterm.GLOBAL.window_theme_map or {}
  wezterm.GLOBAL.next_theme_index = wezterm.GLOBAL.next_theme_index or 1

  local theme_index = wezterm.GLOBAL.window_theme_map[window_id]

  if not theme_index then
    theme_index = wezterm.GLOBAL.next_theme_index
    wezterm.GLOBAL.window_theme_map[window_id] = theme_index

    wezterm.log_info("New window (ID: " .. window_id .. "), assigning theme index: " .. theme_index)

    local num_schemes = math.min(#dark_schemes, #light_schemes)
    wezterm.GLOBAL.next_theme_index = (wezterm.GLOBAL.next_theme_index % num_schemes) + 1
  end

  local appearance = get_appearance()
  local scheme_name = scheme_for_appearance(appearance, theme_index)

  wezterm.log_info("Applying theme '" .. scheme_name .. "' to window " .. window_id)
  overrides.color_scheme = scheme_name
  window:set_config_overrides(overrides)
end)

wezterm.on("toggle-opacity", function(window, pane)
  local overrides = window:get_config_overrides() or {}
  if not overrides.window_background_opacity then
    overrides.window_background_opacity = 0.5
  else
    overrides.window_background_opacity = nil
  end
  window:set_config_overrides(overrides)
end)
