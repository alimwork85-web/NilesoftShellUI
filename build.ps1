# Builds dist\NilesoftShellUI.exe (one file, no console). Needs: pip install pyinstaller
Set-Location $PSScriptRoot
py -3.14 -m PyInstaller --noconfirm --clean --onefile --windowed --name NilesoftShellUI `
  --icon assets\app.ico --version-file version_info.txt `
  --add-data "index.html;." --add-data "presets.js;." --add-data "catppuccin.js;." `
  --add-data "assets\app-256.png;assets" app.pyw
