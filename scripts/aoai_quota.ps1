<#
  Azure OpenAI subscription quota tier fetcher (no API key needed)
  Uses Azure CLI to obtain an AAD token and calls Azure Management API:
    GET https://management.azure.com/subscriptions/{sub}/providers/Microsoft.CognitiveServices/quotaTiers?api-version=2025-10-01-preview
  Outputs raw JSON and a short summary if possible.
#>

param()

function Get-AccessToken {
  $tok = az account get-access-token --resource https://management.azure.com --query accessToken -o tsv 2>$null
  if (-not $tok) { throw 'Azure CLI oturumu bulunamadı. Önce: az login' }
  return $tok
}

try {
  $subId = az account show --query id -o tsv 2>$null
  if (-not $subId) { throw 'Abonelik bulunamadı. az account show başarısız. az login yapın ve doğru subscription seçin (az account set --subscription <id>).'}
  $token = Get-AccessToken
  $uri = "https://management.azure.com/subscriptions/$subId/providers/Microsoft.CognitiveServices/quotaTiers?api-version=2025-10-01-preview"
  $headers = @{ Authorization = "Bearer $token" }
  $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers -ErrorAction Stop
  Write-Output "Raw quotaTiers JSON:";
  $resp | ConvertTo-Json -Depth 8

  if ($resp.value) {
    Write-Output "\nSummary:";
    foreach ($item in $resp.value) {
      $name = $item.name
      $tier = $item.properties.tier
      $regions = ($item.properties.regions -join ', ')
      if ($name -or $tier -or $regions) {
        Write-Output ("- Name: {0}; Tier: {1}; Regions: {2}" -f $name,$tier,$regions)
      }
    }
  }
}
catch {
  Write-Error $_.Exception.Message
  if ($_.Exception.Response) {
    try {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $errBody = $reader.ReadToEnd()
      Write-Output "Error body:";
      Write-Output $errBody
    } catch {}
  }
  exit 1
}
