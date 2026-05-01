#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir

$env:BENCHMARK_RESULTS_ROOT = Join-Path $repoRoot "results"

# Ensure results directories exist
New-Item -ItemType Directory -Force -Path "$repoRoot\results\windows\energy" | Out-Null
New-Item -ItemType Directory -Force -Path "$repoRoot\results\windows\BenchmarkDotNet.Artifacts" | Out-Null

# Set Ultimate Performance power plan
$guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
powercfg /duplicatescheme $guid 2>$null
powercfg /setactive $guid 2>$null; $LASTEXITCODE = 0
Write-Host "Power plan set to Ultimate Performance"

# Disable turbo boost via registry (Intel)
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\be337238-0d82-4146-a960-4f3749d470c7"
Set-ItemProperty -Path $regPath -Name "ValueMax" -Value 99 -ErrorAction SilentlyContinue
Write-Host "Turbo boost limited"

Write-Host "BENCHMARK_RESULTS_ROOT=$env:BENCHMARK_RESULTS_ROOT"
Write-Host "Launching benchmark..."

Set-Location "$repoRoot\src\windows\FannkuchBenchmark"
dotnet run -c Release -- @args
