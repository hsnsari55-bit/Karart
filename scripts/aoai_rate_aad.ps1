<#
  Azure OpenAI rate-limit header inspector using AAD (no API key needed)
  Prereq: az login; caller must have access (e.g., Cognitive Services User) on the AOAI resource.
#>

param(
  [string]$ResourceName = "hasans-5146-resource",
  [string]$DeploymentName = "gpt-5",
  [string]$ApiVersion = "2024-06-01",
  [ValidateSet('chat','responses')]
  [string]$Api = 'chat',
  # openai.azure.com (OpenAI kind) veya cognitiveservices.azure.com (AIServices kind)
  [ValidateSet('openai.azure.com','cognitiveservices.azure.com')]
  [string]$BaseHost = 'openai.azure.com'
)

# API sürümü/uç noktası uyumsuzluğu kaynaklı 400 hatalarını önlemek için
# iki farklı payload/endpoint desteklenir:
# - chat/completions (2024-06-01 ve öncesi)
# - responses (2024-12-01-preview ve sonrası)
if ($Api -eq 'responses') {
  $uri = "https://$ResourceName.$BaseHost/openai/deployments/$DeploymentName/responses?api-version=$ApiVersion"
  $body = '{"input":[{"role":"user","content":[{"type":"text","text":"ping"}]}],"max_output_tokens":1}'
} else {
  $uri = "https://$ResourceName.$BaseHost/openai/deployments/$DeploymentName/chat/completions?api-version=$ApiVersion"
  # gpt-5 ailesi + 2024-06-01 chat/completions için: max_completion_tokens
  $body = '{"messages":[{"role":"user","content":"ping"}],"max_completion_tokens":1}'
}

function Get-AadToken {
  $tok = az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv 2>$null
  if (-not $tok) { throw 'AAD token alınamadı. az login yapın ve tekrar deneyin.' }
  return $tok
}

try {
  $token = Get-AadToken
  $headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
  try {
    $resp = Invoke-WebRequest -Method Post -Uri $uri -Headers $headers -Body $body -ErrorAction Stop
  } catch {
    # AIServices kaynakları için openai.azure.com 404 dönebilir; cognitiveservices.azure.com ile tekrar dene
    if ($BaseHost -eq 'openai.azure.com') {
      try {
        $alt = $uri -replace "openai.azure.com","cognitiveservices.azure.com"
        $resp = Invoke-WebRequest -Method Post -Uri $alt -Headers $headers -Body $body -ErrorAction Stop
        Write-Warning "openai.azure.com 404 verdi; cognitiveservices.azure.com ile başarılı deneme yapıldı."
      } catch { throw }
    } else { throw }
  }
  $rate = $resp.Headers.GetEnumerator() | Where-Object { $_.Name -like 'x-ratelimit*' } | ForEach-Object { "{0}: {1}" -f $_.Name, $_.Value }
  if ($rate) {
    Write-Output "Rate-limit headers:"; $rate | ForEach-Object { Write-Output $_ }
  } else {
    Write-Output "x-ratelimit başlığı bulunamadı."
  }
}
catch {
  Write-Warning $_.Exception.Message
  if ($_.Exception.Response) {
    $hdr = $_.Exception.Response.Headers
    $rate = $hdr.GetEnumerator() | Where-Object { $_.Name -like 'x-ratelimit*' } | ForEach-Object { "{0}: {1}" -f $_.Name, $_.Value }
    if ($rate) { Write-Output "Rate-limit headers (from error):"; $rate | ForEach-Object { Write-Output $_ } }
    try {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $errBody = $reader.ReadToEnd(); Write-Output "Error body:"; Write-Output $errBody
      if ($errBody -match 'Unrecognized request schema|messages') {
        Write-Warning "Muhtemel neden: 2024-12-01-preview ile chat/completions kullanımı. Bu sürümde responses API ve 'input'/'max_output_tokens' beklenir. Komut örneği: powershell -NoProfile -File scripts/aoai_rate_aad.ps1 -ApiVersion '2024-12-01-preview' -Api responses"
      }
    } catch {}
  }
  exit 1
}
