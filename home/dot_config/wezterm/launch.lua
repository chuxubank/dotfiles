local wezterm = require("wezterm")
local mux = wezterm.mux
local launch_menu = {}
local default_prog
local set_environment_variables = {}

-- With default_gui_startup_args = {"connect", "unix"}, gui-startup does not
-- run for the attach path. Maximize the windows that are displayed after the
-- Unix-domain mux has been attached instead of spawning a duplicate local tab.
wezterm.on("gui-attached", function()
  local workspace = mux.get_active_workspace()
  for _, window in ipairs(mux.all_windows()) do
    if window:get_workspace() == workspace then
      window:gui_window():maximize()
    end
  end
end)

if wezterm.target_triple == "x86_64-pc-windows-msvc" then
  table.insert(launch_menu, {
    label = "CMD",
    args = { "cmd.exe" },
  })
  table.insert(launch_menu, {
    label = "UCRT64 / MSYS2",
    args = { "C:/msys64/msys2_shell.cmd", "-defterm", "-no-start", "-full-path", "-ucrt64", "-shell", "zsh" },
  })
  table.insert(launch_menu, {
    label = "MINGW64 / MSYS2",
    args = { "C:/msys64/msys2_shell.cmd", "-defterm", "-no-start", "-full-path", "-mingw64", "-shell", "zsh" },
  })

  default_prog = { "pwsh.exe", "-NoLogo" }

  set_environment_variables = {
    -- This changes the default prompt for cmd.exe to report the
    -- current directory using OSC 7, show the current time and
    -- the current directory colored in the prompt.
    prompt = "$E]7;file://localhost/$P$E\\$E[32m$T$E[0m $E[35m$P$E[36m$_$G$E[0m ",
    -- use a more ls-like output format for dir
    DIRCMD = "/d",
  }
end

return {
  launch_menu = launch_menu,
  default_prog = default_prog,
  set_environment_variables = set_environment_variables,
}
