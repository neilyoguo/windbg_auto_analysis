param(
    [string]$Python = "",
    [string]$InstallDir = "$env:ProgramData\mcp_windbg_service"
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

$ServiceScriptSource = Join-Path $PSScriptRoot "mcp_windbg_service.py"
if (-not (Test-Path $ServiceScriptSource)) {
    throw "File not found: $ServiceScriptSource"
}

Write-Host "Checking Python: $Python"
& $Python -c "import win32serviceutil" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "pywin32 is missing. Run: $Python -m pip install pywin32"
}

& $Python -c "import mcp_windbg" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "mcp-windbg is missing. Run: $Python -m pip install mcp-windbg"
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $InstallDir "logs") | Out-Null

$ServiceScript = Join-Path $InstallDir "mcp_windbg_service.py"
Copy-Item -Force $ServiceScriptSource $ServiceScript

Write-Host "Installing service MCPWinDbg ..."
& $Python $ServiceScript --startup auto install
if ($LASTEXITCODE -ne 0) {
    throw "Service installation failed."
}

Write-Host "Starting service MCPWinDbg ..."
& $Python $ServiceScript start
if ($LASTEXITCODE -ne 0) {
    throw "Service start failed. Check log: $InstallDir\logs\stderr.log"
}

Write-Host "Done."
Write-Host "Service name: MCPWinDbg"
Write-Host "Command: python -m mcp_windbg --transport streamable-http --host 0.0.0.0 --port 1203"
Write-Host "MCP endpoint: http://127.0.0.1:1203/mcp"
Write-Host "Log dir: $InstallDir\logs"
Write-Host "Check status: Get-Service MCPWinDbg"
