<#
  Azure OpenAI rate-limit header inspector
  Requirements:
    - Environment variable AZURE_OPENAI_KEY must contain your Azure OpenAI resource key (Keys and Endpoint -> Key1/Key2)
    - Update $resourceName and $deploymentName below if needed
    - Uses chat/completions to fetch x-ratelimit-* headers
    - IMPORTANT: Güvenlik için API anahtarınızı bu dosyaya YAPIŞTIRMAYIN. Anahtarı ya -ApiKey parametresiyle ya da AZURE_OPENAI_KEY ortam değişkeniyle verin.
#>

param(
  [string]$ResourceName = "hasans-5146-resource",
  [string]$DeploymentName = "gpt-5",
  [string]$ApiVersion = "2024-06-01",
  [string]$ApiKey,
  [ValidateSet('chat','responses')]
  [string]$Api = 'chat'
)

$endpoint = if ($Api -eq 'responses') {
  "https://$ResourceName.openai.azure.com/openai/deployments/$DeploymentName/responses?api-version=$ApiVersion"
} else {
  "https://$ResourceName.openai.azure.com/openai/deployments/$DeploymentName/chat/completions?api-version=$ApiVersion"
}
if (-not $ApiKey) {
  $ApiKey = [System.Environment]::GetEnvironmentVariable('AZURE_OPENAI_KEY')
}
if (-not $ApiKey) {
  $ApiKey = [System.Environment]::GetEnvironmentVariable('AZURE_OPENAI_KEY','User')
}
if (-not $ApiKey) {
  Write-Error "AZURE_OPENAI_KEY is not set and no -ApiKey was provided. Either pass -ApiKey <key> or set the environment variable (e.g., setx AZURE_OPENAI_KEY <key> then reopen terminal)."
  exit 1
}

$headers = @{ 'api-key' = $ApiKey; 'Content-Type' = 'application/json' }
$body = if ($Api -eq 'responses') {
  $content = @{ type = 'text'; text = 'ping' }
  $userMsg = @{ role = 'user'; content = @($content) }
  @{ input = @($userMsg); max_output_tokens = 1 } | ConvertTo-Json -Depth 6
} else {
  $userMsg = @{ role = 'user'; content = 'ping' }
  # 2024-06-01 chat/completions için gpt-5 ailesinde beklenen alan: max_completion_tokens
  @{ messages = @($userMsg); max_completion_tokens = 1 } | ConvertTo-Json -Depth 6
}

try {
  $resp = Invoke-WebRequest -Method Post -Uri $endpoint -Headers $headers -Body $body -ErrorAction Stop
  $rateHeaders = $resp.Headers.GetEnumerator() | Where-Object { $_.Name -like 'x-ratelimit*' } | ForEach-Object { "{0}: {1}" -f $_.Name, $_.Value }
  if ($rateHeaders) {
    Write-Output "Rate-limit headers:";
    $rateHeaders | ForEach-Object { Write-Output $_ }
  } else {
    Write-Output "No x-ratelimit headers found in response."
  }
}
catch {
  Write-Warning $_.Exception.Message
  if ($_.Exception.Response) {
    $hdr = $_.Exception.Response.Headers
    $rateHeaders = $hdr.GetEnumerator() | Where-Object { $_.Name -like 'x-ratelimit*' } | ForEach-Object { "{0}: {1}" -f $_.Name, $_.Value }
    if ($rateHeaders) {
      Write-Output "Rate-limit headers (from error response):";
      $rateHeaders | ForEach-Object { Write-Output $_ }
    }
    try {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $errBody = $reader.ReadToEnd()
      Write-Output "Error body:";
      Write-Output $errBody
      if ($errBody -match 'Unrecognized request schema|messages') {
        Write-Warning "Muhtemel neden: 2024-12-01-preview ile chat/completions kullanımı. Bu sürümde responses API ve 'input'/'max_output_tokens' beklenir. Komut örneği: powershell -NoProfile -File scripts/aoai_rate.ps1 -ApiVersion '2024-12-01-preview' -Api responses -ApiKey <key>"
      }
    } catch {}
  }
}
