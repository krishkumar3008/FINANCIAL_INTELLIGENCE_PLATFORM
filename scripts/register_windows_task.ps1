# PowerShell Script to register the Nifty 100 Daily Market-Close Pipeline in Windows Task Scheduler
# Task Name: Nifty100_Daily_AutoUpdate
# Trigger: Monday through Friday at 16:00 (4:00 PM IST)

$ErrorActionPreference = "Continue"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python.exe"
}

$TaskName = "Nifty100_Daily_AutoUpdate"
$ActionCommand = "`"$PythonExe`" -m src.automation.daily_pipeline --now"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Nifty 100 Automated Daily Pipeline - Windows Task Setup " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Project Root : $ProjectRoot"
Write-Host "Python Path  : $PythonExe"
Write-Host "Task Name    : $TaskName"
Write-Host "Schedule     : Every Weekday (Mon-Fri) at 16:00 IST"
Write-Host "Command      : $ActionCommand"
Write-Host "----------------------------------------------------------"

try {
    # Check if task already exists silently
    $null = & schtasks.exe /Query /TN $TaskName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[INFO] Existing task '$TaskName' found. Updating definition..." -ForegroundColor Yellow
    }

    # Register task via schtasks.exe
    $createArgs = @(
        "/Create",
        "/TN", $TaskName,
        "/TR", "cmd.exe /c cd /d `"$ProjectRoot`" && $ActionCommand",
        "/SC", "WEEKLY",
        "/D", "MON,TUE,WED,THU,FRI",
        "/ST", "16:00",
        "/F"
    )

    schtasks.exe $createArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[SUCCESS] Task '$TaskName' successfully registered in Windows Task Scheduler!" -ForegroundColor Green
        Write-Host "The pipeline will automatically execute daily at 16:00 IST Monday-Friday." -ForegroundColor Green
        Write-Host "`nTo test-run the task immediately, execute:" -ForegroundColor White
        Write-Host "  schtasks.exe /Run /TN `"$TaskName`"" -ForegroundColor Cyan
        Write-Host "To remove the task in the future, execute:" -ForegroundColor White
        Write-Host "  schtasks.exe /Delete /TN `"$TaskName`" /F" -ForegroundColor Gray
    } else {
        Write-Host "`n[ERROR] Failed to register task with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
}
catch {
    Write-Host "`n[ERROR] An error occurred: $_" -ForegroundColor Red
}
Write-Host "==========================================================`n"
