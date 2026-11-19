param(
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [Parameter(Mandatory=$true)][string]$NewRoot
)
$ErrorActionPreference = 'Stop'
$taskNewRoot = [System.IO.Path]::GetFullPath($NewRoot)
if (Test-Path -LiteralPath $taskNewRoot) { throw 'NewRoot already exists; nothing will be overwritten.' }
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Python executable not found.' }
$taskSource = Join-Path $PSScriptRoot 'EXECUTED_b_model_backtest.py'
$taskInput = Join-Path $PSScriptRoot 'EXECUTED_INPUT_lotto_data.csv'
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne '3ecf4fb805c2448e49c39e01174b3a112d4865c7ff1a31157437515b78be47cb') { throw 'Source hash mismatch.' }
if ((Get-FileHash -LiteralPath $taskInput -Algorithm SHA256).Hash.ToLowerInvariant() -ne '243cd17e6b97a2d96709ddfc689a068038669341a52dcc0743c141d309e43b9f') { throw 'Data hash mismatch.' }
$taskSandbox = Join-Path $taskNewRoot 'sandbox'
$taskScripts = Join-Path $taskSandbox 'scripts'
$taskData = Join-Path $taskSandbox 'work\lotto-data'
$taskOut = Join-Path $taskSandbox 'outputs'
New-Item -ItemType Directory -Path $taskScripts,$taskData,$taskOut | Out-Null
$taskCopiedSource = Join-Path $taskScripts 'b_model_backtest.py'
$taskCopiedInput = Join-Path $taskData 'lotto_data.csv'
Copy-Item -LiteralPath $taskSource -Destination $taskCopiedSource
Copy-Item -LiteralPath $taskInput -Destination $taskCopiedInput
if ((Get-FileHash -LiteralPath $taskCopiedSource).Hash -ne (Get-FileHash -LiteralPath $taskSource).Hash) { throw 'Copied source mismatch.' }
if ((Get-FileHash -LiteralPath $taskCopiedInput).Hash -ne (Get-FileHash -LiteralPath $taskInput).Hash) { throw 'Copied input mismatch.' }
$taskStartUtc = [DateTime]::UtcNow.ToString('o')
& $PythonExe $taskCopiedSource 1> (Join-Path $taskNewRoot 'stdout.log') 2> (Join-Path $taskNewRoot 'stderr.log')
$taskExitCode = $LASTEXITCODE
@{start_utc=$taskStartUtc; end_utc=[DateTime]::UtcNow.ToString('o'); exit_code=$taskExitCode; source_sha256=(Get-FileHash -LiteralPath $taskCopiedSource).Hash; raw_data_sha256=(Get-FileHash -LiteralPath $taskCopiedInput).Hash; actual_1245='NOT READ / NOT USED'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskNewRoot 'execution_result.json') -Encoding UTF8
if ($taskExitCode -ne 0) { throw "Backtest failed, exit=$taskExitCode; see separate logs." }
Get-ChildItem -LiteralPath $taskOut -File | Get-FileHash -Algorithm SHA256
Write-Output 'Unmodified B-v1 rerun finished; existing audit outputs were preserved.'
