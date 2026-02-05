# Paper-CLI Wrapper Script for PowerShell
# Usage: .\run-paper.ps1 [command] [args...]

$CLI_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$WORK_DIR = Get-Location

$env:PYTHONPATH = "$CLI_DIR;$env:PYTHONPATH"

if (Test-Path "$CLI_DIR\.env") {
    Get-Content "$CLI_DIR\.env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

Set-Location $WORK_DIR
python -m src.main $args
exit $LASTEXITCODE
