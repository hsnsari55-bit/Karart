$ErrorActionPreference = 'Stop'

$workspace = 'c:\Karart'
$marker = Join-Path $workspace '.cline-reset-result.txt'
$logPath = Join-Path $workspace '.cline-reset-log.txt'
$codeExe = 'C:\Users\hasan\AppData\Local\Programs\Microsoft VS Code\Code.exe'

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $logPath -Value ("[$timestamp] $Message") -Encoding UTF8
}

try {
    if (Test-Path $marker) {
        Remove-Item $marker -Force
    }

    if (Test-Path $logPath) {
        Remove-Item $logPath -Force
    }

    Write-Log 'Reset script started.'
    Start-Sleep -Seconds 4

    Write-Log 'Stopping VS Code processes.'
    try {
        & taskkill /F /IM Code.exe *> $null
    }
    catch {
        Write-Log 'taskkill returned a non-fatal error.'
    }
    Write-Log 'VS Code stop command completed.'
    Start-Sleep -Seconds 3

    $base = Join-Path $env:APPDATA 'Code\User\globalStorage'
    $src = Join-Path $base 'saoudrizwan.claude-dev'

    if (Test-Path $src) {
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $backupName = "saoudrizwan.claude-dev.bak-$stamp"
        $dst = Join-Path $base $backupName
        Write-Log "Renaming '$src' to '$dst'."
        Rename-Item -Path $src -NewName $backupName
        Set-Content -Path $marker -Value "OK|$dst" -Encoding UTF8
    }
    else {
        Write-Log 'Source storage folder was not found.'
        Set-Content -Path $marker -Value 'NOT_FOUND' -Encoding UTF8
    }

    if (-not (Test-Path $codeExe)) {
        throw "Code.exe not found at: $codeExe"
    }

    Write-Log 'Reopening VS Code.'
    Start-Process -FilePath $codeExe -ArgumentList @('-r', $workspace)
    Write-Log 'Reset script finished successfully.'
}
catch {
    $message = $_.Exception.Message
    Write-Log "ERROR: $message"
    Set-Content -Path $marker -Value "ERROR|$message" -Encoding UTF8
    throw
}