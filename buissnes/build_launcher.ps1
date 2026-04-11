Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$arguments = @(
  '-m', 'PyInstaller',
  '--noconfirm',
  '--clean',
  '--windowed',
  '--onefile',
  '--name', 'NegroGamesLauncher',
  '--add-data', 'logo.png;.',
  'main.py'
)

& "c:/Users/PC/Desktop/buissnes/.venv-1/Scripts/python.exe" @arguments