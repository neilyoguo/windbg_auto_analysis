param(
    [string]$Python = "",
    [string]$InstallDir = "$env:ProgramData\mcp_windbg_service",
    [switch]$RemoveFiles
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $adminRole = [Security.Principal.WindowsBuiltInRole]::Administrator
    if (-not $principal.IsInRole($adminRole)) {
        throw "Please run PowerShell as Administrator."
    }
}

Assert-Admin

if (-not $Python) {
    $Python = (Get-Command python -ErrorAction Stop).Source
}

$ServiceScript = Join-Path $InstallDir "mcp_windbg_service.py"
if (-not (Test-Path $ServiceScript)) {
    $ServiceScript = Join-Path $PSScriptRoot "mcp_windbg_service.py"
}
if (-not (Test-Path $ServiceScript)) {
    throw "mcp_windbg_service.py not found. Cannot remove service through pywin32."
}

$svc = Get-Service -Name MCPWinDbg -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -ne "Stopped") {
    Write-Host "Stopping service MCPWinDbg ..."
    & $Python $ServiceScript stop
    Start-Sleep -Seconds 2
}

Write-Host "Removing service MCPWinDbg ..."
& $Python $ServiceScript remove

if ($RemoveFiles -and (Test-Path $InstallDir)) {
    Write-Host "Removing install dir: $InstallDir ..."
    Remove-Item -Recurse -Force $InstallDir
}

Write-Host "Done."
