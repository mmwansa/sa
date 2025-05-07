# Windows PowerShell: Load environment variables from a file and executes a command.
param (
    [string]$envFile,
    [string]$command,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$args
)

if (-not $envFile -or -not $command) {
    Write-Host "Usage: .\run_with_env.ps1 <path-to-env-file> <command> [args...]"
    exit 1
}

if (-not (Test-Path $envFile)) {
    Write-Host "Error: File '$envFile' not found."
    exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*#") { return }  # Skip comments
    if ($_ -match "^\s*$") { return }  # Skip empty lines

    $key, $value = $_ -split "=", 2
    if ($value -match '^\s*"\s*(.*)\s*"\s*$') {
        $value = $matches[1]  # Remove surrounding quotes
    }
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
}

& $command @args
