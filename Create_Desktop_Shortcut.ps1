# LUDO Desktop Launcher PowerShell Script
# Creates a proper Windows shortcut with icon

$WScriptShell = New-Object -ComObject WScript.Shell
$Desktop = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = "$Desktop\LUDO.lnk"

# Create shortcut
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "E:\brainstroming\AI_Miles\Start_LUDO.bat"
$Shortcut.WorkingDirectory = "E:\brainstroming\AI_Miles"
$Shortcut.Description = "L.U.D.O AI Assistant"
$Shortcut.WindowStyle = 1  # Normal window

# Optional: Set icon (if you have one)
# $Shortcut.IconLocation = "E:\brainstroming\AI_Miles\HUD\ludo_icon.ico"

$Shortcut.Save()

Write-Host "✅ Desktop shortcut created: $ShortcutPath"
Write-Host "You can now double-click 'LUDO' on your desktop to start!"
