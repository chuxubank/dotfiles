if ($env:TERM_PROGRAM -eq "WezTerm") {
    $prompt = ""
    function Invoke-Starship-PreCommand {
        $current_location = $executionContext.SessionState.Path.CurrentLocation
        if ($current_location.Provider.Name -eq "FileSystem") {
            $ansi_escape = [char]27
            $provider_path = $current_location.ProviderPath -replace "\\", "/"
            $prompt = "$ansi_escape]7;file://${env:COMPUTERNAME}/${provider_path}$ansi_escape\"
        }
        $host.ui.Write($prompt)
    }
    Invoke-Expression (&starship init powershell)
}

$PSReadLineOptions = @{
    EditMode                      = "Emacs"
    HistoryNoDuplicates           = $true
    HistorySearchCursorMovesToEnd = $true
    Colors                        = @{
        "Command" = "#8181f7"
    }
}
Set-PSReadLineOption @PSReadLineOptions
Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete

{{- if eq .chezmoi.os "windows" }}
#34de4b3d-13a8-4540-b76d-b9e8d3851756 PowerToys CommandNotFound module

Import-Module "C:\Program Files\PowerToys\WinUI3Apps\..\WinGetCommandNotFound.psd1"
#34de4b3d-13a8-4540-b76d-b9e8d3851756
{{- end }}
