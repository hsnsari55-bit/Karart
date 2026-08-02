<#
  Azure OpenAI call helper with exponential backoff on 429/503
  - Destekler: chat/completions (2024-06-01), responses (2024-12-01-preview ve sonrası)
  - Anahtar: -ApiKey ya da AZURE_OPENAI_KEY ortam değişkeni
  - Amaç: 429 aldığınızda x-ratelimit-* başlıklarını yazdırıp uygun süre kadar bekleyerek tekrar denemek
#>

param(
  [string]$ResourceName = "hasans-5146-resource",
  [string]$DeploymentName = "gpt-5",
  [string]$ApiVersion = "2024-06-01",
  [ValidateSet('chat','responses')]
  [string]$Api = 'chat',
  [string]$ApiKey,
  [int]$MaxRetries = 6,
  [int]$InitialDelaySec = 2,
  [double]$JitterPct = 0.20,
  [int]$MaxDelaySec = 60,
  [switch]$UseAAD,
  [ValidateSet('openai.azure.com','cognitiveservices.azure.com')]
  [string]$BaseHost = 'openai.azure.com',
  # İSTEĞE BAĞLI: İstemci tarafı "API sayaçları". x-ratelimit başlıklarına göre
  # bir sonraki güvenli zamanı yerel bir durum dosyasına yazıp yeni isteği
  # o zamana kadar bekletir. Aynı makinede/oturumda ardışık isteklerde 429 riskini azaltır.
  [switch]$EnableClientCounters,
  [string]$StateFile = "$env:TEMP/aoai_rate_state.json",
  # Limitlerin altına düştüğünüzde proaktif bekleme eşikleri (0-1 arası oran)
  [double]$MinRemainingRequestsPct = 0.05,
  [double]$MinRemainingTokensPct = 0.05
)

# Yardımcı: PSCustomObject -> Hashtable dönüştür
function Convert-ToHashtable {
  param([Parameter(Mandatory=$true)]$obj)
  if ($null -eq $obj) { return @{} }
  if ($obj -is [hashtable]) { return $obj }
  if ($obj -is [System.Collections.IDictionary]) { return @{} + $obj }
  if ($obj -is [System.Management.Automation.PSCustomObject]) {
    $h = @{}
    foreach ($p in $obj.PSObject.Properties) {
      $h[$p.Name] = Convert-ToHashtable -obj $p.Value
    }
    return $h
  }
  try {
    # JSON string ise dene
    if ($obj -is [string] -and $obj.Trim().StartsWith('{')) {
      $tmp = $obj | ConvertFrom-Json
      return Convert-ToHashtable -obj $tmp
    }
  } catch {}
  return @{}
}

if (-not $UseAAD) {
  if (-not $ApiKey) { $ApiKey = [System.Environment]::GetEnvironmentVariable('AZURE_OPENAI_KEY') }
  if (-not $ApiKey) { Write-Error "AZURE_OPENAI_KEY not set and no -ApiKey provided. Ya -UseAAD ile AAD kullanın ya da -ApiKey verin."; exit 1 }
}

$endpoint = if ($Api -eq 'responses') {
  "https://$ResourceName.$BaseHost/openai/deployments/$DeploymentName/responses?api-version=$ApiVersion"
} else {
  "https://$ResourceName.$BaseHost/openai/deployments/$DeploymentName/chat/completions?api-version=$ApiVersion"
}

function Get-AadToken {
  $tok = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv 2>$null
  if (-not $tok) { throw 'AAD token alınamadı. az login yapın ve tekrar deneyin.' }
  return $tok
}

if ($UseAAD) {
  $token = Get-AadToken
  $headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
} else {
  $headers = @{ 'api-key' = $ApiKey; 'Content-Type' = 'application/json' }
}

if ($Api -eq 'responses') {
  $content = @{ type = 'text'; text = 'ping' }
  $userMsg = @{ role = 'user'; content = @($content) }
  $body = @{ input = @($userMsg); max_output_tokens = 16 } | ConvertTo-Json -Depth 6
} else {
  $userMsg = @{ role = 'user'; content = 'ping' }
  # gpt-5 ailesi + 2024-06-01 chat/completions için: max_completion_tokens
  $body = @{ messages = @($userMsg); max_completion_tokens = 16 } | ConvertTo-Json -Depth 6
}

function Show-RateHeaders($hdrs) {
  if (-not $hdrs) { return }
  $hdrs.GetEnumerator() |
    Where-Object { $_.Name -like 'x-ratelimit*' -or $_.Name -eq 'retry-after' -or $_.Name -eq 'apim-request-id' -or $_.Name -eq 'x-azure-ref' } |
    ForEach-Object { Write-Output ("{0}: {1}" -f $_.Name, $_.Value) }
}

function Parse-DurationSec([string]$val) {
  if (-not $val) { return $null }
  # Örn: "10s", "1.5s", "250ms", "2m", "1h" veya "10s;w=rolling"
  $raw = $val.Split(';')[0].Trim()
  if ($raw -match '^([0-9]*\.?[0-9]+)\s*(ms|s|m|h)?$') {
    $num = [double]$Matches[1]
    $unit = $Matches[2]
    switch ($unit) {
      'ms' { return [math]::Ceiling($num / 1000.0) }
      'm'  { return [math]::Ceiling($num * 60.0) }
      'h'  { return [math]::Ceiling($num * 3600.0) }
      default { return [math]::Ceiling($num) } # saniye varsayımı
    }
  }
  # HTTP Retry-After tarih formatı olabilir
  try {
    $dt = [DateTime]::Parse($raw)
    $sec = [int][math]::Ceiling(($dt - [DateTime]::UtcNow).TotalSeconds)
    if ($sec -gt 0) { return $sec }
  } catch {}
  return $null
}

function Parse-ResetSeconds($hdrs) {
  if (-not $hdrs) { return $null }
  $retryAfter = $hdrs['retry-after']
  $ra = Parse-DurationSec $retryAfter
  $resetReq = Parse-DurationSec $hdrs['x-ratelimit-reset-requests']
  $resetTok = Parse-DurationSec $hdrs['x-ratelimit-reset-tokens']
  $candidates = @($ra, $resetReq, $resetTok) | Where-Object { $_ -ne $null -and $_ -gt 0 }
  if ($candidates.Count -gt 0) { return ($candidates | Measure-Object -Maximum).Maximum }
  return $null
}

# --- İstemci tarafı sayaç/durum yönetimi (opsiyonel) ---
function Get-RateStateKey {
  return ("{0}|{1}|{2}|{3}|{4}" -f $ResourceName,$DeploymentName,$Api,$ApiVersion,$BaseHost)
}

function Load-RateState {
  param([string]$path)
  if (-not (Test-Path -LiteralPath $path)) { return @{} }
  try {
    $raw = Get-Content -LiteralPath $path -Raw
    $obj = $raw | ConvertFrom-Json
    return (Convert-ToHashtable -obj $obj)
  } catch { return @{} }
}

function Save-RateState {
  param([hashtable]$state,[string]$path)
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  ($state | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $path -Encoding UTF8
}

function Preflight-RespectState {
  if (-not $EnableClientCounters) { return }
  $key = Get-RateStateKey
  $st = Load-RateState -path $StateFile
  $node = $st[$key]
  if ($node -and $node.nextAllowedAt) {
    try {
      $next = [DateTime]::Parse($node.nextAllowedAt)
      $now = [DateTime]::UtcNow
      if ($next -gt $now) {
        $sleep = [int][math]::Ceiling(($next - $now).TotalSeconds)
        if ($sleep -gt 0) { Write-Output ("Önceden kaydedilmiş rate-limit nedeniyle bekleniyor: {0}s" -f $sleep); Start-Sleep -Seconds $sleep }
      }
    } catch {}
  }
}

function Update-RateStateFromHeaders {
  param([object]$hdrs)
  if (-not $EnableClientCounters) { return }
  if (-not $hdrs) { return }
  $key = Get-RateStateKey
  $st = Load-RateState -path $StateFile
  if (-not $st) { $st = @{} }

  $remReq = $hdrs['x-ratelimit-remaining-requests']
  $remTok = $hdrs['x-ratelimit-remaining-tokens']
  $limReq = $hdrs['x-ratelimit-limit-requests']
  $limTok = $hdrs['x-ratelimit-limit-tokens']
  $reset = Parse-ResetSeconds $hdrs
  $node = @{}
  if ($st -is [hashtable] -and $st.ContainsKey($key)) {
    $node = Convert-ToHashtable -obj $st[$key]
  }

  $needDelay = $false
  try { if ($remReq -and ([int]$remReq) -le 0) { $needDelay = $true } } catch {}
  try { if ($remTok -and ([int]$remTok) -le 0) { $needDelay = $true } } catch {}
  if ($reset -and $reset -gt 0 -and $needDelay) {
    $node.nextAllowedAt = ([DateTime]::UtcNow.AddSeconds([int]$reset)).ToString('o')
  } elseif (-not $node.ContainsKey('nextAllowedAt')) {
    # ilk kayıt, önlemli olalım; fakat zorunlu değil
    $node.nextAllowedAt = $null
  }
  $node.lastSeen = ([DateTime]::UtcNow).ToString('o')
  $node.remainingRequests = $remReq
  $node.remainingTokens = $remTok
  $node.limitRequests = $limReq
  $node.limitTokens = $limTok
  $node.lastResetHintSec = $reset
  $st[$key] = $node
  Save-RateState -state $st -path $StateFile
}

$delay = [math]::Max(1, $InitialDelaySec)
for ($i = 0; $i -le $MaxRetries; $i++) {
  try {
    Preflight-RespectState
    try {
      $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $endpoint -Headers $headers -Body $body -ErrorAction Stop
    } catch {
      # openai.azure.com 404 verirse, AIServices türü için cognitiveservices.azure.com ile yeniden dene
      $innerStatus = $null
      if ($_.Exception -and $_.Exception.Response) { $innerStatus = $_.Exception.Response.StatusCode.Value__ }
      if ($UseAAD -and $BaseHost -eq 'openai.azure.com' -and $innerStatus -eq 404) {
        $alt = $endpoint -replace 'openai.azure.com','cognitiveservices.azure.com'
        $resp = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $alt -Headers $headers -Body $body -ErrorAction Stop
        Write-Warning "openai.azure.com 404 verdi; cognitiveservices.azure.com ile başarılı deneme yapıldı."
      } else { throw }
    }
    Write-Output "Success"
    Show-RateHeaders $resp.Headers
    Update-RateStateFromHeaders -hdrs $resp.Headers
    break
  } catch {
    $status = $null; $hdrs = $null
    if ($_.Exception -and $_.Exception.Response) {
      $status = $_.Exception.Response.StatusCode.Value__
      $hdrs = $_.Exception.Response.Headers
    }
    if ($status) { Write-Warning ("HTTP {0}" -f $status) } else { Write-Warning "İstek başarısız oldu (durum kodu alınamadı)." }
    Show-RateHeaders $hdrs
    Update-RateStateFromHeaders -hdrs $hdrs
    try {
      if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errBody = $reader.ReadToEnd(); if ($errBody) { Write-Output "Error body:"; Write-Output $errBody }
      }
    } catch {}

    $transient = @(408, 425, 429, 500, 502, 503, 504)
    if ($status -in $transient) {
      $reset = Parse-ResetSeconds $hdrs
      if ($reset -and $reset -gt 0) { $sleep = [math]::Max($delay, $reset) } else { $sleep = $delay }
      $sleep = [math]::Min($sleep, $MaxDelaySec)
      # jitter uygula
      $minJ = 1.0 - [math]::Abs($JitterPct); if ($minJ -lt 0.0) { $minJ = 0.0 }
      $maxJ = 1.0 + [math]::Abs($JitterPct)
      $factor = Get-Random -Minimum $minJ -Maximum $maxJ
      $sleep = [int][math]::Max(1, [math]::Ceiling($sleep * $factor))
      Write-Output ("Bekleme: {0}s (attempt {1}/{2})" -f $sleep, ($i+1), $MaxRetries)
      Start-Sleep -Seconds $sleep
      $delay = [math]::Min([int]([math]::Ceiling($delay * 2)), $MaxDelaySec)
      if ($i -eq $MaxRetries) { Write-Error "Retry limit reached."; exit 1 }
    } else {
      throw
    }
  }
}

# Proaktif bekleme: Son başarılı/başarısız yanıttan kalan/limit oranları çok düşmüşse
# ve reset süresi biliniyorsa, yeni çağrıdan önce uyumlu bekleme yapın.
if ($EnableClientCounters) {
  try {
    $st = Load-RateState -path $StateFile
    $key = Get-RateStateKey
    if ($st -and $st.ContainsKey($key)) {
      $node = $st[$key]
      $now = [DateTime]::UtcNow
      $resetSec = $null
      if ($node.lastResetHintSec) { $resetSec = [int]$node.lastResetHintSec }
      $limReq = 0; $limTok = 0; $remReq = 0; $remTok = 0
      try { if ($node.limitRequests) { $limReq = [int]$node.limitRequests } } catch {}
      try { if ($node.limitTokens) { $limTok = [int]$node.limitTokens } } catch {}
      try { if ($node.remainingRequests) { $remReq = [int]$node.remainingRequests } } catch {}
      try { if ($node.remainingTokens) { $remTok = [int]$node.remainingTokens } } catch {}
      $needSleep = $false
      if ($limReq -gt 0) {
        $pct = if ($limReq -gt 0) { $remReq / [double]$limReq } else { 1.0 }
        if ($pct -le $MinRemainingRequestsPct) { $needSleep = $true }
      }
      if ($limTok -gt 0) {
        $pctT = if ($limTok -gt 0) { $remTok / [double]$limTok } else { 1.0 }
        if ($pctT -le $MinRemainingTokensPct) { $needSleep = $true }
      }
      if ($needSleep -and $resetSec -and $resetSec -gt 0 -and $node.lastSeen) {
        try {
          $last = [DateTime]::Parse($node.lastSeen)
          $until = $last.AddSeconds($resetSec)
          if ($until -gt $now) {
            $sleep = [int][math]::Ceiling(($until - $now).TotalSeconds)
            if ($sleep -gt 0) { Write-Output ("Proaktif bekleme: {0}s (kalan/limit eşikleri)" -f $sleep); Start-Sleep -Seconds $sleep }
          }
        } catch {}
      }
    }
  } catch {}
}
